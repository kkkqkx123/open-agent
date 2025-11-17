"""工作流核心模块

提供工作流的核心实现，包括图子模块、执行引擎和插件系统。
"""

from .interfaces import IWorkflow, IWorkflowExecutor, IWorkflowState, ExecutionContext
from .entities import Workflow, WorkflowExecution, NodeExecution, WorkflowState, ExecutionResult, WorkflowMetadata
from .workflow import Workflow as WorkflowImpl
from .graph import IGraph, INode, IEdge, IGraphBuilder, INodeRegistry, IRoutingFunction, IRoutingRegistry
from .execution import IExecutor, IAsyncExecutor, IStreamingExecutor, IExecutionContext

__all__ = [
    # 核心接口
    "IWorkflow",
    "IWorkflowExecutor", 
    "IWorkflowState",
    "ExecutionContext",
    
    # 实体
    "Workflow",
    "WorkflowExecution",
    "NodeExecution",
    "WorkflowState",
    "ExecutionResult",
    "WorkflowMetadata",
    
    # 实现
    "WorkflowImpl",
    
    # 图子模块
    "IGraph",
    "INode",
    "IEdge",
    "IGraphBuilder",
    "INodeRegistry",
    "IRoutingFunction",
    "IRoutingRegistry",
    
    # 执行引擎
    "IExecutor",
    "IAsyncExecutor",
    "IStreamingExecutor",
    "IExecutionContext"
]