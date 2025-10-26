"""提示词管理模块

提供提示词的资产化管理，支持简单/复合提示词，提供统一的注册、加载、合并机制。
"""

from .interfaces import IPromptRegistry, IPromptLoader, IPromptInjector
from .models import PromptMeta, PromptConfig
from .registry import PromptRegistry
from .loader import PromptLoader
from .injector import PromptInjector
from ...application.workflow.state import AgentState, ToolResult
try:
    from .agent_state import SystemMessage, HumanMessage
except ImportError:
    # 如果导入失败，跳过这些类
    pass
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
    "AgentState",
    "ToolResult",
    "SystemMessage",
    "HumanMessage",
    "create_agent_workflow",
    "create_simple_workflow",
]