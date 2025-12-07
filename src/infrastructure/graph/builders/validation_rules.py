"""统一验证规则

提供可复用的验证规则，减少各构建器中的重复验证逻辑。
"""

from typing import Dict, List, Optional, Union, Callable
import re

from src.interfaces.workflow.element_builder import IValidationRule, BuildContext
from src.interfaces.workflow.config import INodeConfig, IEdgeConfig


class BasicConfigValidationRule(IValidationRule):
    """基础配置验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证基础配置"""
        errors = []
        
        if not config:
            errors.append("配置不能为空")
            return errors
        
        # 验证配置对象的基本属性
        if isinstance(config, INodeConfig) and not config.name:
            errors.append("名称不能为空")
        
        if isinstance(config, IEdgeConfig) and not config.from_node:
            errors.append("起始节点不能为空")
        
        return errors
    
    def get_rule_name(self) -> str:
        return "basic_config_validation"
    
    def get_priority(self) -> int:
        return 1  # 最高优先级


class NodeExistenceValidationRule(IValidationRule):
    """节点存在性验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证节点是否存在"""
        errors = []
        
        if isinstance(config, IEdgeConfig):
            node_names = set(context.graph_config.nodes.keys())
            
            if config.from_node not in node_names and config.from_node not in ["__start__"]:
                errors.append(f"起始节点 '{config.from_node}' 不存在")
            
            if config.to_node not in node_names and config.to_node not in ["__end__"] and config.type.value == "simple":
                errors.append(f"目标节点 '{config.to_node}' 不存在")
        
        return errors
    
    def get_rule_name(self) -> str:
        return "node_existence_validation"
    
    def get_priority(self) -> int:
        return 10


class FunctionNameValidationRule(IValidationRule):
    """函数名称验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证函数名称"""
        errors = []
        
        if isinstance(config, INodeConfig):
            if not config.function_name:
                errors.append("节点函数名称不能为空")
            elif not self._is_valid_function_name(config.function_name):
                errors.append(f"无效的函数名称: {config.function_name}")
        
        elif isinstance(config, IEdgeConfig) and config.type.value == "conditional":
            if config.condition and not self._is_valid_function_name(config.condition):
                errors.append(f"无效的条件函数名称: {config.condition}")
        
        return errors
    
    def _is_valid_function_name(self, name: str) -> bool:
        """检查函数名称是否有效"""
        if not name:
            return False
        
        # 函数名称应该以字母或下划线开头，只包含字母、数字和下划线
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, name))
    
    def get_rule_name(self) -> str:
        return "function_name_validation"
    
    def get_priority(self) -> int:
        return 20


class ConditionalEdgeValidationRule(IValidationRule):
    """条件边验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证条件边配置"""
        errors = []
        
        if isinstance(config, IEdgeConfig) and config.type.value == "conditional":
            # 检查是否为灵活条件边
            if hasattr(config, 'is_flexible_conditional') and config.is_flexible_conditional():
                if not hasattr(config, 'route_function') or not config.route_function:
                    errors.append("灵活条件边必须指定路由函数")
            else:
                # 传统条件边
                if not config.condition:
                    errors.append("条件边必须指定条件表达式")
        
        return errors
    
    def get_rule_name(self) -> str:
        return "conditional_edge_validation"
    
    def get_priority(self) -> int:
        return 30


class SelfLoopValidationRule(IValidationRule):
    """自循环验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证是否存在自循环"""
        errors = []
        
        if isinstance(config, IEdgeConfig):
            if config.from_node == config.to_node:
                errors.append("不允许节点自循环")
        
        return errors
    
    def get_rule_name(self) -> str:
        return "self_loop_validation"
    
    def get_priority(self) -> int:
        return 40


class EntryPointValidationRule(IValidationRule):
    """入口点验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证入口点配置"""
        errors = []
        
        # 这个规则在图级别验证，这里只是示例
        if hasattr(context.graph_config, 'entry_point') and context.graph_config.entry_point:
            node_names = set(context.graph_config.nodes.keys())
            if context.graph_config.entry_point not in node_names:
                errors.append(f"入口点节点 '{context.graph_config.entry_point}' 不存在")
        
        return errors
    
    def get_rule_name(self) -> str:
        return "entry_point_validation"
    
    def get_priority(self) -> int:
        return 50


class PathMapValidationRule(IValidationRule):
    """路径映射验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证路径映射配置"""
        errors = []
        
        if isinstance(config, IEdgeConfig) and config.path_map:
            node_names = set(context.graph_config.nodes.keys())
            
            for target_node in config.path_map.values():
                if target_node not in node_names and target_node not in ["__end__"]:
                    errors.append(f"路径映射中的目标节点 '{target_node}' 不存在")
        
        return errors
    
    def get_rule_name(self) -> str:
        return "path_map_validation"
    
    def get_priority(self) -> int:
        return 60


class CompositionValidationRule(IValidationRule):
    """组合验证规则"""
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证节点组合配置"""
        errors = []
        
        if isinstance(config, INodeConfig):
            # 检查组合名称和函数序列的一致性
            if hasattr(config, 'composition_name') and config.composition_name:
                if not hasattr(config, 'function_sequence') or not config.function_sequence:
                    errors.append("指定了组合名称但缺少函数序列")
            
            # 检查函数序列
            if hasattr(config, 'function_sequence') and config.function_sequence:
                for func_name in config.function_sequence:
                    if not self._is_valid_function_name(func_name):
                        errors.append(f"函数序列中包含无效的函数名称: {func_name}")
        
        return errors
    
    def _is_valid_function_name(self, name: str) -> bool:
        """检查函数名称是否有效"""
        if not name:
            return False
        
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, name))
    
    def get_rule_name(self) -> str:
        return "composition_validation"
    
    def get_priority(self) -> int:
        return 70


class CustomParameterValidationRule(IValidationRule):
    """自定义参数验证规则"""
    
    def __init__(self, parameter_name: str, validator_func: Callable, error_message: str, priority: int = 100):
        """初始化自定义参数验证规则
        
        Args:
            parameter_name: 参数名称
            validator_func: 验证函数，接收参数值，返回布尔值
            error_message: 错误消息
            priority: 验证优先级
        """
        self.parameter_name = parameter_name
        self.validator_func = validator_func
        self.error_message = error_message
        self._priority = priority
    
    def validate(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> List[str]:
        """验证自定义参数"""
        errors = []
        
        if hasattr(config, self.parameter_name):
            param_value = getattr(config, self.parameter_name)
            if not self.validator_func(param_value):
                errors.append(self.error_message.format(value=param_value))
        
        return errors
    
    def get_rule_name(self) -> str:
        return f"custom_parameter_validation_{self.parameter_name}"
    
    def get_priority(self) -> int:
        return self._priority


class ValidationRuleRegistry:
    """验证规则注册表"""
    
    def __init__(self):
        self._rules: Dict[str, IValidationRule] = {}
        self._register_default_rules()
    
    def register_rule(self, rule: IValidationRule) -> None:
        """注册验证规则"""
        self._rules[rule.get_rule_name()] = rule
    
    def get_rule(self, rule_name: str) -> Optional[IValidationRule]:
        """获取验证规则"""
        return self._rules.get(rule_name)
    
    def get_all_rules(self) -> List[IValidationRule]:
        """获取所有验证规则"""
        return list(self._rules.values())
    
    def get_rules_for_config_type(self, config_type: type) -> List[IValidationRule]:
        """根据配置类型获取适用的验证规则"""
        # 这里可以根据配置类型过滤规则，目前返回所有规则
        return self.get_all_rules()
    
    def _register_default_rules(self) -> None:
        """注册默认验证规则"""
        self.register_rule(BasicConfigValidationRule())
        self.register_rule(NodeExistenceValidationRule())
        self.register_rule(FunctionNameValidationRule())
        self.register_rule(ConditionalEdgeValidationRule())
        self.register_rule(SelfLoopValidationRule())
        self.register_rule(EntryPointValidationRule())
        self.register_rule(PathMapValidationRule())
        self.register_rule(CompositionValidationRule())


# 全局验证规则注册表实例
_global_validation_registry = ValidationRuleRegistry()


def get_validation_registry() -> ValidationRuleRegistry:
    """获取全局验证规则注册表
    
    Returns:
        ValidationRuleRegistry: 验证规则注册表实例
    """
    return _global_validation_registry


def register_validation_rule(rule: IValidationRule) -> None:
    """注册验证规则到全局注册表
    
    Args:
        rule: 验证规则
    """
    _global_validation_registry.register_rule(rule)


def create_custom_parameter_rule(
    parameter_name: str,
    validator_func: Callable,
    error_message: str,
    priority: int = 100
) -> CustomParameterValidationRule:
    """创建自定义参数验证规则的便捷函数
    
    Args:
        parameter_name: 参数名称
        validator_func: 验证函数
        error_message: 错误消息
        priority: 验证优先级
        
    Returns:
        CustomParameterValidationRule: 自定义验证规则
    """
    return CustomParameterValidationRule(
        parameter_name=parameter_name,
        validator_func=validator_func,
        error_message=error_message,
        priority=priority
    )