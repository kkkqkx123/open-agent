"""Core workflow interfaces.

This module contains the core workflow interfaces that define the contract
for workflow implementations without causing circular dependencies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import IWorkflowState
    from .graph import IGraph, INode, IEdge
    from .config import IGraphConfig

from ..common_domain import IValidationResult
from ...core.common import WorkflowExecutionContext

class IWorkflow(ABC):
    """工作流接口 - 纯数据容器"""

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
    def config(self) -> 'IGraphConfig':
        """工作流配置"""
        pass

    @property
    @abstractmethod
    def entry_point(self) -> Optional[str]:
        """入口点"""
        pass

    @property
    @abstractmethod
    def compiled_graph(self) -> Optional[Any]:
        """编译后的图"""
        pass

    @abstractmethod
    def set_entry_point(self, entry_point: str) -> None:
        """设置入口点"""
        pass

    @abstractmethod
    def set_graph(self, graph: Any) -> None:
        """设置编译后的图"""
        pass

    # 数据访问方法
    @abstractmethod
    def get_node(self, node_id: str) -> Optional['INode']:
        """获取节点"""
        pass

    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional['IEdge']:
        """获取边"""
        pass

    @abstractmethod
    def get_nodes(self) -> Dict[str, 'INode']:
        """获取所有节点"""
        pass

    @abstractmethod
    def get_edges(self) -> Dict[str, 'IEdge']:
        """获取所有边"""
        pass
    
    @abstractmethod
    def add_node(self, node_config: Any) -> None:
        """添加节点
        
        Args:
            node_config: 节点配置
        """
        pass
    
    @abstractmethod
    def add_edge(self, edge_config: Any) -> None:
        """添加边
        
        Args:
            edge_config: 边配置
        """
        pass


class IWorkflowManager(ABC):
    """工作流管理器接口 - 统一管理工作流生命周期"""

    @abstractmethod
    def create_workflow(self, config: 'IGraphConfig') -> IWorkflow:
        """创建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            IWorkflow: 工作流实例
        """
        pass

    @abstractmethod
    def execute_workflow(
        self,
        workflow: IWorkflow,
        initial_state: 'IWorkflowState',
        context: Optional[Dict[str, Any]] = None
    ) -> 'IWorkflowState':
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        pass

    @abstractmethod
    async def execute_workflow_async(
        self,
        workflow: IWorkflow,
        initial_state: 'IWorkflowState',
        context: Optional[Dict[str, Any]] = None
    ) -> 'IWorkflowState':
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        pass

    @abstractmethod
    def validate_workflow(self, workflow: IWorkflow) -> IValidationResult:
        """验证工作流
        
        Args:
            workflow: 工作流实例
            
        Returns:
            IValidationResult: 验证结果
        """
        pass

    @abstractmethod
    def compile_workflow(self, workflow: IWorkflow) -> None:
        """编译工作流
        
        Args:
            workflow: 工作流实例
        """
        pass

    @abstractmethod
    def get_workflow_status(self, workflow: IWorkflow) -> Dict[str, Any]:
        """获取工作流状态
        
        Args:
            workflow: 工作流实例
            
        Returns:
            Dict[str, Any]: 工作流状态信息
        """
        pass


class IWorkflowValidator(ABC):
    """工作流验证器接口"""

    @abstractmethod
    def validate(self, workflow: IWorkflow) -> IValidationResult:
        """验证工作流
        
        Args:
            workflow: 工作流实例
            
        Returns:
            IValidationResult: 验证结果
        """
        pass

    @abstractmethod
    def validate_config(self, config: 'IGraphConfig') -> IValidationResult:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            IValidationResult: 验证结果
        """
        pass


class IWorkflowRegistry(ABC):
    """工作流注册表接口"""

    @abstractmethod
    def register_workflow(self, workflow_id: str, workflow: IWorkflow) -> None:
        """注册工作流"""
        pass

    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """获取工作流"""
        pass

    @abstractmethod
    def unregister_workflow(self, workflow_id: str) -> bool:
        """注销工作流"""
        pass

    @abstractmethod
    def list_workflows(self) -> List[str]:
        """列出所有已注册的工作流"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空注册表"""
        pass
    
    @abstractmethod
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 注册表统计信息
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息（兼容接口）
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.get_registry_stats()