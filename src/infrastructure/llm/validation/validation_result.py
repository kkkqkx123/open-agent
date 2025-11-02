"""验证结果"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ValidationSeverity(Enum):
    """验证严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """验证问题"""
    
    field: str
    message: str
    severity: ValidationSeverity
    code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code,
            "context": self.context
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"[{self.severity.value.upper()}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    """验证结果"""
    
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Optional[str] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 如果传入了 is_valid 为 True 但有错误，应该修正为 False
        if self.is_valid and len(self.issues) > 0:
            has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
            if has_errors:
                self.is_valid = False
        elif self.is_valid is None:
            self.is_valid = len(self.issues) == 0
    
    def add_issue(self, field: str, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR, 
                  code: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """
        添加验证问题
        
        Args:
            field: 字段名
            message: 问题描述
            severity: 严重程度
            code: 错误代码
            context: 上下文信息
        """
        issue = ValidationIssue(
            field=field,
            message=message,
            severity=severity,
            code=code,
            context=context
        )
        self.issues.append(issue)
        # 更新is_valid状态，只要有任何问题就设为False
        self.is_valid = False
    
    def add_error(self, field: str, message: str, code: Optional[str] = None, 
                  context: Optional[Dict[str, Any]] = None) -> None:
        """添加错误"""
        self.add_issue(field, message, ValidationSeverity.ERROR, code, context)
    
    def add_warning(self, field: str, message: str, code: Optional[str] = None, 
                    context: Optional[Dict[str, Any]] = None) -> None:
        """添加警告"""
        self.add_issue(field, message, ValidationSeverity.WARNING, code, context)
    
    def add_info(self, field: str, message: str, code: Optional[str] = None, 
                context: Optional[Dict[str, Any]] = None) -> None:
        """添加信息"""
        self.add_issue(field, message, ValidationSeverity.INFO, code, context)
    
    def get_errors(self) -> List[ValidationIssue]:
        """获取所有错误"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """获取所有警告"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    def get_infos(self) -> List[ValidationIssue]:
        """获取所有信息"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.INFO]
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """根据严重程度获取问题"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)
    
    def get_field_issues(self, field: str) -> List[ValidationIssue]:
        """获取特定字段的问题"""
        return [issue for issue in self.issues if issue.field == field]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": self.summary,
            "error_count": len(self.get_errors()),
            "warning_count": len(self.get_warnings()),
            "info_count": len(self.get_infos()),
        }
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """合并验证结果"""
        combined = ValidationResult(is_valid=True)
        # 直接合并问题列表，避免调用 add_issue 导致的递归
        combined.issues = self.issues + other.issues
        # 手动更新 is_valid 状态
        combined.is_valid = len(combined.issues) == 0
        
        if self.summary and other.summary:
            combined.summary = f"{self.summary}; {other.summary}"
        elif self.summary:
            combined.summary = self.summary
        elif other.summary:
            combined.summary = other.summary
        
        return combined
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.is_valid:
            return "验证通过"
        
        error_count = len(self.get_errors())
        warning_count = len(self.get_warnings())
        
        if error_count > 0:
            return f"验证失败，发现 {error_count} 个错误"
        elif warning_count > 0:
            return f"验证通过，但有 {warning_count} 个警告"
        else:
            return "验证通过"
    
    def get_summary(self) -> str:
        """获取摘要"""
        if self.summary:
            return self.summary
        
        if self.is_valid:
            return "配置验证通过"
        
        error_count = len(self.get_errors())
        warning_count = len(self.get_warnings())
        
        if error_count > 0:
            return f"发现 {error_count} 个错误和 {warning_count} 个警告"
        elif warning_count > 0:
            return f"发现 {warning_count} 个警告"
        else:
            return "配置验证通过"