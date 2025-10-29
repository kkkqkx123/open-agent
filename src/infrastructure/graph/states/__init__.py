"""统一状态定义模块

提供工作流和图使用的统一状态定义。
"""

from .base import BaseGraphState, create_base_state, HumanMessage, AIMessage
from .workflow import WorkflowState, create_workflow_state
from .react import ReActState
from .plan_execute import PlanExecuteState
from .factory import StateFactory
from .serializer import StateSerializer
from .optimized_manager import OptimizedStateManager, create_optimized_state_manager
from .enhanced_manager import EnhancedStateManager, create_enhanced_state_manager, ConflictType, ConflictResolutionStrategy

__all__ = [
    "BaseGraphState",
    "WorkflowState",
    "ReActState",
    "PlanExecuteState",
    "StateFactory",
    "StateSerializer",
    "OptimizedStateManager",
    "create_optimized_state_manager",
    "EnhancedStateManager",
    "create_enhanced_state_manager",
    "ConflictType",
    "ConflictResolutionStrategy",
    "create_base_state",
    "create_workflow_state",
    "HumanMessage",
    "AIMessage"
]