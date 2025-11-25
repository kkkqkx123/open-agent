"""配置验证规则实现"""

import logging
import re
from typing import Dict, Any, List, Type, Optional, Union, Callable
from abc import ABC, abstractmethod

from src.interfaces.configuration import IValidationRule, ValidationResult

logger = logging.getLogger(__name__)


class BaseValidationRule(IValidationRule):
    """基础验证规则"""
    
    def __init__(self, rule_name: str, description: str = ""):
        self._rule_name = rule_name
        self._description = description
    
    def get_rule_name(self) -> str:
        return self._rule_name
    
    def get_description(self) -> str:
        return self._description


class RequiredFieldRule(BaseValidationRule):
    """必需字段验证规则"""
    
    def __init__(self, field_name: str, description: Optional[str] = None):
        super().__init__(
            f"required_field_{field_name}",
            description or f"字段 {field_name} 是必需的"
        )
        self._field_name = field_name
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证必需字段"""
        if self._field_name not in config:
            return ValidationResult(
                is_valid=False,
                errors=[f"缺少必需字段: {self._field_name}"],
                warnings=[]
            )
        
        value = config[self._field_name]
        if value is None or value == "":
            return ValidationResult(
                is_valid=False,
                errors=[f"必需字段 {self._field_name} 不能为空"],
                warnings=[]
            )
        
        return ValidationResult(True, [], [])


class FieldTypeRule(BaseValidationRule):
    """字段类型验证规则"""
    
    def __init__(self, field_name: str, expected_type: Type, description: Optional[str] = None):
        super().__init__(
            f"field_type_{field_name}",
            description or f"字段 {field_name} 必须是 {expected_type.__name__} 类型"
        )
        self._field_name = field_name
        self._expected_type = expected_type
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证字段类型"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])  # 字段不存在，由其他规则处理
        
        value = config[self._field_name]
        if not isinstance(value, self._expected_type):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 类型错误，期望 {self._expected_type.__name__}，实际 {type(value).__name__}"],
                warnings=[]
            )
        
        return ValidationResult(True, [], [])


class RangeRule(BaseValidationRule):
    """数值范围验证规则"""
    
    def __init__(self, field_name: str, min_value: Optional[Union[int, float]] = None, 
                 max_value: Optional[Union[int, float]] = None, description: Optional[str] = None):
        super().__init__(
            f"range_{field_name}",
            description or f"字段 {field_name} 必须在指定范围内"
        )
        self._field_name = field_name
        self._min_value = min_value
        self._max_value = max_value
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证数值范围"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])
        
        value = config[self._field_name]
        if not isinstance(value, (int, float)):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 必须是数值类型"],
                warnings=[]
            )
        
        errors = []
        if self._min_value is not None and value < self._min_value:
            errors.append(f"字段 {self._field_name} 值 {value} 小于最小值 {self._min_value}")
        
        if self._max_value is not None and value > self._max_value:
            errors.append(f"字段 {self._field_name} 值 {value} 大于最大值 {self._max_value}")
        
        return ValidationResult(len(errors) == 0, errors, [])


class EnumRule(BaseValidationRule):
    """枚举值验证规则"""
    
    def __init__(self, field_name: str, allowed_values: List[Any], description: Optional[str] = None):
        super().__init__(
            f"enum_{field_name}",
            description or f"字段 {field_name} 必须是允许的值之一"
        )
        self._field_name = field_name
        self._allowed_values = allowed_values
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证枚举值"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])
        
        value = config[self._field_name]
        if value not in self._allowed_values:
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 值 {value} 不在允许的值列表中: {self._allowed_values}"],
                warnings=[]
            )
        
        return ValidationResult(True, [], [])


class RegexRule(BaseValidationRule):
    """正则表达式验证规则"""
    
    def __init__(self, field_name: str, pattern: str, description: Optional[str] = None):
        super().__init__(
            f"regex_{field_name}",
            description or f"字段 {field_name} 必须匹配正则表达式 {pattern}"
        )
        self._field_name = field_name
        self._pattern = pattern
        self._compiled_pattern = re.compile(pattern)
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证正则表达式"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])
        
        value = config[self._field_name]
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 必须是字符串类型"],
                warnings=[]
            )
        
        if not self._compiled_pattern.match(value):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 值 {value} 不匹配正则表达式 {self._pattern}"],
                warnings=[]
            )
        
        return ValidationResult(True, [], [])


class UrlRule(BaseValidationRule):
    """URL验证规则"""
    
    def __init__(self, field_name: str, schemes: Optional[List[str]] = None, description: Optional[str] = None):
        super().__init__(
            f"url_{field_name}",
            description or f"字段 {field_name} 必须是有效的URL"
        )
        self._field_name = field_name
        self._schemes = schemes or ['http', 'https', 'ftp']
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证URL"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])
        
        value = config[self._field_name]
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 必须是字符串类型"],
                warnings=[]
            )
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(value)
            
            if not parsed.scheme:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"字段 {self._field_name} 缺少URL协议"],
                    warnings=[]
                )
            
            if parsed.scheme not in self._schemes:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"字段 {self._field_name} 协议 {parsed.scheme} 不在允许的协议列表中: {self._schemes}"],
                    warnings=[]
                )
            
            if not parsed.netloc:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"字段 {self._field_name} 缺少URL主机名"],
                    warnings=[]
                )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} URL格式错误: {e}"],
                warnings=[]
            )
        
        return ValidationResult(True, [], [])


class EmailRule(BaseValidationRule):
    """邮箱验证规则"""
    
    def __init__(self, field_name: str, description: Optional[str] = None):
        super().__init__(
            f"email_{field_name}",
            description or f"字段 {field_name} 必须是有效的邮箱地址"
        )
        self._field_name = field_name
        # 简单的邮箱正则表达式
        self._email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证邮箱"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])
        
        value = config[self._field_name]
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 必须是字符串类型"],
                warnings=[]
            )
        
        if not re.match(self._email_pattern, value):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 值 {value} 不是有效的邮箱地址"],
                warnings=[]
            )
        
        return ValidationResult(True, [], [])


class CustomRule(BaseValidationRule):
    """自定义验证规则"""
    
    def __init__(self, rule_name: str, validator_func: Callable[[Dict[str, Any]], ValidationResult], description: Optional[str] = None):
        super().__init__(rule_name, description or "")
        self._validator_func = validator_func
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """执行自定义验证"""
        try:
            result = self._validator_func(config)
            if not isinstance(result, ValidationResult):
                return ValidationResult(
                    is_valid=False,
                    errors=[f"自定义验证函数必须返回 ValidationResult 对象"],
                    warnings=[]
                )
            return result
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"自定义验证规则 {self._rule_name} 执行失败: {e}"],
                warnings=[]
            )


class ConditionalRule(BaseValidationRule):
    """条件验证规则"""
    
    def __init__(self, rule_name: str, condition_func: Callable[[Dict[str, Any]], bool],
                 true_rule: IValidationRule, false_rule: Optional[IValidationRule] = None,
                 description: Optional[str] = None):
        super().__init__(rule_name, description or "")
        self._condition_func = condition_func
        self._true_rule = true_rule
        self._false_rule = false_rule
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """根据条件执行验证"""
        try:
            if self._condition_func(config):
                return self._true_rule.validate(config)
            elif self._false_rule:
                return self._false_rule.validate(config)
            else:
                return ValidationResult(True, [], [])
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"条件验证规则 {self._rule_name} 执行失败: {e}"],
                warnings=[]
            )


class CompositeRule(BaseValidationRule):
    """复合验证规则"""
    
    def __init__(self, rule_name: str, rules: List[IValidationRule], 
                 require_all: bool = True, description: Optional[str] = None):
        super().__init__(rule_name, description or "")
        self._rules = rules
        self._require_all = require_all  # True: 所有规则都必须通过，False: 至少一个规则通过
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """执行复合验证"""
        all_errors = []
        all_warnings = []
        passed_count = 0
        
        for rule in self._rules:
            result = rule.validate(config)
            if result.is_valid:
                passed_count += 1
            else:
                all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        if self._require_all:
            # 所有规则都必须通过
            is_valid = passed_count == len(self._rules)
        else:
            # 至少一个规则通过
            is_valid = passed_count > 0
        
        return ValidationResult(is_valid, all_errors, all_warnings)


class NestedRule(BaseValidationRule):
    """嵌套对象验证规则"""
    
    def __init__(self, field_name: str, nested_rules: List[IValidationRule], 
                 description: Optional[str] = None):
        super().__init__(
            f"nested_{field_name}",
            description or f"字段 {field_name} 的嵌套对象验证"
        )
        self._field_name = field_name
        self._nested_rules = nested_rules
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证嵌套对象"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])
        
        nested_config = config[self._field_name]
        if not isinstance(nested_config, dict):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 必须是字典类型"],
                warnings=[]
            )
        
        all_errors = []
        all_warnings = []
        
        for rule in self._nested_rules:
            result = rule.validate(nested_config)
            if not result.is_valid:
                all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return ValidationResult(len(all_errors) == 0, all_errors, all_warnings)


class ListRule(BaseValidationRule):
    """列表验证规则"""
    
    def __init__(self, field_name: str, item_rule: Optional[IValidationRule] = None,
                 min_length: Optional[int] = None, max_length: Optional[int] = None,
                 description: Optional[str] = None):
        super().__init__(
            f"list_{field_name}",
            description or f"字段 {field_name} 的列表验证"
        )
        self._field_name = field_name
        self._item_rule = item_rule
        self._min_length = min_length
        self._max_length = max_length
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证列表"""
        if self._field_name not in config:
            return ValidationResult(True, [], [])
        
        value = config[self._field_name]
        if not isinstance(value, list):
            return ValidationResult(
                is_valid=False,
                errors=[f"字段 {self._field_name} 必须是列表类型"],
                warnings=[]
            )
        
        errors = []
        warnings = []
        
        # 验证长度
        if self._min_length is not None and len(value) < self._min_length:
            errors.append(f"字段 {self._field_name} 长度 {len(value)} 小于最小长度 {self._min_length}")
        
        if self._max_length is not None and len(value) > self._max_length:
            errors.append(f"字段 {self._field_name} 长度 {len(value)} 大于最大长度 {self._max_length}")
        
        # 验证列表项
        if self._item_rule:
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    result = self._item_rule.validate(item)
                    if not result.is_valid:
                        errors.extend([f"列表项 {i}: {error}" for error in result.errors])
                    warnings.extend([f"列表项 {i}: {warning}" for warning in result.warnings])
        
        return ValidationResult(len(errors) == 0, errors, warnings)


# 预定义的常用验证规则
class CommonValidationRules:
    """常用验证规则集合"""
    
    @staticmethod
    def required_string(field_name: str) -> RequiredFieldRule:
        """必需字符串字段"""
        return RequiredFieldRule(field_name)
    
    @staticmethod
    def positive_integer(field_name: str) -> CompositeRule:
        """正整数字段"""
        return CompositeRule(
            f"positive_int_{field_name}",
            [
                RequiredFieldRule(field_name),
                FieldTypeRule(field_name, int),
                RangeRule(field_name, min_value=1)
            ]
        )
    
    @staticmethod
    def non_negative_integer(field_name: str) -> CompositeRule:
        """非负整数字段"""
        return CompositeRule(
            f"non_negative_int_{field_name}",
            [
                RequiredFieldRule(field_name),
                FieldTypeRule(field_name, int),
                RangeRule(field_name, min_value=0)
            ]
        )
    
    @staticmethod
    def port_number(field_name: str) -> CompositeRule:
        """端口号字段"""
        return CompositeRule(
            f"port_{field_name}",
            [
                RequiredFieldRule(field_name),
                FieldTypeRule(field_name, int),
                RangeRule(field_name, min_value=1, max_value=65535)
            ]
        )
    
    @staticmethod
    def boolean_field(field_name: str) -> CompositeRule:
        """布尔字段"""
        return CompositeRule(
            f"bool_{field_name}",
            [
                RequiredFieldRule(field_name),
                FieldTypeRule(field_name, bool)
            ]
        )
    
    @staticmethod
    def url_field(field_name: str, schemes: Optional[List[str]] = None) -> CompositeRule:
        """URL字段"""
        return CompositeRule(
            f"url_{field_name}",
            [
                RequiredFieldRule(field_name),
                UrlRule(field_name, schemes)
            ]
        )
    
    @staticmethod
    def email_field(field_name: str) -> CompositeRule:
        """邮箱字段"""
        return CompositeRule(
            f"email_{field_name}",
            [
                RequiredFieldRule(field_name),
                EmailRule(field_name)
            ]
        )