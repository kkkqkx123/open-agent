"""LLM模块异常定义"""

from typing import Optional, Dict, Any


class LLMError(Exception):
    """LLM模块基础异常"""

    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化LLM异常

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class LLMClientCreationError(LLMError):
    """LLM客户端创建错误"""

    def __init__(
        self, 
        message: str, 
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "LLM_CLIENT_CREATION_ERROR", kwargs)
        self.provider = provider
        self.model_name = model_name
        
        if provider:
            self.details["provider"] = provider
        if model_name:
            self.details["model_name"] = model_name


class UnsupportedModelTypeError(LLMError):
    """不支持的模型类型错误"""

    def __init__(
        self, 
        message: str, 
        model_type: Optional[str] = None,
        supported_types: Optional[list] = None,
        **kwargs: Any
    ):
        super().__init__(message, "UNSUPPORTED_MODEL_TYPE_ERROR", kwargs)
        self.model_type = model_type
        self.supported_types = supported_types or []
        
        if model_type:
            self.details["model_type"] = model_type
        if supported_types:
            self.details["supported_types"] = supported_types


class LLMCallError(LLMError):
    """LLM调用错误"""

    def __init__(
        self,
        message: str,
        error_type: str = "unknown",
        error_code: Optional[str] = None,
        is_retryable: bool = False,
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None,
        error_context: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
    ) -> None:
        """
        初始化LLM调用错误

        Args:
            message: 错误消息
            error_type: 错误类型
            error_code: 错误代码
            is_retryable: 是否可重试
            retry_after: 重试等待时间（秒）
            original_error: 原始错误
            error_context: 错误上下文
            model_name: 模型名称
        """
        super().__init__(message, error_code or "LLM_CALL_ERROR", error_context)
        self.error_type = error_type
        self.is_retryable = is_retryable
        self.retry_after = retry_after
        self.original_error = original_error
        self.error_context = error_context
        self.model_name = model_name

        if model_name:
            self.details["model_name"] = model_name
        if is_retryable:
            self.details["is_retryable"] = is_retryable
        if retry_after:
            self.details["retry_after"] = retry_after


class LLMTimeoutError(LLMCallError):
    """LLM调用超时错误"""

    def __init__(
        self, message: str = "LLM调用超时", timeout: Optional[int] = None, model_name: Optional[str] = None
    ) -> None:
        """
        初始化超时错误

        Args:
            message: 错误消息
            timeout: 超时时间（秒）
            model_name: 模型名称
        """
        super().__init__(message, "timeout", "LLM_TIMEOUT_ERROR", is_retryable=True, model_name=model_name)
        self.timeout = timeout
        
        if timeout:
            self.details["timeout"] = timeout


class LLMRateLimitError(LLMCallError):
    """LLM调用频率限制错误"""

    def __init__(
        self, message: str = "LLM调用频率限制", retry_after: Optional[int] = None, model_name: Optional[str] = None
    ) -> None:
        """
        初始化频率限制错误

        Args:
            message: 错误消息
            retry_after: 重试等待时间（秒）
            model_name: 模型名称
        """
        super().__init__(
            message, "rate_limit_exceeded", "LLM_RATE_LIMIT_ERROR", is_retryable=True, retry_after=retry_after, model_name=model_name
        )


class LLMAuthenticationError(LLMCallError):
    """LLM认证错误"""

    def __init__(self, message: str = "LLM认证失败", model_name: Optional[str] = None) -> None:
        """
        初始化认证错误

        Args:
            message: 错误消息
            model_name: 模型名称
        """
        super().__init__(message, "authentication_error", "LLM_AUTHENTICATION_ERROR", is_retryable=False, model_name=model_name)


class LLMModelNotFoundError(LLMCallError):
    """LLM模型未找到错误"""

    def __init__(self, model_name: str) -> None:
        """
        初始化模型未找到错误

        Args:
            model_name: 模型名称
        """
        message = f"模型未找到: {model_name}"
        super().__init__(message, "model_not_found", "LLM_MODEL_NOT_FOUND_ERROR", is_retryable=False, model_name=model_name)


class LLMTokenLimitError(LLMCallError):
    """LLM Token限制错误"""

    def __init__(
        self,
        message: str = "Token数量超过限制",
        token_count: Optional[int] = None,
        limit: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> None:
        """
        初始化Token限制错误

        Args:
            message: 错误消息
            token_count: 实际Token数量
            limit: Token限制
            model_name: 模型名称
        """
        super().__init__(message, "token_limit_exceeded", "LLM_TOKEN_LIMIT_ERROR", is_retryable=False, model_name=model_name)
        self.token_count = token_count
        self.limit = limit
        
        if token_count:
            self.details["token_count"] = token_count
        if limit:
            self.details["limit"] = limit


class LLMContentFilterError(LLMCallError):
    """LLM内容过滤错误"""

    def __init__(self, message: str = "内容被过滤", model_name: Optional[str] = None) -> None:
        """
        初始化内容过滤错误

        Args:
            message: 错误消息
            model_name: 模型名称
        """
        super().__init__(message, "content_filter", "LLM_CONTENT_FILTER_ERROR", is_retryable=False, model_name=model_name)


class LLMServiceUnavailableError(LLMCallError):
    """LLM服务不可用错误"""

    def __init__(self, message: str = "LLM服务不可用", model_name: Optional[str] = None) -> None:
        """
        初始化服务不可用错误

        Args:
            message: 错误消息
            model_name: 模型名称
        """
        super().__init__(message, "service_unavailable", "LLM_SERVICE_UNAVAILABLE_ERROR", is_retryable=True, model_name=model_name)


class LLMInvalidRequestError(LLMCallError):
    """LLM无效请求错误"""

    def __init__(self, message: str = "无效请求", model_name: Optional[str] = None) -> None:
        """
        初始化无效请求错误

        Args:
            message: 错误消息
            model_name: 模型名称
        """
        super().__init__(message, "invalid_request", "LLM_INVALID_REQUEST_ERROR", is_retryable=False, model_name=model_name)


class LLMConfigurationError(LLMError):
    """LLM配置错误"""

    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs: Any
    ):
        super().__init__(message, "LLM_CONFIGURATION_ERROR", kwargs)
        self.config_key = config_key
        self.config_value = config_value
        
        if config_key:
            self.details["config_key"] = config_key
        if config_value is not None:
            self.details["config_value"] = config_value


class LLMFallbackError(LLMError):
    """LLM降级错误"""

    def __init__(
        self, 
        message: str, 
        original_error: Optional[Exception] = None,
        fallback_model: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "LLM_FALLBACK_ERROR", kwargs)
        self.original_error = original_error
        self.fallback_model = fallback_model
        
        if fallback_model:
            self.details["fallback_model"] = fallback_model


# LLM Wrapper相关异常（整合自llm_wrapper.py）
class LLMWrapperError(LLMError):
    """LLM包装器错误基类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        wrapper_type: Optional[str] = None,
    ):
        super().__init__(message, error_code or "LLM_WRAPPER_ERROR", details)
        self.wrapper_type = wrapper_type

        if wrapper_type:
            self.details["wrapper_type"] = wrapper_type


class TaskGroupWrapperError(LLMWrapperError):
    """任务组包装器错误"""

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        group_id: Optional[str] = None,
        **kwargs: Any
    ):
        details = {"wrapper_type": "TaskGroup"}
        details.update(kwargs)
        if task_id:
            details["task_id"] = task_id
        if group_id:
            details["group_id"] = group_id
        super().__init__(message, "TASK_GROUP_WRAPPER_ERROR", details, "TaskGroup")
        self.task_id = task_id
        self.group_id = group_id


class PollingPoolWrapperError(LLMWrapperError):
    """轮询池包装器错误"""

    def __init__(
        self,
        message: str,
        pool_id: Optional[str] = None,
        **kwargs: Any
    ):
        details = {"wrapper_type": "PollingPool"}
        details.update(kwargs)
        if pool_id:
            details["pool_id"] = pool_id
        super().__init__(message, "POLLING_POOL_WRAPPER_ERROR", details, "PollingPool")
        self.pool_id = pool_id


class WrapperFactoryError(LLMWrapperError):
    """包装器工厂错误"""

    def __init__(
        self,
        message: str,
        factory_type: Optional[str] = None,
        **kwargs: Any
    ):
        details = {"wrapper_type": "Factory"}
        details.update(kwargs)
        if factory_type:
            details["factory_type"] = factory_type
        super().__init__(message, "WRAPPER_FACTORY_ERROR", details, "Factory")
        self.factory_type = factory_type


class WrapperConfigError(LLMWrapperError):
    """包装器配置错误"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs: Any
    ):
        details = {"wrapper_type": "Config"}
        details.update(kwargs)
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = config_value
        super().__init__(message, "WRAPPER_CONFIG_ERROR", details, "Config")
        self.config_key = config_key
        self.config_value = config_value


class WrapperExecutionError(LLMWrapperError):
    """包装器执行错误"""

    def __init__(
        self,
        message: str,
        execution_context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        # 初始化details字典，确保类型正确
        details: Dict[str, Any] = {"wrapper_type": "Execution"}
        details.update(kwargs)
        if execution_context:
            details["execution_context"] = execution_context
        super().__init__(message, "WRAPPER_EXECUTION_ERROR", details, "Execution")
        self.execution_context = execution_context or {}


# 导出所有异常
__all__ = [
    # 基础LLM异常
    "LLMError",
    "LLMClientCreationError",
    "UnsupportedModelTypeError",
    "LLMCallError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    "LLMModelNotFoundError",
    "LLMTokenLimitError",
    "LLMContentFilterError",
    "LLMServiceUnavailableError",
    "LLMInvalidRequestError",
    "LLMConfigurationError",
    "LLMFallbackError",
    # LLM Wrapper异常
    "LLMWrapperError",
    "TaskGroupWrapperError",
    "PollingPoolWrapperError",
    "WrapperFactoryError",
    "WrapperConfigError",
    "WrapperExecutionError",
]