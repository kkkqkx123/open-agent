"""工作流领域模块

包含工作流状态定义、配置模型和核心接口。
"""

from .state import (
    WorkflowState,
    AgentState,  # 向后兼容别名
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    ToolResult,
    WorkflowStatus,
    MessageRole,
    create_message,
    adapt_langchain_message
)

from .config import (
    WorkflowConfig,
    NodeConfig,
    EdgeConfig,
    EdgeType,
    StateSchemaConfig
)

__all__ = [
    # 状态相关
    "WorkflowState",
    "AgentState",
    "BaseMessage",
    "SystemMessage", 
    "HumanMessage",
    "AIMessage",
    "ToolMessage",
    "ToolResult",
    "WorkflowStatus",
    "MessageRole",
    "create_message",
    "adapt_langchain_message",
    
    # 配置相关
    "WorkflowConfig",
    "NodeConfig", 
    "EdgeConfig",
    "EdgeType",
    "StateSchemaConfig"
]