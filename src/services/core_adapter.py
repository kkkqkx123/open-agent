"""Core层适配器

提供Service层到Core层的依赖注入适配器实现。
"""

from typing import Any, Optional

from src.interfaces.logger import ILogger
from .logger.injection import get_logger as get_service_logger
from .history.injection import get_token_calculation_service


def initialize_core_dependencies() -> None:
    """初始化Core层依赖
    
    将Service层的依赖设置到Core层。
    """
    from src.core.interfaces import set_logger_provider, set_token_calculator
    
    # 设置日志提供者
    def logger_provider(name: Optional[str] = None) -> ILogger:
        return get_service_logger(name)
    
    set_logger_provider(logger_provider)
    
    # 设置Token计算器
    def token_calculator(messages: Any, model_type: str, model_name: str) -> int:
        try:
            token_service = get_token_calculation_service()
            return token_service.calculate_messages_tokens(
                messages,
                model_type,
                model_name
            )
        except Exception:
            # 如果服务不可用，返回估算值
            if not messages:
                return 0
            
            total_chars = 0
            for message in messages:
                if hasattr(message, 'content') and message.content:
                    total_chars += len(str(message.content))
            
            return max(1, total_chars // 4)
    
    set_token_calculator(token_calculator)


def clear_core_dependencies() -> None:
    """清除Core层依赖"""
    from src.core.interfaces import clear_providers
    
    clear_providers()


__all__ = [
    "initialize_core_dependencies",
    "clear_core_dependencies",
]