"""配置相关接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum

from .common_domain import ValidationResult


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
    def validate(self, config: Dict[str, Any]) -> ConfigValidationResult:
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
    def validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        pass


# 配置异常定义
class ConfigError(Exception):
    """配置基础异常"""
    
    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.config_path = config_path
        self.details = details or {}


class ConfigurationValidationError(ConfigError):
    """配置验证异常"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, details=kwargs)
        self.config_key = config_key
        
        if config_key:
            self.details["config_key"] = config_key


class ConfigurationLoadError(ConfigError):
    """配置加载异常"""
    
    def __init__(
        self,
        message: str,
        load_error: Optional[str] = None,
        file_format: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, details=kwargs)
        self.load_error = load_error
        self.file_format = file_format
        
        if load_error:
            self.details["load_error"] = load_error
        if file_format:
            self.details["file_format"] = file_format


class ConfigurationEnvironmentError(ConfigError):
    """配置环境变量异常"""
    
    def __init__(
        self,
        message: str,
        env_var_name: Optional[str] = None,
        env_var_value: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, details=kwargs)
        self.env_var_name = env_var_name
        self.env_var_value = env_var_value
        
        if env_var_name:
            self.details["env_var_name"] = env_var_name
        if env_var_value:
            self.details["env_var_value"] = env_var_value


class ConfigurationParseError(ConfigError):
    """配置解析异常"""
    
    def __init__(
        self,
        message: str,
        parse_error: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(message, details=kwargs)
        self.parse_error = parse_error
        self.line_number = line_number
        self.column_number = column_number
        
        if parse_error:
            self.details["parse_error"] = parse_error
        if line_number:
            self.details["line_number"] = line_number
        if column_number:
            self.details["column_number"] = column_number


class ConfigurationMergeError(ConfigError):
    """配置合并异常"""
    
    def __init__(
        self,
        message: str,
        source_config: Optional[str] = None,
        target_config: Optional[str] = None,
        merge_conflict: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, details=kwargs)
        self.source_config = source_config
        self.target_config = target_config
        self.merge_conflict = merge_conflict
        
        if source_config:
            self.details["source_config"] = source_config
        if target_config:
            self.details["target_config"] = target_config
        if merge_conflict:
            self.details["merge_conflict"] = merge_conflict


class ConfigurationSchemaError(ConfigError):
    """配置模式异常"""
    
    def __init__(
        self,
        message: str,
        schema_path: Optional[str] = None,
        schema_version: Optional[str] = None,
        schema_error: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, details=kwargs)
        self.schema_path = schema_path
        self.schema_version = schema_version
        self.schema_error = schema_error
        
        if schema_path:
            self.details["schema_path"] = schema_path
        if schema_version:
            self.details["schema_version"] = schema_version
        if schema_error:
            self.details["schema_error"] = schema_error


class ConfigurationInheritanceError(ConfigError):
    """配置继承异常"""
    
    def __init__(
        self,
        message: str,
        parent_config: Optional[str] = None,
        child_config: Optional[str] = None,
        inheritance_error: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, details=kwargs)
        self.parent_config = parent_config
        self.child_config = child_config
        self.inheritance_error = inheritance_error
        
        if parent_config:
            self.details["parent_config"] = parent_config
        if child_config:
            self.details["child_config"] = child_config
        if inheritance_error:
            self.details["inheritance_error"] = inheritance_error