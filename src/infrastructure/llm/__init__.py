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
from .hooks import LoggingHook, MetricsHook, RetryHook, CompositeHook
from .fallback_system import (
    FallbackManager,
    FallbackConfig,
    create_fallback_manager,
    SequentialFallbackStrategy,
    PriorityFallbackStrategy,
    RandomFallbackStrategy,
    ErrorTypeBasedStrategy,
    ParallelFallbackStrategy,
    ConditionalFallbackStrategy,
    ConditionalFallback,
    create_fallback_strategy,
)
from .pool.interfaces import IConnectionPool
from .pool.connection_pool import HTTPConnectionPool, connection_pool_manager
from .pool.factory import ConnectionPoolFactory
from .memory.memory_manager import MemoryManager, memory_manager_factory
from .plugins.interfaces import ILLMPlugin, IPluginManager
from .plugins.plugin_manager import PluginManager, plugin_manager_factory

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
    "RetryHook",
    "CompositeHook",
    # 降级
    "FallbackManager",
    "FallbackConfig",
    "create_fallback_manager",
    "SequentialFallbackStrategy",
    "PriorityFallbackStrategy",
    "RandomFallbackStrategy",
    "ErrorTypeBasedStrategy",
    "ParallelFallbackStrategy",
    "ConditionalFallbackStrategy",
    "ConditionalFallback",
    "create_fallback_strategy",
    # 连接池
    "IConnectionPool",
    "HTTPConnectionPool",
    "connection_pool_manager",
    "ConnectionPoolFactory",
    # 内存管理
    "MemoryManager",
    "memory_manager_factory",
    # 插件系统
    "ILLMPlugin",
    "IPluginManager",
    "PluginManager",
    "plugin_manager_factory",
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