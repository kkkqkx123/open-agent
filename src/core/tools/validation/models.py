"""
验证模块数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class ValidationStatus(Enum):
    """验证状态枚举"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """验证问题"""
    level: ValidationStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """后处理，确保类型正确"""
        if not isinstance(self.details, dict):
            self.details = dict(self.details) if self.details else {}


@dataclass
class ValidationResult:
    """验证结果"""
    tool_name: str
    tool_type: str
    status: ValidationStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_issue(self, level: ValidationStatus, message: str, **kwargs):
        """添加验证问题"""
        suggestion = kwargs.pop('suggestion', None)
        details = kwargs.copy()
        self.issues.append(ValidationIssue(level, message, details, suggestion))
        # 更新总体状态（取最严重的状态）
        if level == ValidationStatus.ERROR:
            self.status = ValidationStatus.ERROR
        elif level == ValidationStatus.WARNING and self.status != ValidationStatus.ERROR:
            self.status = ValidationStatus.WARNING
    
    def is_successful(self) -> bool:
        """检查验证是否成功"""
        return self.status == ValidationStatus.SUCCESS
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return any(issue.level == ValidationStatus.ERROR for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return any(issue.level == ValidationStatus.WARNING for issue in self.issues)
    
    def merge(self, other: 'ValidationResult') -> None:
        """合并另一个验证结果"""
        self.issues.extend(other.issues)
        # 更新状态
        if other.status == ValidationStatus.ERROR:
            self.status = ValidationStatus.ERROR
        elif other.status == ValidationStatus.WARNING and self.status != ValidationStatus.ERROR:
            self.status = ValidationStatus.WARNING
        
        # 合并元数据
        self.metadata.update(other.metadata)
    
    def get_error_count(self) -> int:
        """获取错误数量"""
        return sum(1 for issue in self.issues if issue.level == ValidationStatus.ERROR)
    
    def get_warning_count(self) -> int:
        """获取警告数量"""
        return sum(1 for issue in self.issues if issue.level == ValidationStatus.WARNING)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "tool_name": self.tool_name,
            "tool_type": self.tool_type,
            "status": self.status.value,
            "issues": [
                {
                    "level": issue.level.value,
                    "message": issue.message,
                    "details": issue.details,
                    "suggestion": issue.suggestion,
                    "timestamp": issue.timestamp.isoformat()
                }
                for issue in self.issues
            ],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "error_count": self.get_error_count(),
            "warning_count": self.get_warning_count()
        }


# 导出所有模型
__all__ = [
    "ValidationStatus",
    "ValidationIssue",
    "ValidationResult",
]