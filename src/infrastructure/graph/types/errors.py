"""基础设施层图错误定义

提供图执行过程中使用的错误类型。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from warnings import warn

from typing_extensions import deprecated

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Command, Interrupt

__all__ = (
    "EmptyChannelError",
    "GraphRecursionError",
    "InvalidUpdateError",
    "GraphBubbleUp",
    "GraphInterrupt",
    "InvalidGraphError",
    "NodeNotFoundError",
    "GraphValueError",
    "GraphTypeError",
    "EdgeNotFoundError",
    "CheckpointNotFoundError",
    "CheckpointError",
    "DeliveryFailedError",
    "InvalidConfigurationError",
)


class GraphBubbleUp(Exception):
    """图冒泡异常基类。"""
    pass


class GraphRecursionError(RecursionError):
    """当图已耗尽最大步数时引发。

    这可以防止无限循环。
    """
    pass


class InvalidUpdateError(Exception):
    """当尝试使用无效的更新集更新通道时引发。"""
    pass


class GraphInterrupt(GraphBubbleUp):
    """当子图被中断时引发，被根图抑制。"""

    def __init__(self, interrupts: Sequence[Interrupt] = ()) -> None:
        super().__init__(interrupts)


class InvalidGraphError(Exception):
    """当图配置无效时引发。"""
    pass


class NodeNotFoundError(Exception):
    """当找不到指定的节点时引发。"""
    pass


class GraphValueError(Exception):
    """当图值无效时引发。"""
    pass


class GraphTypeError(Exception):
    """当图类型无效时引发。"""
    pass


class EdgeNotFoundError(Exception):
    """当找不到指定的边时引发。"""
    pass


class CheckpointNotFoundError(Exception):
    """当找不到指定的检查点时引发。"""
    pass


class CheckpointError(Exception):
    """检查点相关错误。"""
    pass


class DeliveryFailedError(Exception):
    """消息传递失败错误。"""
    pass


class InvalidConfigurationError(Exception):
    """配置无效错误。"""
    pass


class EmptyChannelError(Exception):
    """当尝试获取尚未首次更新的通道的值时引发。"""
    pass