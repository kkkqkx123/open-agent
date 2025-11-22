"""
提示词相关异常定义
"""

from typing import Dict, Any, Optional

from .core import CoreError


class PromptError(CoreError):
    """提示词基础异常
    
    所有提示词相关异常的基类。
    """
    
    def __init__(self, message: str = "") -> None:
        """初始化提示词异常
        
        Args:
            message: 错误消息
        """
        super().__init__(message)
        self.message = message
        self.error_code = "PROMPT_ERROR"
        self.details: Dict[str, Any] = {}


class PromptRegistryError(PromptError):
    """提示词注册表异常
    
    当提示词注册表操作失败时抛出。
    """
    pass


class PromptLoadError(PromptError):
    """提示词加载异常
    
    当提示词加载失败时抛出。
    """
    
    def __init__(self, message: str, prompt_path: Optional[str] = None) -> None:
        """初始化加载异常
        
        Args:
            message: 错误消息
            prompt_path: 提示词路径
        """
        super().__init__(message)
        self.message = message
        self.prompt_path = prompt_path
        self.error_code = "PROMPT_LOAD_ERROR"
        self.details: Dict[str, Any] = {}
        if prompt_path:
            self.details["prompt_path"] = prompt_path


class PromptInjectionError(PromptError):
    """提示词注入异常
    
    当提示词注入失败时抛出。
    """
    
    def __init__(self, message: str) -> None:
        """初始化注入异常
        
        Args:
            message: 错误消息
        """
        super().__init__(message)
        self.message = message
        self.error_code = "PROMPT_INJECTION_ERROR"
        self.details: Dict[str, Any] = {}


class PromptConfigurationError(PromptError):
    """提示词配置异常
    
    当提示词配置错误时抛出。
    """
    pass


class PromptNotFoundError(PromptError):
    """提示词不存在异常
    
    当请求的提示词不存在时抛出。
    """
    pass


class PromptValidationError(PromptError):
    """提示词验证异常
    
    当提示词验证失败时抛出。
    """
    
    def __init__(self, message: str, validation_errors: Optional[list[str]] = None) -> None:
        """初始化验证异常
        
        Args:
            message: 错误消息
            validation_errors: 验证错误列表
        """
        super().__init__(message)
        self.message = message
        self.validation_errors = validation_errors or []
        self.error_code = "PROMPT_VALIDATION_ERROR"
        self.details: Dict[str, Any] = {"validation_errors": self.validation_errors}


class PromptCacheError(PromptError):
    """提示词缓存异常
    
    当提示词缓存操作失败时抛出。
    """
    
    def __init__(self, message: str, cache_key: Optional[str] = None) -> None:
        """初始化缓存异常
        
        Args:
            message: 错误消息
            cache_key: 缓存键
        """
        super().__init__(message)
        self.message = message
        self.cache_key = cache_key
        self.error_code = "PROMPT_CACHE_ERROR"
        self.details: Dict[str, Any] = {}
        if cache_key:
            self.details["cache_key"] = cache_key
