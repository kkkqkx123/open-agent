"""统一状态定义模块

提供工作流和图使用的统一状态定义。
"""

from .base import (
    BaseGraphState, create_base_state, BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
    GraphBaseMessage, GraphHumanMessage, GraphAIMessage, GraphSystemMessage, GraphToolMessage, MessageRole, create_message,
    LCBaseMessage
)
from .workflow import (
    WorkflowState, create_workflow_state, create_agent_state, create_react_state, create_plan_execute_state,
    update_state_with_message, update_state_with_tool_result, update_state_with_error,
    validate_state, serialize_state, deserialize_state
)
from .react import ReActState
from .plan_execute import PlanExecuteState
from .factory import StateFactory
from .serializer import StateSerializer
from .interface import ConflictType, ConflictResolutionStrategy
from .base_manager import BaseStateManager
from .pooling_manager import PoolingStateManager, create_optimized_state_manager
from .conflict_manager import ConflictStateManager, Conflict, create_enhanced_state_manager
from .version_manager import VersionStateManager
from .composite_manager import CompositeStateManager, create_composite_state_manager

__all__ = [
    "BaseGraphState",
    "WorkflowState",
    "ReActState",
    "PlanExecuteState",
    "StateFactory",
    "StateSerializer",
    "BaseStateManager",
    "PoolingStateManager",
    "ConflictStateManager",
    "VersionStateManager",
    "CompositeStateManager",
    "create_optimized_state_manager",
    "create_enhanced_state_manager",
    "create_composite_state_manager",
    "ConflictType",
    "ConflictResolutionStrategy",
    "Conflict",
    "create_base_state",
    "create_workflow_state",
    "create_agent_state",
    "create_react_state",
    "create_plan_execute_state",
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "GraphBaseMessage",
    "GraphHumanMessage",
    "GraphAIMessage",
    "GraphSystemMessage",
    "GraphToolMessage",
    "MessageRole",
    "LCBaseMessage",
    "update_state_with_message",
    "update_state_with_tool_result",
    "update_state_with_error",
    "validate_state",
    "serialize_state",
    "deserialize_state",
    "create_message"
]