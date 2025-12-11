"""Core层适配器

提供Service层到Core层的依赖注入适配器实现。
"""

from typing import Any, Optional

from src.interfaces.logger import ILogger
from .logger.logger_service import create_logger_service
from .llm.token_calculation_service import TokenCalculationService


def initialize_core_dependencies() -> None:
    """初始化Core层依赖
    
    将Service层的依赖设置到Core层。
    """
    from src.interfaces import set_logger_provider, set_token_calculator
    
    # 设置日志提供者
    def logger_provider(name: Optional[str] = None) -> ILogger:
        # 创建简单的日志服务实例
        return create_logger_service(name or "default")
    
    set_logger_provider(logger_provider)
    
    # 设置Token计算器
    def token_calculator(messages: Any, model_type: str, model_name: str) -> int:
        try:
            # 创建Token计算服务实例
            token_service = TokenCalculationService()
            # TokenCalculationService使用calculate_messages_tokens方法
            if hasattr(token_service, 'calculate_messages_tokens'):
                # 如果是消息列表，使用calculate_messages_tokens方法
                if isinstance(messages, list):
                    return token_service.calculate_messages_tokens(messages, model_type, model_name)
                else:
                    # 单个消息或文本，使用calculate_tokens方法
                    return token_service.calculate_tokens(str(messages), model_type, model_name)
            else:
                # 如果没有相应方法，返回估算值
                if not messages:
                    return 0
                
                total_chars = 0
                if isinstance(messages, list):
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            total_chars += len(str(message.content))
                else:
                    total_chars = len(str(messages))
                
                return max(1, total_chars // 4)
        except Exception:
            # 如果服务不可用，返回估算值
            if not messages:
                return 0
            
            total_chars = 0
            if isinstance(messages, list):
                for message in messages:
                    if hasattr(message, 'content') and message.content:
                        total_chars += len(str(message.content))
            else:
                total_chars = len(str(messages))
            
            return max(1, total_chars // 4)
    
    set_token_calculator(token_calculator)


def clear_core_dependencies() -> None:
    """清除Core层依赖"""
    from src.interfaces.dependency_injection import clear_providers
    
    clear_providers()


__all__ = [
    "initialize_core_dependencies",
    "clear_core_dependencies",
]