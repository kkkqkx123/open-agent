"""基础设施层图类型定义

提供图引擎兼容的类型定义，支持状态图、检查点、命令等核心概念。
"""

# 导入错误类型
from .errors import (
    CheckpointError,
    CheckpointNotFoundError,
    DeliveryFailedError,
    EdgeNotFoundError,
    EmptyChannelError,
    GraphInterrupt,
    GraphRecursionError,
    GraphTypeError,
    GraphValueError,
    InvalidConfigurationError,
    InvalidGraphError,
    InvalidUpdateError,
    NodeNotFoundError,
)

# 导入常量
from .constants import (
    END,
    ERROR,
    INTERRUPT,
    INPUT,
    NO_WRITES,
    NS_END,
    NS_SEP,
    NULL_TASK_ID,
    PREVIOUS,
    PUSH,
    PULL,
    RESERVED,
    RESUME,
    START,
    TAG_HIDDEN,
    TAG_NOSTREAM,
    TASKS,
    RETURN,
)

# 导入数据结构
from .data_structures import (
    CacheKey,
    Command,
    ExecutableTask,
    Interrupt,
    MISSING,
    Send,
    StateSnapshot,
    StateUpdate,
    StreamMode,
    StreamWriter,
    Task,
)

# 导入策略类型
from .policies import (
    CachePolicy,
    RetryPolicy,
)

# 导入工具函数
from .utils import interrupt

# 添加工具输出混入类
class ToolOutputMixin:
    """工具输出混入类，用于兼容性。"""
    pass


__all__ = (
    # 数据结构
    "StateUpdate",
    "Task",
    "CacheKey",
    "ExecutableTask",
    "StateSnapshot",
    "Send",
    "Command",
    "Interrupt",
    "MISSING",
    "StreamMode",
    "StreamWriter",
    # 策略类型
    "RetryPolicy",
    "CachePolicy",
    # 工具函数
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
    "PUSH",
    "PULL",
    "NS_SEP",
    "NS_END",
    "NULL_TASK_ID",
    "RESERVED",
    "TAG_NOSTREAM",
    "TAG_HIDDEN",
    # 兼容性
    "ToolOutputMixin",
)