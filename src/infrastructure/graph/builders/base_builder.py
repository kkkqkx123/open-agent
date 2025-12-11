"""基础构建器实现

提供节点和边构建器的基础实现。
"""

from typing import Any, Dict, List, Optional, Union, Callable, overload, TypeVar
import logging

from src.interfaces.workflow.element_builder import (
    IElementBuilder, INodeBuilder, IEdgeBuilder,
    IValidationRule, IBuildStrategy, BuildContext
)
from src.interfaces.workflow.config import INodeConfig, IEdgeConfig

# Type variable for generic config
ConfigType = TypeVar('ConfigType', INodeConfig, IEdgeConfig, Union[INodeConfig, IEdgeConfig])


class BaseElementBuilder(IElementBuilder):
    """基础元素构建器
    
    提供通用的构建功能，包括验证和策略支持。
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        enable_caching: bool = True,
        enable_validation: bool = True
    ):
        """初始化基础元素构建器
        
        Args:
            logger: 日志记录器
            enable_caching: 是否启用缓存
            enable_validation: 是否启用验证
        """
        # 使用基础设施层的日志服务
        if logger is None:
            from src.interfaces.dependency_injection import get_logger
            self.logger = get_logger(self.__class__.__name__)
        else:
            self.logger = logger
            
        self.enable_caching = enable_caching
        self.enable_validation = enable_validation
        self._validation_rules: List[IValidationRule] = []
        self._build_strategies: List[IBuildStrategy] = []
        self._cache: Dict[str, Any] = {}
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return self.__class__.__name__.replace("Builder", "").lower()
    
    def build_element(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> Any:
        """构建元素
        
        Args:
            config: 配置对象
            context: 构建上下文
            
        Returns:
            Any: 构建的元素
        """
        # 验证配置
        if self.enable_validation:
            self._validate_config(config, context)
        
        # 应用构建策略
        for strategy in self._build_strategies:
            if strategy.can_handle(config, context):
                self.logger.debug(f"使用构建策略: {strategy.get_strategy_name()}")
                return strategy.execute(config, context, self)
        
        # 默认构建逻辑
        return self._build_element_impl(config, context)
    
    def add_validation_rule(self, rule: IValidationRule) -> None:
        """添加验证规则
        
        Args:
            rule: 验证规则
        """
        self._validation_rules.append(rule)
        self.logger.debug(f"添加验证规则: {rule.get_rule_name()}")
    
    def remove_validation_rule(self, rule_name: str) -> bool:
        """移除验证规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, rule in enumerate(self._validation_rules):
            if rule.get_rule_name() == rule_name:
                del self._validation_rules[i]
                self.logger.debug(f"移除验证规则: {rule_name}")
                return True
        return False
    
    def add_build_strategy(self, strategy: IBuildStrategy) -> None:
        """添加构建策略
        
        Args:
            strategy: 构建策略
        """
        self._build_strategies.append(strategy)
        self.logger.debug(f"添加构建策略: {strategy.get_strategy_name()}")
    
    def remove_build_strategy(self, strategy_name: str) -> bool:
        """移除构建策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, strategy in enumerate(self._build_strategies):
            if strategy.get_strategy_name() == strategy_name:
                del self._build_strategies[i]
                self.logger.debug(f"移除构建策略: {strategy_name}")
                return True
        return False
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        self.logger.debug("清除构建器缓存")
    
    def _validate_config(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> None:
        """验证配置
        
        Args:
            config: 配置对象
            context: 构建上下文
            
        Raises:
            ValueError: 验证失败
        """
        errors = []
        
        # 应用所有验证规则
        for rule in self._validation_rules:
            rule_errors = rule.validate(config, context)
            errors.extend(rule_errors)
        
        if errors:
            error_msg = f"配置验证失败:\n" + "\n".join(f"  - {error}" for error in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _build_element_impl(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> Any:
        """构建元素的具体实现
        
        子类应该重写此方法。
        
        Args:
            config: 配置对象
            context: 构建上下文
            
        Returns:
            Any: 构建的元素
        """
        raise NotImplementedError("子类必须实现 _build_element_impl 方法")


class BaseNodeBuilder(BaseElementBuilder, INodeBuilder):
    """基础节点构建器
    
    提供节点构建的基础功能。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "node"
    
    def get_node_function(self, config: INodeConfig, context: BuildContext) -> Optional[Callable]:
        """获取节点函数
        
        Args:
            config: 节点配置
            context: 构建上下文
            
        Returns:
            Optional[Callable]: 节点函数
        """
        # 默认实现：尝试从函数解析器获取
        if context.function_resolver and config.function_name:
            return context.function_resolver.get_node_function(
                config.function_name, 
                config.config
            )
        return None
    
    def _build_element_impl(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> Callable:  # type: ignore
        """构建节点的具体实现
        
        Args:
            config: 节点配置（从Union中接受INodeConfig部分）
            context: 构建上下文
            
        Returns:
            Callable: 节点函数
        """
        if not isinstance(config, INodeConfig):
            raise TypeError(f"Expected INodeConfig, got {type(config)}")
        
        # 尝试获取节点函数
        node_function = self.get_node_function(config, context)  # type: ignore
        if node_function:
            return node_function
        
        # 如果没有找到函数，创建一个默认函数
        def default_node_function(state: Any) -> Any:
            """默认节点函数"""
            self.logger.warning(f"使用默认节点函数: {config.name}")
            return state
        
        return default_node_function


class BaseEdgeBuilder(BaseElementBuilder, IEdgeBuilder):
    """基础边构建器
    
    提供边构建的基础功能。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "edge"
    
    def get_edge_function(self, config: IEdgeConfig, context: BuildContext) -> Optional[Callable]:
        """获取边函数
        
        Args:
            config: 边配置
            context: 构建上下文
            
        Returns:
            Optional[Callable]: 边函数
        """
        # 默认实现：尝试从函数解析器获取条件函数
        if context.function_resolver and config.condition:
            return context.function_resolver.get_condition_function(config.condition)
        return None
    
    def _build_element_impl(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> Dict[str, Any]:  # type: ignore
        """构建边的具体实现
        
        Args:
            config: 边配置（从Union中接受IEdgeConfig部分）
            context: 构建上下文
            
        Returns:
            Dict[str, Any]: 边数据
        """
        if not isinstance(config, IEdgeConfig):
            raise TypeError(f"Expected IEdgeConfig, got {type(config)}")
        
        edge_data = {
            "config": config,
            "condition_function": self.get_edge_function(config, context),  # type: ignore
            "path_map": config.path_map
        }
        
        return edge_data


class SimpleNodeBuilder(BaseNodeBuilder):
    """简单节点构建器
    
    用于构建简单类型的节点。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "simple_node"


class AsyncNodeBuilder(BaseNodeBuilder):
    """异步节点构建器
    
    用于构建异步类型的节点。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "async_node"


class StartNodeBuilder(BaseNodeBuilder):
    """开始节点构建器
    
    用于构建开始节点。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "start_node"


class EndNodeBuilder(BaseNodeBuilder):
    """结束节点构建器
    
    用于构建结束节点。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "end_node"


class SimpleEdgeBuilder(BaseEdgeBuilder):
    """简单边构建器
    
    用于构建简单类型的边。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "simple_edge"


class ConditionalEdgeBuilder(BaseEdgeBuilder):
    """条件边构建器
    
    用于构建条件边。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "conditional_edge"


class FlexibleConditionalEdgeBuilder(BaseEdgeBuilder):
    """灵活条件边构建器
    
    用于构建灵活条件边。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "flexible_conditional_edge"
    
    def _build_element_impl(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> Dict[str, Any]:  # type: ignore
        """构建灵活条件边的具体实现
        
        Args:
            config: 边配置（从Union中接受IEdgeConfig部分）
            context: 构建上下文
            
        Returns:
            Dict[str, Any]: 边数据
        """
        if not isinstance(config, IEdgeConfig):
            raise TypeError(f"Expected IEdgeConfig, got {type(config)}")
        
        # 检查是否有灵活条件边工厂
        if not hasattr(context, 'flexible_edge_factory') or not context.flexible_edge_factory:
            raise ValueError("灵活条件边工厂未设置")
        
        flexible_edge_factory = context.flexible_edge_factory
        flexible_edge = flexible_edge_factory.create_from_config(config)
        route_function = flexible_edge.create_route_function()
        
        edge_data = {
            "config": config,
            "condition_function": route_function,
            "path_map": config.path_map,
            "edge_type": "flexible_conditional"
        }
        
        return edge_data