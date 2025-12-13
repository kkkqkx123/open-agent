"""基础设施层图错误定义

提供图执行过程中使用的错误类型、错误代码和错误消息创建函数。
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Any

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
    "GraphErrorCode",
    "create_error_message",
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


class GraphErrorCode(Enum):
    """图错误代码枚举"""
    
    # 图配置错误
    INVALID_GRAPH_CONFIGURATION = "INVALID_GRAPH_CONFIGURATION"
    INVALID_NODE_CONFIGURATION = "INVALID_NODE_CONFIGURATION"
    INVALID_EDGE_CONFIGURATION = "INVALID_EDGE_CONFIGURATION"
    
    # 图执行错误
    GRAPH_EXECUTION_ERROR = "GRAPH_EXECUTION_ERROR"
    NODE_EXECUTION_ERROR = "NODE_EXECUTION_ERROR"
    EDGE_EXECUTION_ERROR = "EDGE_EXECUTION_ERROR"
    
    # 通道错误
    INVALID_CONCURRENT_GRAPH_UPDATE = "INVALID_CONCURRENT_GRAPH_UPDATE"
    CHANNEL_UPDATE_ERROR = "CHANNEL_UPDATE_ERROR"
    CHANNEL_ACCESS_ERROR = "CHANNEL_ACCESS_ERROR"
    
    # 检查点错误
    CHECKPOINT_ERROR = "CHECKPOINT_ERROR"
    CHECKPOINT_NOT_FOUND = "CHECKPOINT_NOT_FOUND"
    CHECKPOINT_RESTORE_ERROR = "CHECKPOINT_RESTORE_ERROR"
    
    # 状态错误
    STATE_TRANSITION_ERROR = "STATE_TRANSITION_ERROR"
    STATE_VALIDATION_ERROR = "STATE_VALIDATION_ERROR"
    STATE_CONFLICT_ERROR = "STATE_CONFLICT_ERROR"
    
    # 资源错误
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    
    # 并发错误
    CONCURRENCY_ERROR = "CONCURRENCY_ERROR"
    DEADLOCK_DETECTED = "DEADLOCK_DETECTED"
    RACE_CONDITION = "RACE_CONDITION"


def create_error_message(message: str, error_code: GraphErrorCode | str, **kwargs: Any) -> str:
    """创建格式化的错误消息
    
    Args:
        message: 错误消息
        error_code: 错误代码
        **kwargs: 其他参数
        
    Returns:
        格式化的错误消息
    """
    if isinstance(error_code, GraphErrorCode):
        error_code_str = error_code.value
    else:
        error_code_str = str(error_code)
    
    # 构建详细的消息
    details = []
    for key, value in kwargs.items():
        if value is not None:
            details.append(f"{key}: {value}")
    
    if details:
        return f"[{error_code_str}] {message} ({', '.join(details)})"
    else:
        return f"[{error_code_str}] {message}"