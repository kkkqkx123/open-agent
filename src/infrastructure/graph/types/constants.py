"""基础设施层图常量定义

提供LangGraph兼容的常量定义，包括保留键、配置键等。
"""

import sys
from typing import Literal, cast

__all__ = (
    "TAG_NOSTREAM",
    "TAG_HIDDEN",
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
)

# --- 公共常量 ---
TAG_NOSTREAM = sys.intern("nostream")
"""用于禁用聊天模型流的标记。"""
TAG_HIDDEN = sys.intern("langsmith:hidden")
"""用于在某些跟踪/流式环境中隐藏节点/边的标记。"""
END = sys.intern("__end__")
"""图样式Pregel中的最后一个（可能是虚拟）节点。"""
START = sys.intern("__start__")
"""图样式Pregel中的第一个（可能是虚拟）节点。"""

# --- 保留写入键 ---
INPUT = sys.intern("__input__")
# 用于作为输入传递给图的值
INTERRUPT = sys.intern("__interrupt__")
# 用于节点引发的动态中断
RESUME = sys.intern("__resume__")
# 用于在中断后传递给节点以恢复的值
ERROR = sys.intern("__error__")
# 用于节点引发的错误
NO_WRITES = sys.intern("__no_writes__")
# 标记信号节点没有写入任何内容
TASKS = sys.intern("__pregel_tasks")
# 用于节点/边返回的Send对象，对应下面的PUSH
RETURN = sys.intern("__return__")
# 用于我们只记录返回值的任务的写入
PREVIOUS = sys.intern("__previous__")
# 处理每个节点Control值的隐式分支

# --- 保留缓存命名空间 ---
CACHE_NS_WRITES = sys.intern("__pregel_ns_writes")
# 节点写入的缓存命名空间

# --- 保留config.configurable键 ---
CONFIG_KEY_SEND = sys.intern("__pregel_send")
# 保存接受状态/边/保留键写入的`write`函数
CONFIG_KEY_READ = sys.intern("__pregel_read")
# 保存返回当前状态副本的`read`函数
CONFIG_KEY_CALL = sys.intern("__pregel_call")
# 保存接受节点/函数、参数并返回future的`call`函数
CONFIG_KEY_CHECKPOINTER = sys.intern("__pregel_checkpointer")
# 保存从父图传递给子图的BaseCheckpointSaver
CONFIG_KEY_STREAM = sys.intern("__pregel_stream")
# 保存从父图传递给子图的StreamProtocol
CONFIG_KEY_CACHE = sys.intern("__pregel_cache")
# 保存提供给子图的BaseCache
CONFIG_KEY_RESUMING = sys.intern("__pregel_resuming")
# 保存一个布尔值，指示子图是否应该从先前的检查点恢复
CONFIG_KEY_TASK_ID = sys.intern("__pregel_task_id")
# 保存当前任务的task ID
CONFIG_KEY_THREAD_ID = sys.intern("thread_id")
# 保存当前调用的线程ID
CONFIG_KEY_CHECKPOINT_MAP = sys.intern("checkpoint_map")
# 保存checkpoint_ns -> checkpoint_id的映射，用于父图
CONFIG_KEY_CHECKPOINT_ID = sys.intern("checkpoint_id")
# 保存当前的checkpoint_id（如果有）
CONFIG_KEY_CHECKPOINT_NS = sys.intern("checkpoint_ns")
# 保存当前的checkpoint_ns，根图为""
CONFIG_KEY_NODE_FINISHED = sys.intern("__pregel_node_finished")
# 保存节点完成时要调用的回调
CONFIG_KEY_SCRATCHPAD = sys.intern("__pregel_scratchpad")
# 保存一个可变字典，用于当前任务范围的临时存储
CONFIG_KEY_RUNNER_SUBMIT = sys.intern("__pregel_runner_submit")
# 保存一个函数，该函数接收来自runner的任务，执行它们并返回结果
CONFIG_KEY_DURABILITY = sys.intern("__pregel_durability")
# 保存持久化模式，为"sync"、"async"或"exit"之一
CONFIG_KEY_RUNTIME = sys.intern("__pregel_runtime")
# 保存一个包含上下文、存储、流写入器等的Runtime实例
CONFIG_KEY_RESUME_MAP = sys.intern("__pregel_resume_map")
# 保存任务ns -> 恢复值的映射，用于恢复任务

# --- 其他常量 ---
PUSH = sys.intern("__pregel_push")
# 表示推送式任务，即由Send对象创建的任务
PULL = sys.intern("__pregel_pull")
# 表示拉取式任务，即由边触发的任务
NS_SEP = sys.intern("|")
# 用于checkpoint_ns，分隔每个级别（即graph|subgraph|subsubgraph）
NS_END = sys.intern(":")
# 用于checkpoint_ns，对于每个级别，将命名空间与task_id分隔开
CONF = cast(Literal["configurable"], sys.intern("configurable"))
# RunnableConfig中configurable字典的键
NULL_TASK_ID = sys.intern("00000000-0000-0000-0000-000000000000")
# 用于不与任务关联的写入的task_id

# 重新定义以避免与langgraph.constants的循环导入
_TAG_HIDDEN = sys.intern("langsmith:hidden")

RESERVED = {
    _TAG_HIDDEN,
    # 保留写入键
    INPUT,
    INTERRUPT,
    RESUME,
    ERROR,
    NO_WRITES,
    # 保留config.configurable键
    CONFIG_KEY_SEND,
    CONFIG_KEY_READ,
    CONFIG_KEY_CHECKPOINTER,
    CONFIG_KEY_STREAM,
    CONFIG_KEY_CHECKPOINT_MAP,
    CONFIG_KEY_RESUMING,
    CONFIG_KEY_TASK_ID,
    CONFIG_KEY_CHECKPOINT_MAP,
    CONFIG_KEY_CHECKPOINT_ID,
    CONFIG_KEY_CHECKPOINT_NS,
    CONFIG_KEY_RESUME_MAP,
    # 其他常量
    PUSH,
    PULL,
    NS_SEP,
    NS_END,
    CONF,
}