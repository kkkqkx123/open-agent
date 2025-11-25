"""LLM重试模块"""

from typing import Optional
from .retry_manager import RetryManager, get_global_retry_manager, set_global_retry_manager, retry
from .retry_config import RetryConfig, RetryAttempt, RetrySession, RetryStats
from src.interfaces.llm import IRetryStrategy, IRetryLogger
from .strategies import (
    DefaultRetryLogger,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    FixedDelayStrategy,
    AdaptiveRetryStrategy,
    ConditionalRetryStrategy,
    create_retry_strategy,
    create_status_code_checker,
    create_error_type_checker
)


def create_retry_manager(config: RetryConfig, logger: Optional[IRetryLogger] = None) -> RetryManager:
    """
    创建重试管理器
    
    Args:
        config: 重试配置
        logger: 日志记录器
        
    Returns:
        重试管理器实例
    """
    return RetryManager(config, logger)


__all__ = [
    "RetryManager",
    "get_global_retry_manager",
    "set_global_retry_manager",
    "retry",
    "RetryConfig",
    "RetryAttempt",
    "RetrySession",
    "RetryStats",
    "IRetryStrategy",
    "IRetryLogger",
    "DefaultRetryLogger",
    "ExponentialBackoffStrategy",
    "LinearBackoffStrategy",
    "FixedDelayStrategy",
    "AdaptiveRetryStrategy",
    "ConditionalRetryStrategy",
    "create_retry_strategy",
    "create_status_code_checker",
    "create_error_type_checker",
    "create_retry_manager"
]