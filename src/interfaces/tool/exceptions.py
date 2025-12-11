"""
工具相关异常定义
"""

from typing import Optional, Dict, Any


class ToolError(Exception):
    """工具错误异常"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ToolRegistrationError(ToolError):
    """工具注册错误异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        tool_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_REGISTRATION_ERROR", kwargs)
        self.tool_name = tool_name
        self.tool_type = tool_type
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if tool_type:
            self.details["tool_type"] = tool_type


class ToolExecutionError(ToolError):
    """工具执行错误异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        execution_context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_EXECUTION_ERROR", kwargs)
        self.tool_name = tool_name
        self.execution_context = execution_context or {}
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if execution_context:
            self.details["execution_context"] = execution_context


class ToolValidationError(ToolError):
    """工具验证错误异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        validation_errors: Optional[list] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_VALIDATION_ERROR", kwargs)
        self.tool_name = tool_name
        self.validation_errors = validation_errors or []
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if validation_errors:
            self.details["validation_errors"] = validation_errors


class ToolNotFoundError(ToolError):
    """工具未找到异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        tool_id: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_NOT_FOUND_ERROR", kwargs)
        self.tool_name = tool_name
        self.tool_id = tool_id
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if tool_id:
            self.details["tool_id"] = tool_id


class ToolConfigurationError(ToolError):
    """工具配置错误异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_CONFIGURATION_ERROR", kwargs)
        self.tool_name = tool_name
        self.config_key = config_key
        self.config_value = config_value
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if config_key:
            self.details["config_key"] = config_key
        if config_value is not None:
            self.details["config_value"] = config_value


class ToolTimeoutError(ToolError):
    """工具执行超时异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_TIMEOUT_ERROR", kwargs)
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class ToolPermissionError(ToolError):
    """工具权限错误异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        required_permission: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_PERMISSION_ERROR", kwargs)
        self.tool_name = tool_name
        self.required_permission = required_permission
        self.user_id = user_id
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if required_permission:
            self.details["required_permission"] = required_permission
        if user_id:
            self.details["user_id"] = user_id


class ToolDependencyError(ToolError):
    """工具依赖错误异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        dependency_name: Optional[str] = None,
        dependency_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_DEPENDENCY_ERROR", kwargs)
        self.tool_name = tool_name
        self.dependency_name = dependency_name
        self.dependency_type = dependency_type
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if dependency_name:
            self.details["dependency_name"] = dependency_name
        if dependency_type:
            self.details["dependency_type"] = dependency_type


class ToolResourceError(ToolError):
    """工具资源错误异常"""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "TOOL_RESOURCE_ERROR", kwargs)
        self.tool_name = tool_name
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if tool_name:
            self.details["tool_name"] = tool_name
        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id:
            self.details["resource_id"] = resource_id


class ValidationReporterError(ToolError):
    """验证报告器错误异常"""
    
    def __init__(
        self,
        message: str,
        reporter_format: Optional[str] = None,
        reporter_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "VALIDATION_REPORTER_ERROR", kwargs)
        self.reporter_format = reporter_format
        self.reporter_type = reporter_type
        
        if reporter_format:
            self.details["reporter_format"] = reporter_format
        if reporter_type:
            self.details["reporter_type"] = reporter_type


# 导出所有异常
__all__ = [
    "ToolError",
    "ToolRegistrationError",
    "ToolExecutionError",
    "ToolValidationError",
    "ToolNotFoundError",
    "ToolConfigurationError",
    "ToolTimeoutError",
    "ToolPermissionError",
    "ToolDependencyError",
    "ToolResourceError",
    "ValidationReporterError",
]