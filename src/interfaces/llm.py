"""LLM模块核心接口定义 - 旧版兼容接口文件

此文件是为了向后兼容而保留的，建议新代码使用 src.interfaces.llm 子模块。
"""

# 从新的子模块导入所有接口
from .llm.base import LLMResponse, ILLMClient
from .llm.factory import ILLMClientFactory, IClientFactory
from .llm.hooks import ILLMCallHook
from .llm.manager import ILLMManager
from .llm.task_group import ITaskGroupManager
from .llm.fallback.base import IFallbackManager, IFallbackStrategy, IFallbackLogger
from .llm.retry.base import IRetryStrategy, IRetryLogger
from .llm.polling import IPollingPoolManager

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
]