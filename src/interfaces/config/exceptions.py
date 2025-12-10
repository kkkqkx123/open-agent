"""配置异常定义"""

from typing import Dict, Any, Optional


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