"""LLM模块异常定义"""

from typing import Optional, Dict, Any


class LLMError(Exception):
    """LLM模块基础异常"""

    pass


class LLMClientCreationError(LLMError):
    """LLM客户端创建错误"""

    pass


class UnsupportedModelTypeError(LLMError):
    """不支持的模型类型错误"""

    pass


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
        """
        super().__init__(message)
        self.error_type = error_type
        self.error_code = error_code
        self.is_retryable = is_retryable
        self.retry_after = retry_after
        self.original_error = original_error
        self.error_context = error_context


class LLMTimeoutError(LLMCallError):
    """LLM调用超时错误"""

    def __init__(
        self, message: str = "LLM调用超时", timeout: Optional[int] = None
    ) -> None:
        """
        初始化超时错误

        Args:
            message: 错误消息
            timeout: 超时时间（秒）
        """
        super().__init__(message, "timeout", is_retryable=True)
        self.timeout = timeout


class LLMRateLimitError(LLMCallError):
    """LLM调用频率限制错误"""

    def __init__(
        self, message: str = "LLM调用频率限制", retry_after: Optional[int] = None
    ) -> None:
        """
        初始化频率限制错误

        Args:
            message: 错误消息
            retry_after: 重试等待时间（秒）
        """
        super().__init__(
            message, "rate_limit_exceeded", is_retryable=True, retry_after=retry_after
        )


class LLMAuthenticationError(LLMCallError):
    """LLM认证错误"""

    def __init__(self, message: str = "LLM认证失败") -> None:
        """
        初始化认证错误

        Args:
            message: 错误消息
        """
        super().__init__(message, "authentication_error", is_retryable=False)


class LLMModelNotFoundError(LLMCallError):
    """LLM模型未找到错误"""

    def __init__(self, model_name: str) -> None:
        """
        初始化模型未找到错误

        Args:
            model_name: 模型名称
        """
        message = f"模型未找到: {model_name}"
        super().__init__(message, "model_not_found", is_retryable=False)
        self.model_name = model_name


class LLMTokenLimitError(LLMCallError):
    """LLM Token限制错误"""

    def __init__(
        self,
        message: str = "Token数量超过限制",
        token_count: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> None:
        """
        初始化Token限制错误

        Args:
            message: 错误消息
            token_count: 实际Token数量
            limit: Token限制
        """
        super().__init__(message, "token_limit_exceeded", is_retryable=False)
        self.token_count = token_count
        self.limit = limit


class LLMContentFilterError(LLMCallError):
    """LLM内容过滤错误"""

    def __init__(self, message: str = "内容被过滤") -> None:
        """
        初始化内容过滤错误

        Args:
            message: 错误消息
        """
        super().__init__(message, "content_filter", is_retryable=False)


class LLMServiceUnavailableError(LLMCallError):
    """LLM服务不可用错误"""

    def __init__(self, message: str = "LLM服务不可用") -> None:
        """
        初始化服务不可用错误

        Args:
            message: 错误消息
        """
        super().__init__(message, "service_unavailable", is_retryable=True)


class LLMInvalidRequestError(LLMCallError):
    """LLM无效请求错误"""

    def __init__(self, message: str = "无效请求") -> None:
        """
        初始化无效请求错误

        Args:
            message: 错误消息
        """
        super().__init__(message, "invalid_request", is_retryable=False)


class LLMConfigurationError(LLMError):
    """LLM配置错误"""

    pass


class LLMFallbackError(LLMError):
    """LLM降级错误"""

    def __init__(
        self, message: str, original_error: Optional[Exception] = None
    ) -> None:
        """
        初始化降级错误

        Args:
            message: 错误消息
            original_error: 原始错误
        """
        super().__init__(message)
        self.original_error = original_error