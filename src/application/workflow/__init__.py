"""工作流系统模块

基于LangGraph的YAML配置化工作流系统，支持ReAct等工作流模式。
重构后提供统一的工作流创建接口和改进的状态管理。
"""

from .manager import IWorkflowManager, WorkflowManager
from ...domain.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, StateSchemaConfig
from ...domain.workflow.state import WorkflowState, AgentState
from .registry import NodeRegistry, BaseNode, NodeExecutionResult, register_node, get_node, get_global_registry
from .builder import WorkflowBuilder
from .factory import (
    IWorkflowFactory,
    UnifiedWorkflowFactory,
    get_global_factory,
    create_workflow_from_config,
    create_simple_workflow,
    create_react_workflow,
    create_plan_execute_workflow
)
from .nodes import AnalysisNode, ToolNode, LLMNode, ConditionNode
from .edges import SimpleEdge, ConditionalEdge
from .auto_discovery import auto_register_nodes, register_builtin_nodes
from .visualization import IWorkflowVisualizer, create_visualizer

# 自动注册预定义节点
try:
    from .nodes.analysis_node import AnalysisNode as _AnalysisNode
    from .nodes.tool_node import ToolNode as _ToolNode
    from .nodes.llm_node import LLMNode as _LLMNode
    from .nodes.condition_node import ConditionNode as _ConditionNode
    
    # 初始化时自动注册内置节点
    register_builtin_nodes()
except ImportError as e:
    # 如果节点模块不存在，记录警告但不中断导入
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"无法导入节点模块: {e}")

__all__ = [
    # 核心接口
    "IWorkflowManager",
    "WorkflowManager",
    "IWorkflowFactory",
    "UnifiedWorkflowFactory",
    
    # 配置和状态
    "WorkflowConfig",
    "NodeConfig",
    "EdgeConfig", 
    "StateSchemaConfig",
    "WorkflowState",
    "AgentState",  # 向后兼容
    
    # 节点系统
    "NodeRegistry",
    "BaseNode",
    "NodeExecutionResult",
    "AnalysisNode",
    "ToolNode",
    "LLMNode",
    "ConditionNode",
    
    # 构建器
    "WorkflowBuilder",
    
    # 工厂接口
    "get_global_factory",
    "create_workflow_from_config",
    "create_simple_workflow",
    "create_react_workflow",
    "create_plan_execute_workflow",
    
    # 边系统
    "SimpleEdge",
    "ConditionalEdge",
    
    # 注册功能
    "register_node",
    "get_node",
    "get_global_registry",
    "auto_register_nodes",
    "register_builtin_nodes",
    
    # 可视化
    "IWorkflowVisualizer",
    "create_visualizer",
]