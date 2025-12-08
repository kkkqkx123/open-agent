"""
消息转换器模块

提供 LLM 消息格式的转换功能。
"""

from .message import (
    MessageConverter,
    LLMMessage,
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage
)
from .base import (
    IProvider,
    IConverter,
    ConversionContext,
    MessageRole
)
from .providers import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    OpenAIResponsesProvider
)

__all__ = [
    # 主要接口
    "MessageConverter",
    
    # 消息类
    "LLMMessage",
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    
    # 基础接口和类
    "IProvider",
    "IConverter",
    "ConversionContext",
    "MessageRole",
    
    # 提供商实现
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "OpenAIResponsesProvider"
]