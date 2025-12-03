"""LLM模块核心接口定义 - 兼容旧版导入"""

# 从base模块导入
from .base import LLMResponse, ILLMClient

# 从factory模块导入
from .factory import ILLMClientFactory, IClientFactory

# 从hooks模块导入
from .hooks import ILLMCallHook

# 从manager模块导入
from .manager import ILLMManager

# 从task_group模块导入
from .task_group import ITaskGroupManager

# 从fallback模块导入
from .fallback.base import IFallbackManager, IFallbackStrategy, IFallbackLogger

# 从retry模块导入
from .retry.base import IRetryStrategy, IRetryLogger

# 从polling模块导入
from .polling import IPollingPoolManager

# 从cache模块导入
from .cache import ICacheProvider, ICacheKeyGenerator

# 从token_config模块导入
from .token_config import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    TokenCalculationConfig,
    TokenCostInfo
)

# 从encoding模块导入
from .encoding import EncodingProtocol

# 从converters模块导入
from .converters import IProviderConverter

# 定义导出列表
__all__ = [
    'LLMResponse',
    'ILLMClient',
    'ILLMClientFactory',
    'IClientFactory',
    'ILLMCallHook',
    'ILLMManager',
    'ITaskGroupManager',
    'IFallbackManager',
    'IFallbackStrategy',
    'IFallbackLogger',
    'IRetryStrategy',
    'IRetryLogger',
    'IPollingPoolManager',
    'ICacheProvider',
    'ICacheKeyGenerator',
    # Token配置相关接口
    'ITokenConfigProvider',
    'ITokenCostCalculator',
    'TokenCalculationConfig',
    'TokenCostInfo',
    # 编码相关接口
    'EncodingProtocol',
    # 转换器相关接口
    'IProviderConverter',
]