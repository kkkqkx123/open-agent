"""图引擎常量定义

提供图执行过程中使用的核心常量。
"""

import sys

# --- 核心节点常量 ---
START = sys.intern("__start__")
"""图样式中的第一个（可能是虚拟）节点。"""

END = sys.intern("__end__")
"""图样式中的最后一个（可能是虚拟）节点。"""

# --- 保留写入键 ---
INPUT = sys.intern("__input__")
"""用于作为输入传递给图的值。"""

INTERRUPT = sys.intern("__interrupt__")
"""用于节点引发的动态中断。"""

RESUME = sys.intern("__resume__")
"""用于在中断后传递给节点以恢复的值。"""

ERROR = sys.intern("__error__")
"""用于节点引发的错误。"""

NO_WRITES = sys.intern("__no_writes__")
"""标记信号节点没有写入任何内容。"""

TASKS = sys.intern("__pregel_tasks")
"""用于节点/边返回的Send对象，对应下面的PUSH。"""

RETURN = sys.intern("__return__")
"""用于我们只记录返回值的任务的写入。"""

PREVIOUS = sys.intern("__previous__")
"""处理每个节点Control值的隐式分支。"""

# --- 其他常量 ---
PUSH = sys.intern("__pregel_push")
"""表示推送式任务，即由Send对象创建的任务。"""

PULL = sys.intern("__pregel_pull")
"""表示拉取式任务，即由边触发的任务。"""

NS_SEP = sys.intern("|")
"""用于checkpoint_ns，分隔每个级别（即graph|subgraph|subsubgraph）。"""

NS_END = sys.intern(":")
"""用于checkpoint_ns，对于每个级别，将命名空间与task_id分隔开。"""

NULL_TASK_ID = sys.intern("00000000-0000-0000-0000-000000000000")
"""用于不与任务关联的写入的task_id。"""

# --- 公共常量 ---
TAG_NOSTREAM = sys.intern("nostream")
"""用于禁用聊天模型流的标记。"""

TAG_HIDDEN = sys.intern("langsmith:hidden")
"""用于在某些跟踪/流式环境中隐藏节点/边的标记。"""

# --- 保留字集合 ---
RESERVED = {
    TAG_HIDDEN,
    INPUT,
    INTERRUPT,
    RESUME,
    ERROR,
    NO_WRITES,
    TASKS,
    RETURN,
    PREVIOUS,
    PUSH,
    PULL,
    NS_SEP,
    NS_END,
}

__all__ = [
    # 核心节点常量
    "START",
    "END",
    # 保留写入键
    "INPUT",
    "INTERRUPT",
    "RESUME",
    "ERROR",
    "NO_WRITES",
    "TASKS",
    "RETURN",
    "PREVIOUS",
    # 其他常量
    "PUSH",
    "PULL",
    "NS_SEP",
    "NS_END",
    "NULL_TASK_ID",
    # 公共常量
    "TAG_NOSTREAM",
    "TAG_HIDDEN",
    # 保留字集合
    "RESERVED",
]