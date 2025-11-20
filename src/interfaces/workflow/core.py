"""Core workflow interfaces.

This module contains the core workflow interfaces that define the contract
for workflow implementations without causing circular dependencies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..state import IWorkflowState
    from .graph import IGraph, INode, IEdge

# 需要延迟导入避免循环依赖
try:
    from ...core.workflow.config.config import GraphConfig
except ImportError:
    GraphConfig = Any  # type: ignore


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
    def _nodes(self) -> Dict[str, 'INode']:
        """工作流节点字典"""
        pass

    @property
    @abstractmethod
    def _edges(self) -> Dict[str, 'IEdge']:
        """工作流边字典"""
        pass

    @property
    @abstractmethod
    def entry_point(self) -> Optional[str]:
        """入口点"""
        pass

    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """工作流描述"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """工作流版本"""
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """工作流元数据"""
        pass

    @metadata.setter
    @abstractmethod
    def metadata(self, value: Dict[str, Any]) -> None:
        """设置工作流元数据"""
        pass

    @property
    @abstractmethod
    def graph(self) -> Optional['IGraph']:
        """工作流图"""
        pass

    @abstractmethod
    def set_entry_point(self, entry_point: str) -> None:
        """设置入口点"""
        pass

    @abstractmethod
    def set_graph(self, graph: Any) -> None:
        """设置工作流图"""
        pass

    def get_graph(self) -> Any:
        """获取工作流图"""
        return self.graph

    @abstractmethod
    def add_node(self, node: 'INode') -> None:
        """添加节点"""
        pass

    @abstractmethod
    def add_edge(self, edge: 'IEdge') -> None:
        """添加边"""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional['INode']:
        """获取节点"""
        pass

    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional['IEdge']:
        """获取边"""
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """验证工作流"""
        pass

    @abstractmethod
    def execute(self, initial_state: 'IWorkflowState', context: ExecutionContext) -> 'IWorkflowState':
        """执行工作流"""
        pass

    @abstractmethod
    async def execute_async(self, initial_state: 'IWorkflowState', context: ExecutionContext) -> 'IWorkflowState':
        """异步执行工作流"""
        pass