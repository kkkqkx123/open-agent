"""基础设施层图类型定义

提供LangGraph兼容的类型定义，支持状态图、检查点、命令等核心概念。
"""

from __future__ import annotations

import sys
import uuid
from collections import deque
from collections.abc import Callable, Hashable, Sequence
from dataclasses import asdict, dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Literal,
    NamedTuple,
    TypeVar,
    Union,
    final,
)
from warnings import warn

from typing_extensions import Unpack, deprecated

if TYPE_CHECKING:
    from typing import Any
    # 简化的PregelProtocol类型定义
    class PregelProtocol:
        pass

# 导入错误类型
from .errors import (
    EmptyChannelError,
    GraphRecursionError,
    InvalidUpdateError,
    GraphInterrupt,
    InvalidGraphError,
    NodeNotFoundError,
    GraphValueError,
    GraphTypeError,
    EdgeNotFoundError,
    CheckpointNotFoundError,
    CheckpointError,
    DeliveryFailedError,
    InvalidConfigurationError,
)

# 导入常量
from .constants import (
    START,
    END,
    INPUT,
    INTERRUPT,
    RESUME,
    ERROR,
    NO_WRITES,
    TASKS,
    RETURN,
    PREVIOUS,
    CONFIG_KEY_SEND,
    CONFIG_KEY_READ,
    CONFIG_KEY_CALL,
    CONFIG_KEY_CHECKPOINTER,
    CONFIG_KEY_STREAM,
    CONFIG_KEY_CACHE,
    CONFIG_KEY_RESUMING,
    CONFIG_KEY_TASK_ID,
    CONFIG_KEY_THREAD_ID,
    CONFIG_KEY_CHECKPOINT_MAP,
    CONFIG_KEY_CHECKPOINT_ID,
    CONFIG_KEY_CHECKPOINT_NS,
    CONFIG_KEY_NODE_FINISHED,
    CONFIG_KEY_SCRATCHPAD,
    CONFIG_KEY_RUNNER_SUBMIT,
    CONFIG_KEY_DURABILITY,
    CONFIG_KEY_RUNTIME,
    CONFIG_KEY_RESUME_MAP,
    PUSH,
    PULL,
    NS_SEP,
    NS_END,
    CONF,
    NULL_TASK_ID,
    RESERVED,
    TAG_NOSTREAM,
    TAG_HIDDEN,
)

# 添加 MISSING 常量
class _MissingType:
    def __repr__(self) -> str:
        return "MISSING"

MISSING = _MissingType()

try:
    from langchain_core.messages import ToolMessage  # type: ignore[import-not-found]
    ToolOutputMixin = ToolMessage  # type: ignore[assignment]
except (ImportError, ModuleNotFoundError):

    class ToolOutputMixin:  # type: ignore[no-redef]
        pass


__all__ = (
    "All",
    "Checkpointer",
    "StreamMode",
    "StreamWriter",
    "RetryPolicy",
    "CachePolicy",
    "Interrupt",
    "StateUpdate",
    "PregelTask",
    "PregelExecutableTask",
    "StateSnapshot",
    "Send",
    "Command",
    "Durability",
    "interrupt",
    # 错误类型
    "GraphInterrupt",
    "GraphRecursionError",
    "GraphValueError",
    "GraphTypeError",
    "EmptyChannelError",
    "InvalidUpdateError",
    "NodeNotFoundError",
    "EdgeNotFoundError",
    "InvalidGraphError",
    "CheckpointNotFoundError",
    "CheckpointError",
    "DeliveryFailedError",
    "InvalidConfigurationError",
    # 常量
    "START",
    "END",
    "INPUT",
    "INTERRUPT",
    "RESUME",
    "ERROR",
    "NO_WRITES",
    "TASKS",
    "RETURN",
    "PREVIOUS",
    "CONFIG_KEY_SEND",
    "CONFIG_KEY_READ",
    "CONFIG_KEY_CALL",
    "CONFIG_KEY_CHECKPOINTER",
    "CONFIG_KEY_STREAM",
    "CONFIG_KEY_CACHE",
    "CONFIG_KEY_RESUMING",
    "CONFIG_KEY_TASK_ID",
    "CONFIG_KEY_THREAD_ID",
    "CONFIG_KEY_CHECKPOINT_MAP",
    "CONFIG_KEY_CHECKPOINT_ID",
    "CONFIG_KEY_CHECKPOINT_NS",
    "CONFIG_KEY_NODE_FINISHED",
    "CONFIG_KEY_SCRATCHPAD",
    "CONFIG_KEY_RUNNER_SUBMIT",
    "CONFIG_KEY_DURABILITY",
    "CONFIG_KEY_RUNTIME",
    "CONFIG_KEY_RESUME_MAP",
    "PUSH",
    "PULL",
    "NS_SEP",
    "NS_END",
    "CONF",
    "NULL_TASK_ID",
    "RESERVED",
    "TAG_NOSTREAM",
    "TAG_HIDDEN",
    "MISSING",
)

Durability = Literal["sync", "async", "exit"]
"""图执行的持久化模式。
- `"sync"`: 更改在下一步开始前同步持久化。
- `"async"`: 更改在下一步执行时异步持久化。
- `"exit"`: 更改仅在图退出时持久化。"""

All = Literal["*"]
"""特殊值，表示图应该在所有节点上中断。"""

if TYPE_CHECKING:
    from typing import Any
    # 简化的BaseCheckpointSaver类型定义
    class BaseCheckpointSaver:
        pass

Checkpointer = Union[None, bool, "BaseCheckpointSaver"]
"""检查点类型。
- True: 为此子图启用持久化检查点。
- False: 禁用检查点，即使父图有检查点。
- None: 从父图继承检查点。"""

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

_DC_KWARGS = {"kw_only": True, "slots": True, "frozen": True}


class RetryPolicy(NamedTuple):
    """重试节点的配置。

    !!! version-added "Added in version 0.2.24"
    """

    initial_interval: float = 0.5
    """第一次重试发生前必须经过的时间量。以秒为单位。"""
    backoff_factor: float = 2.0
    """每次重试后间隔增加的倍数。"""
    max_interval: float = 128.0
    """重试之间可能经过的最长时间。以秒为单位。"""
    max_attempts: int = 3
    """放弃前的最大尝试次数，包括第一次。"""
    jitter: bool = True
    """是否在重试之间的间隔中添加随机抖动。"""
    retry_on: Union[
        type[Exception], Sequence[type[Exception]], Callable[[Exception], bool]
    ] = lambda exc: False  # 默认不重试
    """应触发重试的异常类列表，或应为应触发重试的异常返回True的可调用对象。"""


KeyFuncT = TypeVar("KeyFuncT", bound=Callable[..., Union[str, bytes]])


@dataclass(**_DC_KWARGS)
class CachePolicy(Generic[KeyFuncT]):
    """节点的缓存配置。"""

    key_func: KeyFuncT = field(default_factory=lambda: (lambda *args, **kwargs: ""))  # type: ignore[assignment]
    """从节点输入生成缓存键的函数。
    默认为使用pickle对输入进行哈希处理。"""

    ttl: Union[int, None] = None
    """缓存条目的生存时间（秒）。如果为None，则条目永不过期。"""


_DEFAULT_INTERRUPT_ID = "placeholder-id"


@final
@dataclass(init=False, slots=True)
class Interrupt:
    """关于节点中发生的中断的信息。

    !!! version-added "Added in version 0.2.24"

    !!! version-changed "Changed in version v0.4.0"
        * 引入了`interrupt_id`作为属性

    !!! version-changed "Changed in version v0.6.0"

        以下属性已被移除：

        * `ns`
        * `when`
        * `resumable`
        * `interrupt_id`，已弃用，改用`id`
    """

    value: Any
    """与中断关联的值。"""

    id: str
    """中断的ID。可用于直接恢复中断。"""

    def __init__(
        self,
        value: Any,
        id: str = _DEFAULT_INTERRUPT_ID,
        **deprecated_kwargs: Any,
    ) -> None:
        self.value = value

        if (
            (ns := deprecated_kwargs.get("ns", None)) is not None
            and (id == _DEFAULT_INTERRUPT_ID)
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

    @property
    @deprecated("`interrupt_id` is deprecated. Use `id` instead.", category=None)
    def interrupt_id(self) -> str:
        warn(
            "`interrupt_id` is deprecated. Use `id` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.id


class StateUpdate(NamedTuple):
    values: Union[dict[str, Any], None]
    as_node: Union[str, None] = None
    task_id: Union[str, None] = None


class PregelTask(NamedTuple):
    """一个Pregel任务。"""

    id: str
    name: str
    path: tuple[Union[str, int, tuple], ...]
    error: Union[Exception, None] = None
    interrupts: tuple[Interrupt, ...] = ()
    state: Union[None, dict[str, Any], StateSnapshot] = None  # 简化的配置
    result: Union[Any, None] = None


if sys.version_info > (3, 11):
    _T_DC_KWARGS = {"weakref_slot": True, "slots": True, "frozen": True}
else:
    _T_DC_KWARGS = {"frozen": True}


class CacheKey(NamedTuple):
    """任务的缓存键。"""

    ns: tuple[str, ...]
    """缓存条目的命名空间。"""
    key: str
    """缓存条目的键。"""
    ttl: Union[int, None]
    """缓存条目的生存时间（秒）。"""


@dataclass(**_T_DC_KWARGS)
class PregelExecutableTask:
    name: str
    input: Any
    proc: Callable  # 简化的Runnable
    writes: deque[tuple[str, Any]]
    config: dict[str, Any]  # 简化的RunnableConfig
    triggers: Sequence[str]
    retry_policy: Sequence[RetryPolicy]
    cache_key: Union[CacheKey, None]
    id: str
    path: tuple[Union[str, int, tuple], ...]
    writers: Sequence[Callable] = ()  # 简化的Runnable
    subgraphs: Sequence["PregelProtocol"] = ()


class StateSnapshot(NamedTuple):
    """步骤开始时图状态的快照。"""

    values: Union[dict[str, Any], Any]
    """通道的当前值。"""
    next: tuple[str, ...]
    """此步骤中每个任务要执行的节点名称。"""
    config: dict[str, Any]  # 简化的RunnableConfig
    """用于获取此快照的配置。"""
    metadata: Union[dict[str, Any], None]  # 简化的CheckpointMetadata
    """与此快照关联的元数据。"""
    created_at: Union[str, None]
    """快照创建的时间戳。"""
    parent_config: Union[dict[str, Any], None]  # 简化的RunnableConfig
    """用于获取父快照的配置（如果有）。"""
    tasks: tuple[PregelTask, ...]
    """此步骤中要执行的任务。如果已尝试，可能包含错误。"""
    interrupts: tuple[Interrupt, ...]
    """此步骤中发生的待解决的中断。"""


class Send:
    """要发送到图中特定节点的消息或数据包。

    Send类在StateGraph的条件边内使用，以在下一步动态调用具有自定义状态的节点。

    重要的是，发送的状态可以与核心图的状态不同，
    允许灵活和动态的工作流管理。

    一个这样的例子是"map-reduce"工作流，其中图多次并行调用同一个节点，状态不同，
    然后将结果聚合回主图的状态。

    属性：
        node (str): 目标节点的名称。
        arg (Any): 要发送到目标节点的状态或消息。
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


@dataclass(**_DC_KWARGS)
class Command(Generic[N]):
    """一个或多个命令来更新图的状态并向节点发送消息。

    !!! version-added "Added in version 0.2.24"

    Args:
        graph: 要发送命令的图。支持的值：

            - `None`: 当前图
            - `Command.PARENT`: 最近的父图
        update: 应用于图状态的更新。
        resume: 用于恢复执行的值。与[`interrupt()`][langgraph.types.interrupt]一起使用。
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
        # 简化实现，移除对不存在函数的调用
        elif self.update is not None:
            return [("__root__", self.update)]
        else:
            return []

    PARENT: ClassVar[Literal["__parent__"]] = "__parent__"


def interrupt(value: Any) -> Any:
    """从节点内部中断图，带有可恢复的异常。

    interrupt函数通过暂停图执行并向客户端显示值来启用人在环工作流。
    此值可以传达上下文或请求恢复执行所需的输入。

    在给定节点中，此函数的第一次调用引发GraphInterrupt异常，停止执行。
    提供的值包含在异常中并发送给执行图的客户端。

    恢复图的客户端必须使用[`Command`][langgraph.types.Command]原语
    指定中断的值并继续执行。
    图从节点的开始恢复，**重新执行**所有逻辑。

    如果节点包含多个interrupt调用，LangGraph根据节点中的顺序将恢复值与中断匹配。
    此恢复值列表特定于执行节点的任务，不在任务间共享。

    要使用中断，必须启用检查点，因为该功能依赖于持久化图状态。

    Args:
        value: 图中断时向客户端显示的值。

    Returns:
        Any: 在同一节点（精确地说是同一任务）中的后续调用中，返回第一次调用期间提供的值

    Raises:
        GraphInterrupt: 在节点中的第一次调用时，停止执行并向客户端显示提供的值。
    """
    # 简化的实现，实际应该与检查点系统集成
    from .errors import GraphInterrupt
    raise GraphInterrupt([Interrupt(value=value)])