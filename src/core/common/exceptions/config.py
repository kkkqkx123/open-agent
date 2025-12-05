"""配置相关异常定义"""

from typing import Optional, Dict, Any


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
    pass


class ConfigurationLoadError(ConfigError):
    """配置加载异常"""
    pass


class ConfigurationEnvironmentError(ConfigError):
    """配置环境变量异常"""
    pass


__all__ = [
    "ConfigError",
    "ConfigurationValidationError",
    "ConfigurationLoadError",
    "ConfigurationEnvironmentError",
]
