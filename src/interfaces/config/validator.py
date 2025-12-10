"""配置验证器接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

from ..common_domain import ValidationResult


class ValidationSeverity(Enum):
    """验证严重程度枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConfigValidationResult(ValidationResult):
    """配置验证结果 - 扩展通用验证结果"""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None, info: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        super().__init__(is_valid=is_valid, errors=errors or [],
                        warnings=warnings or [], metadata=metadata or {})
        self.info = info or []
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.info.append(message)
    
    def merge(self, other: 'ConfigValidationResult') -> None:
        """合并另一个验证结果"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        if not other.is_valid:
            self.is_valid = False
    
    def has_messages(self, severity: ValidationSeverity) -> bool:
        """检查是否有指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return len(self.errors) > 0
        elif severity == ValidationSeverity.WARNING:
            return len(self.warnings) > 0
        elif severity == ValidationSeverity.INFO:
            return len(self.info) > 0
        return False
    
    def get_messages(self, severity: ValidationSeverity) -> List[str]:
        """获取指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return self.errors
        elif severity == ValidationSeverity.WARNING:
            return self.warnings
        elif severity == ValidationSeverity.INFO:
            return self.info
        return []


class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        pass