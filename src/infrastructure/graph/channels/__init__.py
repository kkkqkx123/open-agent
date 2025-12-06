"""基础设施层通道系统

提供LangGraph兼容的通道实现，支持不同类型的数据传递和聚合。
"""

from .base import BaseChannel
from .last_value import LastValue, LastValueAfterFinish
from .topic import Topic
from .binop import BinaryOperatorAggregate

__all__ = [
    "BaseChannel",
    "LastValue",
    "LastValueAfterFinish", 
    "Topic",
    "BinaryOperatorAggregate",
]