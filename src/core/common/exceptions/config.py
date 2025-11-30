"""
配置系统异常定义
"""

from typing import Optional, Any


class ConfigError(Exception):
    """配置系统基础异常"""
    
    def __init__(self, message: str, config_path: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.config_path = config_path
        self.details = details


class ConfigNotFoundError(ConfigError):
    """配置未找到异常"""
    
    def __init__(self, config_path: str):
        super().__init__(f"配置未找到: {config_path}", config_path)


class ConfigValidationError(ConfigError):
    """配置验证异常"""
    
    def __init__(self, message: str, config_path: Optional[str] = None, field: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message, config_path, details)
        self.field = field


class ConfigInheritanceError(ConfigError):
    """配置继承异常"""
    
    def __init__(self, message: str, config_path: Optional[str] = None, parent_path: Optional[str] = None):
        super().__init__(message, config_path)
        self.parent_path = parent_path


class ConfigFormatError(ConfigError):
    """配置格式异常"""
    
    def __init__(self, message: str, config_path: Optional[str] = None):
        super().__init__(message, config_path)


class ConfigEnvironmentError(ConfigError):
    """环境变量解析异常"""
    
    def __init__(self, message: str, config_path: Optional[str] = None, env_var: Optional[str] = None):
        super().__init__(message, config_path)
        self.env_var = env_var