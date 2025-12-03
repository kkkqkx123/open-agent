"""基础设施层消息系统

提供消息系统的具体实现，替代 langchain_core.messages 依赖。
"""

from .base import BaseMessage
from .types import HumanMessage, AIMessage, SystemMessage, ToolMessage
from .converters import MessageConverter
from .factory import MessageFactory
from .utils import MessageUtils

__all__ = [
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "MessageConverter",
    "MessageFactory",
    "MessageUtils"
]