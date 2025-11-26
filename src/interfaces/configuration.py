"""配置相关接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field


class ValidationSeverity(Enum):
    """验证严重程度枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """验证结果数据结构"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.info.append(message)
    
    def merge(self, other: 'ValidationResult') -> None:
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
            config: 配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        pass


class IConfigManager(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], config_path: str) -> None:
        """保存配置文件
        
        Args:
            config: 配置字典
            config_path: 配置文件路径
        """
        pass
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        pass