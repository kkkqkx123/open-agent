"""图系统适配器层

提供域层状态与图系统状态之间的适配器，解决状态定义冲突问题。
"""

from .state_adapter import StateAdapter
from .message_adapter import MessageAdapter
from .factory import AdapterFactory, get_adapter_factory, get_state_adapter, get_message_adapter, create_state_adapter, create_message_adapter

__all__ = [
    "StateAdapter",
    "MessageAdapter",
    "AdapterFactory",
    "get_adapter_factory",
    "get_state_adapter", 
    "get_message_adapter",
    "create_state_adapter",
    "create_message_adapter"
]