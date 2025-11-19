"""LLM模块

提供LLM相关的核心功能：
- 消息模型定义 (LLMMessage, MessageRole)
- 消息转换器 (MessageConverter)
- LLM提供商接口和实现
"""

from .models import LLMMessage, MessageRole
from .message_converters import MessageConverter, get_message_converter

__all__ = [
    "LLMMessage",
    "MessageRole",
    "MessageConverter",
    "get_message_converter",
]
