"""基础设施层图错误定义

提供错误类型定义。
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Any
from warnings import warn

from typing_extensions import deprecated

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Command, Interrupt

__all__ = (
    "EmptyChannelError",
    "ErrorCode",
    "GraphRecursionError",
    "InvalidUpdateError",
    "GraphBubbleUp",
    "GraphInterrupt",
    "NodeInterrupt",
    "ParentCommand",
    "EmptyInputError",
    "TaskNotFound",
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


class ErrorCode(Enum):
    GRAPH_RECURSION_LIMIT = "GRAPH_RECURSION_LIMIT"
    INVALID_CONCURRENT_GRAPH_UPDATE = "INVALID_CONCURRENT_GRAPH_UPDATE"
    INVALID_GRAPH_NODE_RETURN_VALUE = "INVALID_GRAPH_NODE_RETURN_VALUE"
    MULTIPLE_SUBGRAPHS = "MULTIPLE_SUBGRAPHS"
    INVALID_CHAT_HISTORY = "INVALID_CHAT_HISTORY"


def create_error_message(*, message: str, error_code: ErrorCode) -> str:
    return (
        f"{message}\n"
        "For troubleshooting, visit: https://python.langchain.com/docs/"
        f"troubleshooting/errors/{error_code.value}"
    )


class GraphRecursionError(RecursionError):
    """当图已耗尽最大步数时引发。

    这可以防止无限循环。要增加最大步数，
    使用指定更高`recursion_limit`的配置运行图。

    故障排除指南：

    - [`GRAPH_RECURSION_LIMIT`](https://docs.langchain.com/oss/python/langgraph/GRAPH_RECURSION_LIMIT)

    示例：

        graph = builder.compile()
        graph.invoke(
            {"messages": [("user", "Hello, world!")]},
            # 配置是第二个位置参数
            {"recursion_limit": 1000},
        )
    """

    pass


class InvalidUpdateError(Exception):
    """当尝试使用无效的更新集更新通道时引发。

    故障排除指南：

    - [`INVALID_CONCURRENT_GRAPH_UPDATE`](https://docs.langchain.com/oss/python/langgraph/INVALID_CONCURRENT_GRAPH_UPDATE)
    - [`INVALID_GRAPH_NODE_RETURN_VALUE`](https://docs.langchain.com/oss/python/langgraph/INVALID_GRAPH_NODE_RETURN_VALUE)
    """

    pass


class GraphBubbleUp(Exception):
    pass


class GraphInterrupt(GraphBubbleUp):
    """当子图被中断时引发，被根图抑制。
    从不直接引发或显示给用户。"""

    def __init__(self, interrupts: Sequence[Interrupt] = ()) -> None:
        super().__init__(interrupts)


@deprecated(
    "NodeInterrupt is deprecated. Please use [`interrupt`][langgraph.types.interrupt] instead.",
    category=None,
)
class NodeInterrupt(GraphInterrupt):
    """由节点引发以中断执行。"""

    def __init__(self, value: Any, id: str | None = None) -> None:
        warn(
            "NodeInterrupt is deprecated. Please use `interrupt` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if id is None:
            super().__init__([Interrupt(value=value)])
        else:
            super().__init__([Interrupt(value=value, id=id)])


class ParentCommand(GraphBubbleUp):
    args: tuple["Command"]

    def __init__(self, command: "Command") -> None:
        super().__init__(command)


class EmptyInputError(Exception):
    """当图接收到空输入时引发。"""

    pass


class TaskNotFound(Exception):
    """当执行器无法找到任务时引发（用于分布式模式）。"""

    pass


class EmptyChannelError(Exception):
    """当尝试获取尚未首次更新的通道的值时引发。"""

    pass


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