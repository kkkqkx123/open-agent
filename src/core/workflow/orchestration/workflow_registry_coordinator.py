"""工作流注册表协调器 - 改造自 WorkflowManager

专注于多个工作流的注册和管理，与 WorkflowInstanceCoordinator 协作。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state.workflow import IWorkflowState
from core.workflow.workflow_instance import WorkflowInstance
from src.core.workflow.registry.registry import WorkflowRegistry
from .workflow_instance_coordinator import WorkflowInstanceCoordinator


class IWorkflowRegistryCoordinator(ABC):
    """工作流注册表协调器接口"""
    
    @abstractmethod
    def register_workflow(self, workflow_id: str, workflow: IWorkflow) -> None:
        """注册工作流"""
        pass
    
    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """获取工作流"""
        pass
    
    @abstractmethod
    def create_workflow_coordinator(self, workflow_id: str) -> WorkflowInstanceCoordinator:
        """创建工作流实例协调器"""
        pass
    
    @abstractmethod
    def execute_workflow(
        self, 
        workflow_id: str, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """执行工作流"""
        pass
    
    @abstractmethod
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有已注册的工作流"""
        pass
    
    @abstractmethod
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        pass


class WorkflowRegistryCoordinator(IWorkflowRegistryCoordinator):
    """工作流注册表协调器
    
    专注于多个工作流的注册和管理，改造自 WorkflowManager。
    与 WorkflowInstanceCoordinator 协作提供完整的工作流管理功能。
    """
    
    def __init__(self, registry: Optional[WorkflowRegistry] = None):
        """初始化工作流注册表协调器
        
        Args:
            registry: 工作流注册表（可选，默认创建）
        """
        self._registry = registry or WorkflowRegistry()
        
        # 工作流实例协调器缓存
        self._coordinators: Dict[str, WorkflowInstanceCoordinator] = {}
        
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.debug("工作流注册表协调器初始化完成")
    
    def register_workflow(self, workflow_id: str, workflow: IWorkflow) -> None:
        """注册工作流
        
        Args:
            workflow_id: 工作流ID
            workflow: 工作流实例
        """
        self._registry.register_workflow(workflow_id, workflow)
        
        # 创建对应的协调器
        coordinator = WorkflowInstanceCoordinator(workflow)
        self._coordinators[workflow_id] = coordinator
        
        self.logger.info(f"注册工作流: {workflow_id}")
    
    def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """获取工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[IWorkflow]: 工作流实例
        """
        return self._registry.get_workflow(workflow_id)
    
    def create_workflow_coordinator(self, workflow_id: str) -> WorkflowInstanceCoordinator:
        """创建工作流实例协调器
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            WorkflowInstanceCoordinator: 工作流实例协调器
        """
        if workflow_id in self._coordinators:
            return self._coordinators[workflow_id]
        
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        coordinator = WorkflowInstanceCoordinator(workflow)
        self._coordinators[workflow_id] = coordinator
        return coordinator
    
    def execute_workflow(
        self, 
        workflow_id: str, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """执行工作流 - 委托给对应的协调器
        
        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        coordinator = self.create_workflow_coordinator(workflow_id)
        
        # 如果未提供初始状态，创建默认状态
        if initial_state is None:
            try:
                from src.core.state.factories.state_factory import create_workflow_state
                workflow = self.get_workflow(workflow_id)
                initial_state = create_workflow_state(
                    workflow_id=workflow_id,
                    workflow_name=workflow.name if workflow else "",
                    input_text=""
                )
            except ImportError:
                # 如果无法导入状态工厂，创建一个简单的状态对象
                from src.core.state.implementations.workflow_state import WorkflowState
                initial_state = WorkflowState(
                    id=workflow_id,
                    data={}
                )
        
        return coordinator.execute_workflow(initial_state, config)
    
    async def execute_workflow_async(
        self, 
        workflow_id: str, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """异步执行工作流 - 委托给对应的协调器
        
        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        coordinator = self.create_workflow_coordinator(workflow_id)
        
        # 如果未提供初始状态，创建默认状态
        if initial_state is None:
            try:
                from src.core.state.factories.state_factory import create_workflow_state
                workflow = self.get_workflow(workflow_id)
                initial_state = create_workflow_state(
                    workflow_id=workflow_id,
                    workflow_name=workflow.name if workflow else "",
                    input_text=""
                )
            except ImportError:
                # 如果无法导入状态工厂，创建一个简单的状态对象
                from src.core.state.implementations.workflow_state import WorkflowState
                initial_state = WorkflowState(
                    id=workflow_id,
                    data={}
                )
        
        return await coordinator.execute_workflow_async(initial_state, config)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流状态
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict[str, Any]: 工作流状态信息
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        coordinator = self._coordinators.get(workflow_id)
        stats = coordinator.get_coordinator_stats() if coordinator else {}
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": "registered",
            "active_executions": stats.get("active_executions", 0),
            "total_executions": stats.get("total_executions", 0)
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有已注册的工作流
        
        Returns:
            List[Dict[str, Any]]: 工作流信息列表
        """
        workflow_ids = self._registry.list_workflows()
        result = []
        for workflow_id in workflow_ids:
            workflow = self.get_workflow(workflow_id)
            if workflow:
                coordinator = self._coordinators.get(workflow_id)
                stats = coordinator.get_coordinator_stats() if coordinator else {}
                
                result.append({
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "status": "registered",
                    "active_executions": stats.get("active_executions", 0)
                })
        return result
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否删除成功
        """
        # 清理协调器
        if workflow_id in self._coordinators:
            del self._coordinators[workflow_id]
        
        # 从注册表删除
        return self._registry.unregister_workflow(workflow_id)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        workflow_ids = self._registry.list_workflows()
        
        # 统计所有协调器的执行情况
        total_active_executions = 0
        total_executions = 0
        
        for workflow_id in workflow_ids:
            coordinator = self._coordinators.get(workflow_id)
            if coordinator:
                stats = coordinator.get_coordinator_stats()
                total_active_executions += stats.get("active_executions", 0)
                total_executions += stats.get("total_executions", 0)
        
        return {
            "registered_workflows": len(workflow_ids),
            "active_coordinators": len(self._coordinators),
            "total_active_executions": total_active_executions,
            "total_executions": total_executions,
            "workflow_ids": workflow_ids
        }