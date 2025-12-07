"""图引擎核心数据结构定义

提供图执行过程中使用的核心数据结构。
"""

from __future__ import annotations

import uuid
from collections import deque
from collections.abc import Callable, Hashable, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Generic, Literal, NamedTuple, TypeVar, Union, final

from .constants import START, END


# 流模式类型定义
StreamMode = Literal[
    "values", "updates", "checkpoints", "tasks", "debug", "messages", "custom"
]
"""流方法应如何发出输出。

- `"values"`: 在每一步后发出状态中的所有值，包括中断。
- `"updates"`: 仅发出节点或任务名称和节点或任务在每一步后返回的更新。
- `"custom"`: 使用节点或任务内部的StreamWriter发出自定义数据。
- `"messages"`: 逐个token地发出LLM消息以及节点或任务内任何LLM调用的元数据。
- `"checkpoints"`: 在创建检查点时发出事件，格式与get_state()返回的格式相同。
- `"tasks"`: 在任务开始和完成时发出事件，包括其结果和错误。
- `"debug"`: 发出"checkpoints"和"tasks"事件用于调试目的。
"""

StreamWriter = Callable[[Any], None]
"""接受单个参数并将其写入输出流的Callable。
如果请求为关键字参数，则始终注入到节点中，但在不使用stream_mode="custom"时为无操作。"""


class StateUpdate(NamedTuple):
    """状态更新信息。"""
    
    values: Union[dict[str, Any], None]
    as_node: Union[str, None] = None
    task_id: Union[str, None] = None


class Task(NamedTuple):
    """图执行任务。"""
    
    id: str
    name: str
    path: tuple[Union[str, int, tuple], ...]
    error: Union[Exception, None] = None
    interrupts: tuple[Interrupt, ...] = ()  # type: ignore[name-defined]
    state: Union[None, dict[str, Any], "StateSnapshot"] = None
    result: Union[Any, None] = None


class CacheKey(NamedTuple):
    """任务的缓存键。"""
    
    ns: tuple[str, ...]
    """缓存条目的命名空间。"""
    key: str
    """缓存条目的键。"""
    ttl: Union[int, None]
    """缓存条目的生存时间（秒）。"""


@dataclass(frozen=True, slots=True)
class ExecutableTask:
    """可执行的任务。"""
    
    name: str
    input: Any
    proc: Callable
    writes: deque[tuple[str, Any]]
    config: dict[str, Any]
    triggers: Sequence[str]
    retry_policy: Sequence["RetryPolicy"]  # type: ignore[name-defined]
    cache_key: Union[CacheKey, None]
    id: str
    path: tuple[Union[str, int, tuple], ...]
    writers: Sequence[Callable] = ()


class StateSnapshot(NamedTuple):
    """步骤开始时图状态的快照。"""
    
    values: Union[dict[str, Any], Any]
    """通道的当前值。"""
    next: tuple[str, ...]
    """此步骤中每个任务要执行的节点名称。"""
    config: dict[str, Any]
    """用于获取此快照的配置。"""
    metadata: Union[dict[str, Any], None]
    """与此快照关联的元数据。"""
    created_at: Union[str, None]
    """快照创建的时间戳。"""
    parent_config: Union[dict[str, Any], None]
    """用于获取父快照的配置（如果有）。"""
    tasks: tuple[Task, ...]
    """此步骤中要执行的任务。如果已尝试，可能包含错误。"""
    interrupts: tuple[Interrupt, ...]  # type: ignore[name-defined]
    """此步骤中发生的待解决的中断。"""


class Send:
    """要发送到图中特定节点的消息或数据包。

    Send类在条件边内使用，以在下一步动态调用具有自定义状态的节点。

    重要的是，发送的状态可以与核心图的状态不同，
    允许灵活和动态的工作流管理。

    一个这样的例子是"map-reduce"工作流，其中图多次并行调用同一个节点，状态不同，
    然后将结果聚合回主图的状态。
    """

    __slots__ = ("node", "arg")

    node: str
    arg: Any

    def __init__(self, /, node: str, arg: Any) -> None:
        """
        初始化Send类的新实例。

        Args:
            node: 目标节点的名称。
            arg: 要发送到目标节点的状态或消息。
        """
        self.node = node
        self.arg = arg

    def __hash__(self) -> int:
        return hash((self.node, self.arg))

    def __repr__(self) -> str:
        return f"Send(node={self.node!r}, arg={self.arg!r})"

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Send)
            and self.node == value.node
            and self.arg == value.arg
        )


N = TypeVar("N", bound=Hashable)


@dataclass(frozen=True, slots=True, kw_only=True)
class Command(Generic[N]):
    """一个或多个命令来更新图的状态并向节点发送消息。

    Args:
        graph: 要发送命令的图。支持的值：
            - `None`: 当前图
            - `Command.PARENT`: 最近的父图
        update: 应用于图状态的更新。
        resume: 用于恢复执行的值。与`interrupt()`一起使用。
            可以是以下之一：
            - 中断ID到恢复值的映射
            - 用于恢复下一个中断的单个值
        goto: 可以是以下之一：
            - 要导航到的下一个节点的名称（属于指定`graph`的任何节点）
            - 要导航到的下一个节点名称序列
            - `Send`对象（使用提供的输入执行节点）
            - `Send`对象序列
    """

    graph: Union[str, None] = None
    update: Union[Any, None] = None
    resume: Union[dict[str, Any], Any, None] = None
    goto: Union[Send, Sequence[Union[Send, N]], N] = ()

    def __repr__(self) -> str:
        # 获取所有非None值
        contents = ", ".join(
            f"{key}={value!r}" for key, value in asdict(self).items() if value
        )
        return f"Command({contents})"

    def _update_as_tuples(self) -> Sequence[tuple[Union[str, Any], Any]]:
        if isinstance(self.update, dict):
            return list(self.update.items())
        elif isinstance(self.update, (list, tuple)) and all(
            isinstance(t, tuple) and len(t) == 2 and isinstance(t[0], str)
            for t in self.update
        ):
            return self.update
        elif self.update is not None:
            return [("__root__", self.update)]
        else:
            return []

    PARENT: str = "__parent__"


@final
@dataclass(init=False, slots=True)
class Interrupt:
    """关于节点中发生的中断的信息。"""

    value: Any
    """与中断关联的值。"""

    id: str
    """中断的ID。可用于直接恢复中断。"""

    def __init__(
        self,
        value: Any,
        id: str = "placeholder-id",
        **deprecated_kwargs: Any,
    ) -> None:
        self.value = value

        if (
            (ns := deprecated_kwargs.get("ns", None)) is not None
            and (id == "placeholder-id")
            and (isinstance(ns, Sequence))
        ):
            # 使用uuid替代xxhash
            self.id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "|".join(ns).encode()))
        else:
            self.id = id

    @classmethod
    def from_ns(cls, value: Any, ns: str) -> Interrupt:
        # 使用uuid替代xxhash
        return cls(value=value, id=str(uuid.uuid5(uuid.NAMESPACE_DNS, ns.encode())))


# 添加 MISSING 常量
class _MissingType:
    def __repr__(self) -> str:
        return "MISSING"


MISSING = _MissingType()


__all__ = [
    "StreamMode",
    "StreamWriter",
    "StateUpdate",
    "Task",
    "CacheKey",
    "ExecutableTask",
    "StateSnapshot",
    "Send",
    "Command",
    "Interrupt",
    "MISSING",
]