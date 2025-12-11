"""验证结果实现

提供IValidationResult接口的默认实现。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from src.interfaces.common_domain import IValidationResult


class ValidationResult(IValidationResult):
    """验证结果默认实现
    
    提供IValidationResult接口的标准实现，适用于大多数验证场景。
    """
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None,
                 info: List[str] = None, metadata: Dict[str, Any] = None):
        self._is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.info = info or []
        self.metadata = metadata or {}
    
    @property
    def is_valid(self) -> bool:
        """是否验证通过"""
        return self._is_valid
    
    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)
        self._is_valid = False
    
    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.info.append(message)
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return len(self.warnings) > 0