"""LLM模块初始化文件"""

from .interfaces import ILLMClient, ILLMCallHook, ILLMClientFactory
from .models import LLMMessage, LLMResponse, TokenUsage, ModelInfo
from .config import LLMClientConfig, LLMModuleConfig
from .factory import LLMFactory, get_global_factory, create_client
from .header_validator import HeaderValidator, HeaderProcessor
from .fallback_client import FallbackClientWrapper
from .token_counter import (
    ITokenCounter,
    TokenCounterFactory,
    OpenAITokenCounter,
    GeminiTokenCounter,
    AnthropicTokenCounter,
    MockTokenCounter,
)
from .error_handler import (
    IErrorHandler,
    ErrorHandlerFactory,
    BaseErrorHandler,
    OpenAIErrorHandler,
    GeminiErrorHandler,
    AnthropicErrorHandler,
    ErrorContext,
)
from .exceptions import (
    LLMError,
    LLMClientCreationError,
    UnsupportedModelTypeError,
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
    LLMConfigurationError,
    LLMFallbackError,
)
from .hooks import LoggingHook, MetricsHook, FallbackHook, RetryHook, CompositeHook
from .fallback import (
    FallbackManager,
    FallbackStrategy,
    FallbackModel,
    ConditionalFallback,
)

__all__ = [
    # 接口
    "ILLMClient",
    "ILLMCallHook",
    "ILLMClientFactory",
    # 模型
    "LLMMessage",
    "LLMResponse",
    "LLMError",
    "TokenUsage",
    "ModelInfo",
    # 配置
    "LLMClientConfig",
    "LLMModuleConfig",
    # 工厂
    "LLMFactory",
    "get_global_factory",
    "create_client",
    # 标头验证
    "HeaderValidator",
    "HeaderProcessor",
    # 降级客户端
    "FallbackClientWrapper",
    # Token计算器
    "ITokenCounter",
    "TokenCounterFactory",
    "OpenAITokenCounter",
    "GeminiTokenCounter",
    "AnthropicTokenCounter",
    "MockTokenCounter",
    # 错误处理器
    "IErrorHandler",
    "ErrorHandlerFactory",
    "BaseErrorHandler",
    "OpenAIErrorHandler",
    "GeminiErrorHandler",
    "AnthropicErrorHandler",
    "ErrorContext",
    # 钩子
    "LoggingHook",
    "MetricsHook",
    "FallbackHook",
    "RetryHook",
    "CompositeHook",
    # 降级
    "FallbackManager",
    "FallbackStrategy",
    "FallbackModel",
    "ConditionalFallback",
    # 异常
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
]
