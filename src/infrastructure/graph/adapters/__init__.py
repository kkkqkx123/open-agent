"""图系统适配器层

提供工作流状态与图系统状态之间的适配器，解决状态定义冲突问题。
已移除agent层，现在专注于WorkflowState的适配和转换。
"""

from .state_adapter import StateAdapter, WorkflowStateAdapter, GraphAgentState  # GraphAgentState 保持向后兼容
from .message_adapter import MessageAdapter
from .factory import AdapterFactory, get_adapter_factory, get_state_adapter, get_message_adapter, create_state_adapter, create_message_adapter

__all__ = [
    "StateAdapter",
    "MessageAdapter",
    "WorkflowStateAdapter",
    "GraphAgentState",  # 向后兼容
    "AdapterFactory",
    "get_adapter_factory",
    "get_state_adapter",
    "get_message_adapter",
    "create_state_adapter",
    "create_message_adapter"
]