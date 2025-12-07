"""图引擎工具函数

提供图执行过程中使用的工具函数。
"""

from typing import Any

from .data_structures import Interrupt
from .errors import GraphInterrupt


def interrupt(value: Any) -> Any:
    """从节点内部中断图，带有可恢复的异常。

    interrupt函数通过暂停图执行并向客户端显示值来启用人在环工作流。
    此值可以传达上下文或请求恢复执行所需的输入。

    在给定节点中，此函数的第一次调用引发GraphInterrupt异常，停止执行。
    提供的值包含在异常中并发送给执行图的客户端。

    恢复图的客户端必须使用`Command`原语
    指定中断的值并继续执行。
    图从节点的开始恢复，**重新执行**所有逻辑。

    如果节点包含多个interrupt调用，图引擎根据节点中的顺序将恢复值与中断匹配。
    此恢复值列表特定于执行节点的任务，不在任务间共享。

    要使用中断，必须启用检查点，因为该功能依赖于持久化图状态。

    Args:
        value: 图中断时向客户端显示的值。

    Returns:
        Any: 在同一节点（精确地说是同一任务）中的后续调用中，返回第一次调用期间提供的值

    Raises:
        GraphInterrupt: 在节点中的第一次调用时，停止执行并向客户端显示提供的值。
    """
    interrupt_obj = Interrupt(value=value)
    raise GraphInterrupt((interrupt_obj,))  # type: ignore[arg-type]


__all__ = [
    "interrupt",
]