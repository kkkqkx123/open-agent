"""工作流系统模块

基于LangGraph的增强工作流系统，支持ReAct等工作流模式。
提供统一的工作流创建接口、模板系统、Agent集成和改进的状态管理。
新版本WorkflowBuilder支持：
- 配置驱动的构建过程
- 工作流模板系统
- Agent节点自动注册
- 多种配置输入格式
- 向后兼容的API
"""

from .manager import IWorkflowManager, WorkflowManager
from src.application.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, StateSchemaConfig
from src.application.workflow.state import WorkflowState, AgentState
from .registry import NodeRegistry, BaseNode, NodeExecutionResult, register_node, get_node, get_global_registry
from .builder import WorkflowBuilder, INodeExecutor, AgentNodeExecutor
from .interfaces import IWorkflowBuilder
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
    "IWorkflowBuilder",
    "INodeExecutor",
    "AgentNodeExecutor",
    
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