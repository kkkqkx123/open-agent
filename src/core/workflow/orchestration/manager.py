"""遵循新架构的工作流管理器实现。

此模块提供工作流管理器服务，处理工作流生命周期、
执行和与其他服务的协调。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state.workflow import IWorkflowState
from src.core.workflow.workflow import Workflow
from .orchestrator import WorkflowOrchestrator
from ..execution.core.workflow_executor import WorkflowExecutor
from src.interfaces.workflow.execution import IWorkflowExecutor as IWorkflowExecutorInterface
from ..registry.registry import WorkflowRegistry


class IWorkflowManager(ABC):
    """工作流管理器接口"""
    
    @abstractmethod
    def create_workflow(self, workflow_id: str, name: str, config: Dict[str, Any]) -> IWorkflow:
        """创建新工作流"""
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
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流的状态"""
        pass
    
    @abstractmethod
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有已注册的工作流"""
        pass
    
    @abstractmethod
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        pass


class WorkflowManager(IWorkflowManager):
    """工作流管理器服务。
    
    此类提供高级工作流管理功能，
    包括工作流创建、执行、监控和生命周期管理。
    """
    
    def __init__(
        self,
        orchestrator: WorkflowOrchestrator,
        executor: IWorkflowExecutorInterface,
        registry: WorkflowRegistry
    ):
        """初始化工作流管理器。
        
        Args:
            orchestrator: 工作流编排器服务
            executor: 工作流执行器服务
            registry: 工作流注册表服务
        """
        self._orchestrator = orchestrator
        self._executor = executor
        self._registry = registry
    
    def create_workflow(self, workflow_id: str, name: str, config: Dict[str, Any]) -> IWorkflow:
        """创建新工作流。
        
        Args:
            workflow_id: 工作流的唯一标识符
            name: 工作流的人类可读名称
            config: 工作流配置
            
        Returns:
            创建的工作流实例
        """
        workflow = Workflow(workflow_id, name)
        
        # 基于提供的配置配置工作流
        self._configure_workflow(workflow, config)
        
        # 注册工作流
        self._registry.register_workflow(workflow_id, workflow)
        
        return workflow
    
    def execute_workflow(
        self, 
        workflow_id: str, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """执行工作流。
        
        Args:
            workflow_id: 要执行的工作流的ID
            initial_state: 工作流执行的初始状态
            config: 执行配置
            
        Returns:
            执行后的最终工作流状态
        """
        import uuid
        from src.interfaces.workflow.core import ExecutionContext
        from src.core.state.factories.state_factory import create_workflow_state
        
        # 从注册表获取工作流
        workflow = self._registry.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # 如果未提供，创建默认状态
        if initial_state is None:
            initial_state = create_workflow_state(
                workflow_id=workflow_id,
                workflow_name=workflow.name,
                input_text=""
            )
        
        # 使用必需的参数创建执行上下文
        if config is None:
            config = {}
        
        execution_context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=str(uuid.uuid4()),
            metadata=config.get("metadata", {}),
            config=config
        )
        
        # 执行工作流
        # 类型转换以解决接口不匹配问题
        result = self._executor.execute(workflow, initial_state, execution_context.__dict__ if execution_context else None)  # type: ignore
        return result  # type: ignore  # 假设返回的是兼容的状态对象
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流的状态。
        
        Args:
            workflow_id: 工作流的ID
            
        Returns:
            工作流状态信息
        """
        workflow = self._registry.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": "registered",
            "execution_count": 0 # WorkflowExecutor没有此方法，暂时设置为0
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有已注册的工作流。
        
        Returns:
            工作流信息列表
        """
        workflow_ids = self._registry.list_workflows()
        result = []
        for workflow_id in workflow_ids:
            workflow = self._registry.get_workflow(workflow_id)
            if workflow:
                result.append({
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "status": "registered"
                })
        return result
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流。
        
        Args:
            workflow_id: 要删除的工作流的ID
            
        Returns:
            如果工作流已删除则返回True，如果不存在则返回False
        """
        return self._registry.unregister_workflow(workflow_id)
    
    def _configure_workflow(self, workflow: Workflow, config: Dict[str, Any]) -> None:
        """根据提供的配置配置工作流。
        
        Args:
            workflow: 要配置的工作流
            config: 配置字典
        """
        # 添加节点
        for node_config in config.get("nodes", []):
            workflow.add_node(node_config)
        
        # 添加边
        for edge_config in config.get("edges", []):
            workflow.add_edge(edge_config)
        
        # 如果指定，设置入口点
        if "entry_point" in config:
            workflow.set_entry_point(config["entry_point"])