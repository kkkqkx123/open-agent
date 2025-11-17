"""
工具检验模块数据模型
定义了验证结果相关的数据结构
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