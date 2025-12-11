"""验证规则模块

包含所有具体的验证规则实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import re

from src.interfaces.config.validation import ValidationLevel, ValidationSeverity
from .framework import FrameworkValidationResult


class ValidationRule(ABC):
    """验证规则基类"""
    
    def __init__(self, rule_id: str, level: ValidationLevel, description: str):
        self.rule_id = rule_id
        self.level = level
        self.description = description
    
    @abstractmethod
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> FrameworkValidationResult:
        """执行验证"""
        pass


class RequiredFieldRule(ValidationRule):
    """必需字段验证规则"""
    
    def __init__(self, field_path: str, field_type: Optional[type] = None):
        rule_id = f"required_field_{field_path.replace('.', '_')}"
        description = f"验证字段 '{field_path}' 是否存在且不为None"
        super().__init__(rule_id, ValidationLevel.SCHEMA, description)
        self.field_path = field_path
        self.field_type = field_type
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> FrameworkValidationResult:
        """验证字段是否存在"""
        keys = self.field_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                result = FrameworkValidationResult(
                    self.rule_id,
                    self.level,
                    False,
                    f"缺少必需字段: {self.field_path}"
                )
                result.severity = ValidationSeverity.ERROR
                return result
            current = current[key]
        
        # 如果指定了字段类型，验证类型
        if self.field_type and not isinstance(current, self.field_type):
            result = FrameworkValidationResult(
                self.rule_id,
                self.level,
                False,
                f"字段 '{self.field_path}' 类型错误，期望 {self.field_type.__name__}，实际 {type(current).__name__}"
            )
            result.severity = ValidationSeverity.ERROR
            return result
        
        result = FrameworkValidationResult(
            self.rule_id,
            self.level,
            True,
            f"字段 '{self.field_path}' 存在且类型正确"
        )
        return result


class ValueRangeRule(ValidationRule):
    """值范围验证规则"""
    
    def __init__(self, field_path: str, min_value: Optional[float] = None, max_value: Optional[float] = None):
        rule_id = f"value_range_{field_path.replace('.', '_')}"
        description = f"验证字段 '{field_path}' 的值是否在指定范围内"
        super().__init__(rule_id, ValidationLevel.SEMANTIC, description)
        self.field_path = field_path
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> FrameworkValidationResult:
        """验证值范围"""
        keys = self.field_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                result = FrameworkValidationResult(
                    self.rule_id,
                    self.level,
                    False,
                    f"字段不存在: {self.field_path}"
                )
                result.severity = ValidationSeverity.ERROR
                return result
            current = current[key]
        
        # 验证是否为数值类型
        if not isinstance(current, (int, float)):
            result = FrameworkValidationResult(
                self.rule_id,
                self.level,
                False,
                f"字段 '{self.field_path}' 不是数值类型，无法进行范围验证"
            )
            result.severity = ValidationSeverity.ERROR
            return result
        
        # 验证范围
        if self.min_value is not None and current < self.min_value:
            result = FrameworkValidationResult(
                self.rule_id,
                self.level,
                False,
                f"字段 '{self.field_path}' 值 {current} 小于最小值 {self.min_value}"
            )
            result.severity = ValidationSeverity.ERROR
            return result
        
        if self.max_value is not None and current > self.max_value:
            result = FrameworkValidationResult(
                self.rule_id,
                self.level,
                False,
                f"字段 '{self.field_path}' 值 {current} 大于最大值 {self.max_value}"
            )
            result.severity = ValidationSeverity.ERROR
            return result
        
        result = FrameworkValidationResult(
            self.rule_id,
            self.level,
            True,
            f"字段 '{self.field_path}' 值 {current} 在有效范围内"
        )
        return result


class RegexPatternRule(ValidationRule):
    """正则表达式验证规则"""
    
    def __init__(self, field_path: str, pattern: str, description: Optional[str] = None):
        rule_id = f"regex_pattern_{field_path.replace('.', '_')}"
        desc = description or f"验证字段 '{field_path}' 是否符合正则表达式模式"
        super().__init__(rule_id, ValidationLevel.SEMANTIC, desc)
        self.field_path = field_path
        self.pattern = pattern
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> FrameworkValidationResult:
        """验证正则表达式"""
        keys = self.field_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                result = FrameworkValidationResult(
                    self.rule_id,
                    self.level,
                    False,
                    f"字段不存在: {self.field_path}"
                )
                result.severity = ValidationSeverity.ERROR
                return result
            current = current[key]
        
        # 验证是否为字符串类型
        if not isinstance(current, str):
            result = FrameworkValidationResult(
                self.rule_id,
                self.level,
                False,
                f"字段 '{self.field_path}' 不是字符串类型，无法进行正则验证"
            )
            result.severity = ValidationSeverity.ERROR
            return result
        
        # 验证正则表达式
        if not re.match(self.pattern, current):
            result = FrameworkValidationResult(
                self.rule_id,
                self.level,
                False,
                f"字段 '{self.field_path}' 值 '{current}' 不符合正则表达式模式: {self.pattern}"
            )
            result.severity = ValidationSeverity.ERROR
            return result
        
        result = FrameworkValidationResult(
            self.rule_id,
            self.level,
            True,
            f"字段 '{self.field_path}' 值 '{current}' 符合正则表达式模式"
        )
        return result