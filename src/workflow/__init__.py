"""工作流系统模块

基于LangGraph的YAML配置化工作流系统，支持ReAct等工作流模式。
"""

from .manager import IWorkflowManager, WorkflowManager
from .config import WorkflowConfig, NodeConfig, EdgeConfig, StateSchemaConfig
from .registry import NodeRegistry, BaseNode, NodeExecutionResult, register_node, get_node
from .builder import WorkflowBuilder
from .nodes import AnalysisNode, ToolNode, LLMNode, ConditionNode
from .edges import SimpleEdge, ConditionalEdge

# 自动注册预定义节点
from .nodes.analysis_node import AnalysisNode as _AnalysisNode
from .nodes.tool_node import ToolNode as _ToolNode
from .nodes.llm_node import LLMNode as _LLMNode
from .nodes.condition_node import ConditionNode as _ConditionNode

__all__ = [
    "IWorkflowManager",
    "WorkflowManager",
    "WorkflowConfig",
    "NodeConfig",
    "EdgeConfig",
    "StateSchemaConfig",
    "NodeRegistry",
    "BaseNode",
    "NodeExecutionResult",
    "WorkflowBuilder",
    "AnalysisNode",
    "ToolNode",
    "LLMNode",
    "ConditionNode",
    "SimpleEdge",
    "ConditionalEdge",
    "register_node",
    "get_node",
]