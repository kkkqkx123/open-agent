"""验证规则注册表

管理配置验证规则的注册、查找和执行。
"""

from typing import Dict, List, Type, Any, Optional, Callable

from src.infrastructure.validation.result import ValidationResult
from src.interfaces.config.validation import IValidationRule, IValidationContext, IValidationRuleRegistry


class ValidationRuleRegistry(IValidationRuleRegistry):
    """验证规则注册表
    
    管理所有配置验证规则的注册和查找。
    """
    
    def __init__(self):
        """初始化注册表"""
        self._rules: Dict[str, List[IValidationRule]] = {}
        self._rule_cache: Dict[str, IValidationRule] = {}
    
    def register_rule(self, rule: IValidationRule) -> None:
        """注册验证规则
        
        Args:
            rule: 验证规则
        """
        config_type = rule.config_type
        if config_type not in self._rules:
            self._rules[config_type] = []
        
        self._rules[config_type].append(rule)
        
        # 按优先级排序
        self._rules[config_type].sort(key=lambda r: r.priority)
        
        # 清除缓存
        self._rule_cache.clear()
    
    def unregister_rule(self, rule_id: str) -> bool:
        """注销验证规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否成功注销
        """
        for config_type, rules in self._rules.items():
            self._rules[config_type] = [r for r in rules if r.rule_id != rule_id]
            if len(self._rules[config_type]) != len(rules):
                # 清除缓存
                self._rule_cache.clear()
                return True
        return False
    
    def get_rules(self, config_type: str) -> List[IValidationRule]:
        """获取指定配置类型的所有规则
        
        Args:
            config_type: 配置类型
            
        Returns:
            验证规则列表
        """
        return self._rules.get(config_type, []).copy()
    
    def get_rule(self, rule_id: str) -> Optional[IValidationRule]:
        """根据ID获取验证规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            验证规则或None
        """
        # 先检查缓存
        if rule_id in self._rule_cache:
            return self._rule_cache[rule_id]
        
        # 搜索规则
        for rules in self._rules.values():
            for rule in rules:
                if rule.rule_id == rule_id:
                    self._rule_cache[rule_id] = rule
                    return rule
        
        return None
    
    def validate_config(self, config_type: str, config: Dict[str, Any], 
                       context: IValidationContext) -> ValidationResult:
        """使用所有适用的规则验证配置
        
        Args:
            config_type: 配置类型
            config: 配置数据
            context: 验证上下文
            
        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        rules = self.get_rules(config_type)
        if not rules:
            result.add_warning(f"没有找到配置类型 '{config_type}' 的验证规则")
            return result
        
        for rule in rules:
            try:
                rule_result = rule.validate(config, context)
                
                # 合并结果
                if not rule_result.is_valid:
                    result.is_valid = False
                    result.errors.extend(rule_result.errors)
                
                result.warnings.extend(rule_result.warnings)
                
                # 记录验证步骤
                context.add_validation_step(
                    rule.rule_id,
                    {
                        "is_valid": rule_result.is_valid,
                        "errors": rule_result.errors,
                        "warnings": rule_result.warnings
                    }
                )
                
            except Exception as e:
                error_msg = f"验证规则 '{rule.rule_id}' 执行失败: {str(e)}"
                result.add_error(error_msg)
        
        return result
    
    def get_supported_config_types(self) -> List[str]:
        """获取支持的配置类型列表
        
        Returns:
            配置类型列表
        """
        return list(self._rules.keys())
    
    def clear_rules(self, config_type: Optional[str] = None) -> None:
        """清除规则
        
        Args:
            config_type: 配置类型，None表示清除所有
        """
        if config_type:
            if config_type in self._rules:
                del self._rules[config_type]
        else:
            self._rules.clear()
        
        self._rule_cache.clear()
    
    def register_rule_class(self, rule_class: Type[IValidationRule], 
                           config_types: List[str]) -> None:
        """注册规则类
        
        Args:
            rule_class: 规则类
            config_types: 适用的配置类型列表
        """
        for config_type in config_types:
            try:
                rule_instance = rule_class()
                self.register_rule(rule_instance)
            except Exception as e:
                raise ValueError(f"无法实例化规则类 {rule_class.__name__} 用于配置类型 {config_type}: {e}")
    
    def register_rules_from_module(self, module_path: str) -> None:
        """从模块注册规则
        
        Args:
            module_path: 模块路径
        """
        import importlib
        
        try:
            module = importlib.import_module(module_path)
            
            # 查找模块中的验证规则类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type):
                    # 检查是否符合IValidationRule协议
                    try:
                        if isinstance(attr, IValidationRule) or (
                            hasattr(attr, 'rule_id') and 
                            hasattr(attr, 'config_type') and 
                            hasattr(attr, 'priority') and 
                            hasattr(attr, 'validate')
                        ):
                            # 尝试实例化并注册
                            try:
                                rule_instance = attr()
                                self.register_rule(rule_instance)
                            except Exception:
                                # 跳过无法实例化的规则
                                continue
                    except Exception:
                        # 跳过类检查失败的属性
                        continue
                        
        except ImportError as e:
            raise ValueError(f"无法导入模块 {module_path}: {e}")