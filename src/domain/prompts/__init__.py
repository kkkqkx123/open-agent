"""提示词管理模块

提供提示词的资产化管理，支持简单/复合提示词，提供统一的注册、加载、合并机制。
"""

from .interfaces import IPromptRegistry, IPromptLoader, IPromptInjector
from .models import PromptMeta, PromptConfig
from .registry import PromptRegistry
from .loader import PromptLoader
from .injector import PromptInjector
from ...infrastructure.graph.states import WorkflowState
from ..tools.interfaces import ToolResult
# 从langchain_core导入消息类型
from langchain_core.messages import SystemMessage, HumanMessage
from .langgraph_integration import create_agent_workflow, create_simple_workflow

__all__ = [
    "IPromptRegistry",
    "IPromptLoader", 
    "IPromptInjector",
    "PromptMeta",
    "PromptConfig",
    "PromptRegistry",
    "PromptLoader",
    "PromptInjector",
    "WorkflowState",
    "ToolResult",
    "SystemMessage",
    "HumanMessage",
    "create_agent_workflow",
    "create_simple_workflow",
]