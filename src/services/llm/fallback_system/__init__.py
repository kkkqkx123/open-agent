"""Fallback系统模块

提供统一的降级处理功能。

注意：此模块已迁移到基础设施层，这里保留是为了向后兼容。
建议直接使用 src.infrastructure.llm.fallback 模块。
"""

from .fallback_manager import FallbackManager
# 从基础设施层导入降级配置和组件
from src.infrastructure.llm.fallback import FallbackConfig, FallbackAttempt, FallbackSession, FallbackEngine, FallbackTracker
from .fallback_factory import create_fallback_manager
from src.interfaces.llm import IFallbackStrategy, IClientFactory, IFallbackLogger

__all__ = [
    "FallbackManager",
    "FallbackEngine", 
    "FallbackTracker",
    "FallbackConfig",
    "FallbackAttempt",
    "FallbackSession",
    "create_fallback_manager",
    "IFallbackStrategy",
    "IClientFactory",
    "IFallbackLogger"
]