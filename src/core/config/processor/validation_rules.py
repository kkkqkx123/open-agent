"""验证规则模块

提供可扩展的验证规则框架。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .validation_utils import ValidationLevel
from .validation_report import EnhancedValidationResult


class ValidationRule(ABC):
    """验证规则基类"""
    
    def __init__(self, rule_id: str, level: ValidationLevel, description: str):
        self.rule_id = rule_id
        self.level = level
        self.description = description
    
    @abstractmethod
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> EnhancedValidationResult:
        """执行验证"""
        pass