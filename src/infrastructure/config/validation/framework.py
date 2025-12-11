"""验证框架核心

定义验证级别、严重性、结果类型等核心概念。
只依赖接口层，不依赖其他层。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime

from src.interfaces.common_domain import IValidationResult


class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX = "syntax"           # 语法验证：YAML/JSON格式
    SCHEMA = "schema"           # 模式验证：数据结构
    SEMANTIC = "semantic"       # 语义验证：业务逻辑
    DEPENDENCY = "dependency"   # 依赖验证：外部依赖
    PERFORMANCE = "performance" # 性能验证：性能指标


class ValidationSeverity(Enum):
    """验证严重性级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IFixSuggestion(Protocol):
    """修复建议接口"""
    
    @property
    def description(self) -> str:
        """修复描述"""
        ...
    
    @property
    def auto_fixable(self) -> bool:
        """是否可自动修复"""
        ...
    
    def apply_fix(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用修复
        
        Args:
            config: 原始配置
            
        Returns:
            修复后的配置
        """
        ...


class FrameworkValidationResult(IValidationResult):
    """框架验证结果
    
    实现IValidationResult接口，提供更详细的验证信息，包括规则ID、级别、时间戳等。
    """
    
    def __init__(self, rule_id: str, level: ValidationLevel, passed: bool, message: str = ""):
        self.rule_id = rule_id
        self.level = level
        self.passed = passed
        self.message = message
        self.suggestions: List[str] = []
        self.fix_suggestions: List[IFixSuggestion] = []
        self.timestamp = datetime.now()
        self.severity: ValidationSeverity = ValidationSeverity.WARNING
        self.metadata: Dict[str, Any] = {}
    
    @property
    def is_valid(self) -> bool:
        """是否验证通过"""
        return self.passed
    
    @property
    def errors(self) -> List[str]:
        """错误信息列表"""
        return [self.message] if self.severity == ValidationSeverity.ERROR else []
    
    @property
    def warnings(self) -> List[str]:
        """警告信息列表"""
        return [self.message] if self.severity == ValidationSeverity.WARNING else []
    
    @property
    def info(self) -> List[str]:
        """信息列表"""
        return [self.message] if self.severity == ValidationSeverity.INFO else []
    
    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.message = message
        self.severity = ValidationSeverity.WARNING
    
    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.message = message
        self.severity = ValidationSeverity.ERROR
        self.passed = False
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.message = message
        self.severity = ValidationSeverity.INFO
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据"""
        self.metadata[key] = value
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return self.severity == ValidationSeverity.ERROR
    
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return self.severity == ValidationSeverity.WARNING


class ValidationReport:
    """验证报告
    
    收集和组织多个验证结果，提供汇总信息。
    """
    
    def __init__(self, config_type: str, config_path: Optional[str] = None):
        self.config_type = config_type
        self.config_path = config_path or config_type
        self.timestamp = datetime.now()
        self.level_results: Dict[ValidationLevel, List[FrameworkValidationResult]] = {}
        self.summary: Dict[str, int] = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": 0,
            "info": 0
        }
        self.metadata: Dict[str, Any] = {}
    
    def get_results_by_level(self, level: str) -> List[FrameworkValidationResult]:
        """根据级别获取验证结果
        
        Args:
            level: 验证级别
            
        Returns:
            验证结果列表
        """
        try:
            level_enum = ValidationLevel(level.lower())
            return self.level_results.get(level_enum, [])
        except ValueError:
            return []
    
    def add_level_results(self, level: ValidationLevel, results: List[FrameworkValidationResult]) -> None:
        """添加级别验证结果
        
        Args:
            level: 验证级别
            results: 验证结果列表
        """
        self.level_results[level] = results
        self._update_summary(level, results)
    
    def get_fix_suggestions(self) -> List[IFixSuggestion]:
        """获取所有修复建议
        
        Returns:
            修复建议列表
        """
        suggestions = []
        for results in self.level_results.values():
            for result in results:
                if not result.passed:
                    suggestions.extend(result.fix_suggestions)
        return suggestions
    
    def is_valid(self, min_severity: ValidationSeverity = ValidationSeverity.ERROR) -> bool:
        """检查配置是否有效
        
        Args:
            min_severity: 最低严重性级别
            
        Returns:
            是否有效
        """
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
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据
        
        Args:
            key: 键
            value: 值
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def _update_summary(self, level: ValidationLevel, results: List[FrameworkValidationResult]) -> None:
        """更新摘要统计
        
        Args:
            level: 验证级别
            results: 验证结果列表
        """
        self.summary["total_rules"] += len(results)
        
        for result in results:
            if result.passed:
                self.summary["passed"] += 1
            else:
                self.summary["failed"] += 1
                
                if result.severity == ValidationSeverity.WARNING:
                    self.summary["warnings"] += 1
                elif result.severity == ValidationSeverity.ERROR:
                    self.summary["errors"] += 1
                elif result.severity == ValidationSeverity.CRITICAL:
                    self.summary["errors"] += 1
                elif result.severity == ValidationSeverity.INFO:
                    self.summary["info"] += 1

