"""
提示词相关错误类型定义

提供类型安全的错误处理机制
"""

from typing import Optional, Dict, Any, List


class PromptError(Exception):
    """提示词基础错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = self.__class__.__name__


class PromptLoadError(PromptError):
    """提示词加载错误"""
    
    def __init__(self, message: str, prompt_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.prompt_path = prompt_path


class PromptInjectionError(PromptError):
    """提示词注入错误"""
    
    def __init__(self, message: str, state_info: Optional[Dict[str, Any]] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.state_info = state_info or {}


class PromptValidationError(PromptError):
    """提示词验证错误"""
    
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.validation_errors = validation_errors or []


class PromptCacheError(PromptError):
    """提示词缓存错误"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.cache_key = cache_key


class PromptRegistryError(PromptError):
    """提示词注册表错误"""
    
    def __init__(self, message: str, prompt_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.prompt_name = prompt_name


class PromptReferenceError(PromptError):
    """提示词引用错误"""
    
    def __init__(self, message: str, reference: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.reference = reference


class PromptTypeError(PromptError):
    """提示词类型错误"""
    
    def __init__(self, message: str, prompt_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.prompt_type = prompt_type


def create_prompt_error(error_type: str, message: str, **kwargs) -> PromptError:
    """创建提示词错误"""
    error_classes = {
        "load": PromptLoadError,
        "injection": PromptInjectionError,
        "validation": PromptValidationError,
        "cache": PromptCacheError,
        "registry": PromptRegistryError,
        "reference": PromptReferenceError,
        "type": PromptTypeError
    }
    
    error_class = error_classes.get(error_type, PromptError)
    return error_class(message, **kwargs)


def is_prompt_error(error: Exception) -> bool:
    """检查是否是提示词错误"""
    return isinstance(error, PromptError)


def get_error_details(error: Exception) -> Dict[str, Any]:
    """获取错误详情"""
    if isinstance(error, PromptError):
        return {
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details
        }
    return {
        "error_code": type(error).__name__,
        "message": str(error),
        "details": {}
    }


def format_error_message(error: Exception) -> str:
    """格式化错误消息"""
    if isinstance(error, PromptError):
        details = ""
        if error.details:
            details = f" | 详情: {error.details}"
        return f"[{error.error_code}] {error.message}{details}"
    return f"[{type(error).__name__}] {str(error)}"


def should_retry_error(error: Exception) -> bool:
    """判断错误是否应该重试"""
    # 缓存错误通常可以重试
    if isinstance(error, PromptCacheError):
        return True
    
    # 加载错误可能可以重试（如网络问题）
    if isinstance(error, PromptLoadError):
        return True
    
    # 其他错误通常不应该重试
    return False