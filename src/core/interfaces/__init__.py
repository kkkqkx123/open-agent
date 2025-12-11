"""Core层接口模块

提供Core层组件所需的接口定义，避免直接依赖Service层。
"""

from .dependency_injection import (
    set_logger_provider,
    set_token_calculator,
    get_logger,
    calculate_messages_tokens,
    clear_providers,
)
from .fallback_logger import FallbackLogger

__all__ = [
    "set_logger_provider",
    "set_token_calculator",
    "get_logger",
    "calculate_messages_tokens",
    "clear_providers",
    "FallbackLogger",
]