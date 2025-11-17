"""Fallback系统模块

提供统一的降级处理功能。
"""

from .fallback_manager import FallbackManager
from .fallback_engine import FallbackEngine
from .fallback_tracker import FallbackTracker
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession
from .interfaces import IFallbackStrategy, IClientFactory, IFallbackLogger

__all__ = [
    "FallbackManager",
    "FallbackEngine", 
    "FallbackTracker",
    "FallbackConfig",
    "FallbackAttempt",
    "FallbackSession",
    "IFallbackStrategy",
    "IClientFactory",
    "IFallbackLogger"
]