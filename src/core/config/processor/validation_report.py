"""验证报告模块

提供高级验证结果和报告功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable
from datetime import datetime
from .validation_utils import ValidationLevel, ValidationSeverity


class FixSuggestion:
    """修复建议"""
    
    def __init__(self, description: str, fix_action: Callable, confidence: float = 0.8):
        self.description = description
        self.fix_action = fix_action
        self.confidence = confidence
    
    def apply(self) -> None:
        """应用修复建议"""
        if self.fix_action:
            self.fix_action()


class EnhancedValidationResult:
    """增强的验证结果"""
    
    def __init__(self, rule_id: str, level: ValidationLevel, passed: bool, message: str = ""):
        self.rule_id = rule_id
        self.level = level
        self.passed = passed
        self.message = message
        self.suggestions: List[str] = []
        self.fix_suggestions: List[FixSuggestion] = []
        self.timestamp = datetime.now()
        self.severity: ValidationSeverity = ValidationSeverity.WARNING
    
    def add_warning(self, warning: str) -> None:
        """添加警告信息"""
        self.message = warning
        self.severity = ValidationSeverity.WARNING


class ValidationReport:
    """验证报告"""
    
    def __init__(self, config_type: str):
        self.config_type = config_type # 修复：添加config_type属性
        self.config_path = config_type  # 保持向后兼容性，添加config_path属性
        self.timestamp = datetime.now()
        self.level_results: Dict[ValidationLevel, List[EnhancedValidationResult]] = {}
        self.summary: Dict[str, int] = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": 0
        }
    
    def get_results_by_level(self, level: str) -> List[EnhancedValidationResult]:
        """根据级别获取验证结果"""
        level_enum = ValidationLevel(level.lower())
        return self.level_results.get(level_enum, [])
    
    def add_level_results(self, level: ValidationLevel, results: List[EnhancedValidationResult]) -> None:
        """添加级别验证结果"""
        self.level_results[level] = results
        self._update_summary(level, results)
    
    def get_fix_suggestions(self) -> List[FixSuggestion]:
        """获取所有修复建议"""
        suggestions = []
        for results in self.level_results.values():
            for result in results:
                if not result.passed:
                    suggestions.extend(result.fix_suggestions)
        return suggestions
    
    def is_valid(self, min_severity: ValidationSeverity = ValidationSeverity.ERROR) -> bool:
        """检查配置是否有效"""
        # 定义严重性级别顺序
        severity_order = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.ERROR: 2,
            ValidationSeverity.CRITICAL: 3
        }
        
        for results in self.level_results.values():
            for result in results:
                if not result.passed:
                    # 比较严重性级别
                    if severity_order.get(result.severity, 0) >= severity_order.get(min_severity, 0):
                        return False
        return True
    
    @property
    def is_valid_property(self) -> bool:
        """配置是否有效的属性版本"""
        return self.is_valid()
    
    def _update_summary(self, level: ValidationLevel, results: List[EnhancedValidationResult]) -> None:
        """更新摘要统计"""
        self.summary["total_rules"] += len(results)
        
        for result in results:
            if result.passed:
                self.summary["passed"] += 1
            else:
                self.summary["failed"] += 1
                
                if result.severity == ValidationSeverity.WARNING:
                    self.summary["warnings"] += 1
                elif result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    self.summary["errors"] += 1