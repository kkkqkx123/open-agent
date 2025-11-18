"""工作流核心接口

定义工作流系统的核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass

from .graph.interfaces import IGraph, INode, IEdge
from src.state.interfaces import IState


@dataclass
class ExecutionContext:
    """执行上下文"""
    workflow_id: str
    execution_id: str
    metadata: Dict[str, Any]
    config: Dict[str, Any]


class IWorkflow(ABC):
    """工作流接口"""

    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """工作流名称"""
        pass

    @property
    @abstractmethod
    def _nodes(self) -> Dict[str, INode]:
        """工作流节点字典"""
        pass

    @property
    @abstractmethod
    def _edges(self) -> Dict[str, IEdge]:
        """工作流边字典"""
        pass

    @property
    @abstractmethod
    def _entry_point(self) -> Optional[str]:
        """工作流入口点"""
        pass

    @abstractmethod
    def add_node(self, node: INode) -> None:
        """添加节点"""
        pass

    @abstractmethod
    def add_edge(self, edge: IEdge) -> None:
        """添加边"""
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """验证工作流"""
        pass

    @abstractmethod
    def execute(self, initial_state: IState, context: ExecutionContext) -> IState:
        """执行工作流"""
        pass

    @abstractmethod
    async def execute_async(self, initial_state: IState, context: ExecutionContext) -> IState:
        """异步执行工作流"""
        pass


class IWorkflowExecutor(ABC):
    """工作流执行器接口"""

    @abstractmethod
    def execute(self, workflow: IWorkflow, initial_state: IState, 
                context: ExecutionContext) -> IState:
        """执行工作流"""
        pass

    @abstractmethod
    async def execute_async(self, workflow: IWorkflow, initial_state: IState,
                           context: ExecutionContext) -> IState:
        """异步执行工作流"""
        pass

    @abstractmethod
    def execute_stream(self, workflow: IWorkflow, initial_state: IState,
                       context: ExecutionContext) -> List[Dict[str, Any]]:
        """流式执行工作流"""
        pass

    @abstractmethod
    async def execute_stream_async(self, workflow: IWorkflow, initial_state: IState,
                                  context: ExecutionContext) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流"""
        pass


class IWorkflowState(IState):
    """工作流状态接口"""
    pass


class IWorkflowBuilder(ABC):
    """工作流构建器接口"""

    @abstractmethod
    def create_workflow(self, config: Dict[str, Any]) -> IWorkflow:
        """创建工作流"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        pass