"""状态基类模块

提供状态管理的基础接口和实现。
"""

from .state_base import BaseState
from .message_base import (
    MessageRole, BaseMessage, HumanMessage, AIMessage,
    SystemMessage, ToolMessage, MessageManager
)
from .workflow_state import WorkflowState

__all__ = [
    "BaseState",
    "MessageRole", "BaseMessage", "HumanMessage", "AIMessage",
    "SystemMessage", "ToolMessage", "MessageManager",
    "WorkflowState"
]