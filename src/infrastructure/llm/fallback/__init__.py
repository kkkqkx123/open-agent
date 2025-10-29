"""LLM降级模块"""

from .fallback_manager import FallbackManager, DefaultFallbackLogger
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession
from .interfaces import IFallbackStrategy, IClientFactory, IFallbackLogger
from .strategies import (
    SequentialFallbackStrategy,
    PriorityFallbackStrategy,
    RandomFallbackStrategy,
    ErrorTypeBasedStrategy,
    create_fallback_strategy
)

__all__ = [
    "FallbackManager",
    "DefaultFallbackLogger",
    "FallbackConfig",
    "FallbackAttempt",
    "FallbackSession",
    "IFallbackStrategy",
    "IClientFactory",
    "IFallbackLogger",
    "SequentialFallbackStrategy",
    "PriorityFallbackStrategy",
    "RandomFallbackStrategy",
    "ErrorTypeBasedStrategy",
    "create_fallback_strategy"
]