"""Graph基础设施模块

提供LangGraph相关的核心基础设施，包括：
- 图构建器
- 状态定义
- 配置模型
- 节点注册系统
"""

from .builder import GraphBuilder
from .state import (
    BaseGraphState,
    AgentState,
    WorkflowState,
    ReActState,
    PlanExecuteState,
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    MessageRole,
    create_agent_state,
    create_workflow_state,
    create_react_state,
    create_plan_execute_state,
    create_message,
    update_state_with_message,
    update_state_with_tool_result,
    update_state_with_error,
    validate_state,
    serialize_state,
    deserialize_state
)
from .config import (
    GraphConfig,
    NodeConfig,
    EdgeConfig,
    EdgeType,
    StateFieldConfig,
    GraphStateConfig
)
from .registry import (
    NodeRegistry,
    BaseNode,
    NodeExecutionResult,
    get_global_registry,
    register_node,
    get_node
)

__all__ = [
    # 构建器
    "GraphBuilder",
    
    # 状态类型
    "BaseGraphState",
    "AgentState",
    "WorkflowState",
    "ReActState",
    "PlanExecuteState",
    
    # 消息类型
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "MessageRole",
    
    # 状态工厂函数
    "create_agent_state",
    "create_workflow_state",
    "create_react_state",
    "create_plan_execute_state",
    "create_message",
    "update_state_with_message",
    "update_state_with_tool_result",
    "update_state_with_error",
    "validate_state",
    "serialize_state",
    "deserialize_state",
    
    # 配置类型
    "GraphConfig",
    "NodeConfig",
    "EdgeConfig",
    "EdgeType",
    "StateFieldConfig",
    "GraphStateConfig",
    
    # 注册系统
    "NodeRegistry",
    "BaseNode",
    "NodeExecutionResult",
    "get_global_registry",
    "register_node",
    "get_node",
]