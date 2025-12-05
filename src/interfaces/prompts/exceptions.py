"""
提示词相关异常定义
"""

from typing import Dict, Any, Optional, List


class PromptError(Exception):
    """提示词基础异常
    
    所有提示词相关异常的基类。
    """
    
    def __init__(
        self, 
        message: str = "",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化提示词异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "PROMPT_ERROR"
        self.details = details or {}


class PromptRegistryError(PromptError):
    """提示词注册表异常
    
    当提示词注册表操作失败时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        registry_operation: Optional[str] = None,
        prompt_name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_REGISTRY_ERROR", kwargs)
        self.registry_operation = registry_operation
        self.prompt_name = prompt_name
        
        if registry_operation:
            self.details["registry_operation"] = registry_operation
        if prompt_name:
            self.details["prompt_name"] = prompt_name


class PromptLoadError(PromptError):
    """提示词加载异常
    
    当提示词加载失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        prompt_path: Optional[str] = None,
        load_format: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化加载异常
        
        Args:
            message: 错误消息
            prompt_path: 提示词路径
            load_format: 加载格式
            **kwargs: 其他参数
        """
        super().__init__(message, "PROMPT_LOAD_ERROR", kwargs)
        self.prompt_path = prompt_path
        self.load_format = load_format
        
        if prompt_path:
            self.details["prompt_path"] = prompt_path
        if load_format:
            self.details["load_format"] = load_format


class PromptInjectionError(PromptError):
    """提示词注入异常
    
    当提示词注入失败时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        injection_type: Optional[str] = None,
        target_template: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化注入异常
        
        Args:
            message: 错误消息
            injection_type: 注入类型
            target_template: 目标模板
            **kwargs: 其他参数
        """
        super().__init__(message, "PROMPT_INJECTION_ERROR", kwargs)
        self.injection_type = injection_type
        self.target_template = target_template
        
        if injection_type:
            self.details["injection_type"] = injection_type
        if target_template:
            self.details["target_template"] = target_template


class PromptConfigurationError(PromptError):
    """提示词配置异常
    
    当提示词配置错误时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_CONFIGURATION_ERROR", kwargs)
        self.config_key = config_key
        self.config_value = config_value
        
        if config_key:
            self.details["config_key"] = config_key
        if config_value is not None:
            self.details["config_value"] = config_value


class PromptNotFoundError(PromptError):
    """提示词不存在异常
    
    当请求的提示词不存在时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        search_path: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_NOT_FOUND_ERROR", kwargs)
        self.prompt_name = prompt_name
        self.prompt_id = prompt_id
        self.search_path = search_path or []
        
        if prompt_name:
            self.details["prompt_name"] = prompt_name
        if prompt_id:
            self.details["prompt_id"] = prompt_id
        if search_path:
            self.details["search_path"] = search_path


class PromptValidationError(PromptError):
    """提示词验证异常
    
    当提示词验证失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        validation_errors: Optional[List[str]] = None,
        validation_rule: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化验证异常
        
        Args:
            message: 错误消息
            validation_errors: 验证错误列表
            validation_rule: 验证规则
            **kwargs: 其他参数
        """
        super().__init__(message, "PROMPT_VALIDATION_ERROR", kwargs)
        self.validation_errors = validation_errors or []
        self.validation_rule = validation_rule
        
        if validation_errors:
            self.details["validation_errors"] = validation_errors
        if validation_rule:
            self.details["validation_rule"] = validation_rule


class PromptCacheError(PromptError):
    """提示词缓存异常
    
    当提示词缓存操作失败时抛出。
    """
    
    def __init__(
        self, 
        message: str, 
        cache_key: Optional[str] = None,
        cache_operation: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化缓存异常
        
        Args:
            message: 错误消息
            cache_key: 缓存键
            cache_operation: 缓存操作
            **kwargs: 其他参数
        """
        super().__init__(message, "PROMPT_CACHE_ERROR", kwargs)
        self.cache_key = cache_key
        self.cache_operation = cache_operation
        
        if cache_key:
            self.details["cache_key"] = cache_key
        if cache_operation:
            self.details["cache_operation"] = cache_operation


class PromptTypeNotFoundError(PromptError):
    """提示词类型不存在异常
    
    当请求的提示词类型不存在时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        type_name: Optional[str] = None,
        available_types: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_TYPE_NOT_FOUND_ERROR", kwargs)
        self.type_name = type_name
        self.available_types = available_types or []
        
        if type_name:
            self.details["type_name"] = type_name
        if available_types:
            self.details["available_types"] = available_types


class PromptTypeRegistrationError(PromptError):
    """提示词类型注册异常
    
    当提示词类型注册失败时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        type_name: Optional[str] = None,
        registration_error: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_TYPE_REGISTRATION_ERROR", kwargs)
        self.type_name = type_name
        self.registration_error = registration_error
        
        if type_name:
            self.details["type_name"] = type_name
        if registration_error:
            self.details["registration_error"] = registration_error


class PromptReferenceError(PromptError):
    """提示词引用异常
    
    当提示词引用解析失败时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        reference_path: Optional[str] = None,
        source_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_REFERENCE_ERROR", kwargs)
        self.reference_path = reference_path
        self.source_prompt = source_prompt
        
        if reference_path:
            self.details["reference_path"] = reference_path
        if source_prompt:
            self.details["source_prompt"] = source_prompt


class PromptCircularReferenceError(PromptError):
    """提示词循环引用异常
    
    当检测到提示词循环引用时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        circular_path: Optional[List[str]] = None,
        start_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_CIRCULAR_REFERENCE_ERROR", kwargs)
        self.circular_path = circular_path or []
        self.start_prompt = start_prompt
        
        if circular_path:
            self.details["circular_path"] = circular_path
        if start_prompt:
            self.details["start_prompt"] = start_prompt


class PromptTemplateError(PromptError):
    """提示词模板异常
    
    当提示词模板处理失败时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        template_name: Optional[str] = None,
        template_error: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_TEMPLATE_ERROR", kwargs)
        self.template_name = template_name
        self.template_error = template_error
        
        if template_name:
            self.details["template_name"] = template_name
        if template_error:
            self.details["template_error"] = template_error


class PromptRenderingError(PromptError):
    """提示词渲染异常
    
    当提示词渲染失败时抛出。
    """
    
    def __init__(
        self, 
        message: str,
        rendering_engine: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, "PROMPT_RENDERING_ERROR", kwargs)
        self.rendering_engine = rendering_engine
        self.template_variables = template_variables or {}
        
        if rendering_engine:
            self.details["rendering_engine"] = rendering_engine
        if template_variables:
            self.details["template_variables"] = template_variables


# 导出所有异常
__all__ = [
    "PromptError",
    "PromptRegistryError",
    "PromptLoadError",
    "PromptInjectionError",
    "PromptConfigurationError",
    "PromptNotFoundError",
    "PromptValidationError",
    "PromptCacheError",
    "PromptTypeNotFoundError",
    "PromptTypeRegistrationError",
    "PromptReferenceError",
    "PromptCircularReferenceError",
    "PromptTemplateError",
    "PromptRenderingError",
]