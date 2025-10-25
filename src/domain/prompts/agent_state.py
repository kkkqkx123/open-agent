"""Agent状态定义 - 向后兼容模块

此模块提供向后兼容性，重定向到新的workflow.state模块。
建议新代码使用 src.domain.workflow.state 模块。
"""

# 导入新的状态定义，提供向后兼容性
from ..workflow.state import (
    WorkflowState as AgentState,
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

# 保持原有的导出接口
__all__ = [
    "AgentState",
    "BaseMessage", 
    "SystemMessage",
    "HumanMessage",
    "AIMessage",
    "ToolMessage",
    "ToolResult",
    "create_message",
    "adapt_langchain_message"
]