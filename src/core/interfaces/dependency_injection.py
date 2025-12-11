"""Core层依赖注入接口定义

提供Core层组件获取依赖的简化接口，避免直接依赖Service层。
"""

from typing import Any, Optional, Callable

from src.interfaces.logger import ILogger


# 全局函数实例，用于提供日志服务
_global_logger_provider: Optional[Callable[[Optional[str]], ILogger]] = None
_global_token_calculator: Optional[Callable[[Any, str, str], int]] = None


def set_logger_provider(provider: Callable[[Optional[str]], ILogger]) -> None:
    """设置全局日志提供者
    
    Args:
        provider: 日志提供者函数
    """
    global _global_logger_provider
    _global_logger_provider = provider


def set_token_calculator(calculator: Callable[[Any, str, str], int]) -> None:
    """设置全局Token计算器
    
    Args:
        calculator: Token计算器函数
    """
    global _global_token_calculator
    _global_token_calculator = calculator


def get_logger(name: Optional[str] = None) -> ILogger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        ILogger: 日志记录器实例
    """
    if _global_logger_provider:
        return _global_logger_provider(name)
    
    # 回退实现
    from .fallback_logger import FallbackLogger
    return FallbackLogger(name)


def calculate_messages_tokens(messages: Any, model_type: str, model_name: str) -> int:
    """计算消息列表的Token数量
    
    Args:
        messages: 消息列表
        model_type: 模型类型
        model_name: 模型名称
        
    Returns:
        int: Token数量
    """
    if _global_token_calculator:
        return _global_token_calculator(messages, model_type, model_name)
    
    # 回退实现：简单估算
    if not messages:
        return 0
    
    total_chars = 0
    for message in messages:
        if hasattr(message, 'content') and message.content:
            total_chars += len(str(message.content))
    
    return max(1, total_chars // 4)


def clear_providers() -> None:
    """清除所有提供者"""
    global _global_logger_provider, _global_token_calculator
    _global_logger_provider = None
    _global_token_calculator = None


__all__ = [
    "set_logger_provider",
    "set_token_calculator",
    "get_logger",
    "calculate_messages_tokens",
    "clear_providers",
]