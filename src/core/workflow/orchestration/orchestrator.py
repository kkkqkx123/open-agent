"""工作流编排器

管理工作流的生命周期和编排。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime

from src.interfaces.workflow.core import IWorkflow, ExecutionContext
from src.interfaces.state import IWorkflowState
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.core.workflow.entities import Workflow, WorkflowExecution, ExecutionResult


logger = logging.getLogger(__name__)


class IWorkflowOrchestrator(ABC):
    """工作流编排器接口"""
    
    @abstractmethod
    def register_workflow_template(self, workflow_id: str, workflow: IWorkflow) -> None:
        """注册工作流模板"""
        pass
    
    @abstractmethod
    def get_workflow_template(self, workflow_id: str) -> Optional[IWorkflow]:
        """获取工作流模板"""
        pass
    
    @abstractmethod
    def execute_workflow(self, workflow_id: str, initial_state: IWorkflowState,
                        config: Optional[Dict[str, Any]] = None) -> IWorkflowState:
        """执行工作流"""
        pass
    
    @abstractmethod
    async def execute_workflow_async(self, workflow_id: str, initial_state: IWorkflowState,
                              config: Optional[Dict[str, Any]] = None) -> IWorkflowState:
        """异步执行工作流"""
        pass
    
    @abstractmethod
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行状态"""
        pass
    
    @abstractmethod
    def cleanup_execution(self, execution_id: str) -> None:
        """清理执行记录"""
        pass


class WorkflowOrchestrator(IWorkflowOrchestrator):
    """工作流编排器
    
    管理工作流的生命周期、编排多个工作流的执行。
    """
    
    def __init__(self, executor: Optional[IWorkflowExecutor] = None):
        """初始化编排器
        
        Args:
            executor: 工作流执行器
        """
        self.executor = executor
        self._workflow_templates: Dict[str, IWorkflow] = {}
        self._active_executions: Dict[str, WorkflowExecution] = {}

    def register_workflow_template(self, workflow_id: str, workflow: IWorkflow) -> None:
        """注册工作流模板
        
        Args:
            workflow_id: 工作流ID
            workflow: 工作流实例
        """
        self._workflow_templates[workflow_id] = workflow
        logger.info(f"注册工作流模板: {workflow_id}")

    def get_workflow_template(self, workflow_id: str) -> Optional[IWorkflow]:
        """获取工作流模板
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[IWorkflow]: 工作流实例，如果不存在则返回None
        """
        return self._workflow_templates.get(workflow_id)

    def list_workflow_templates(self) -> List[str]:
        """列出所有工作流模板
        
        Returns:
            List[str]: 工作流ID列表
        """
        return list(self._workflow_templates.keys())

    def execute_workflow(self, workflow_id: str, initial_state: IWorkflowState,
                        config: Optional[Dict[str, Any]] = None) -> IWorkflowState:
        """执行工作流
        
        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        workflow = self.get_workflow_template(workflow_id)
        if not workflow:
            raise ValueError(f"工作流模板不存在: {workflow_id}")
        
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            metadata=config.get("metadata", {}) if config else {},
            config=config or {}
        )
        
        # 记录执行开始
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.now()
        )
        self._active_executions[execution_id] = execution
        
        try:
            if not self.executor:
                raise ValueError("执行器未设置")
            
            # 执行工作流
            result_state = self.executor.execute(workflow, initial_state, context.__dict__ if context else None)
            
            # 更新执行状态
            execution.status = "completed" if result_state.get_data("error") is None else "failed"
            execution.completed_at = datetime.now()
            if result_state.get_data("error"):
                execution.error = result_state.get_data("error")
            
            logger.info(f"工作流执行完成: {workflow_id} ({execution_id})")
            return result_state
            
        except Exception as e:
            # 更新执行状态
            execution.status = "failed"
            execution.completed_at = datetime.now()
            execution.error = str(e)
            
            logger.error(f"工作流执行失败: {workflow_id} ({execution_id}): {e}")
            raise

    async def execute_workflow_async(self, workflow_id: str, initial_state: IWorkflowState,
                              config: Optional[Dict[str, Any]] = None) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        workflow = self.get_workflow_template(workflow_id)
        if not workflow:
            raise ValueError(f"工作流模板不存在: {workflow_id}")
        
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            metadata=config.get("metadata", {}) if config else {},
            config=config or {}
        )
        
        # 记录执行开始
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.now()
        )
        self._active_executions[execution_id] = execution
        
        try:
            if not self.executor:
                raise ValueError("执行器未设置")
            
            # 异步执行工作流
            result_state = await self.executor.execute_async(workflow, initial_state, context.__dict__ if context else None)
            
            # 更新执行状态
            execution.status = "completed" if result_state.get_data("error") is None else "failed"
            execution.completed_at = datetime.now()
            if result_state.get_data("error"):
                execution.error = result_state.get_data("error")
            
            logger.info(f"工作流异步执行完成: {workflow_id} ({execution_id})")
            return result_state
            
        except Exception as e:
            # 更新执行状态
            execution.status = "failed"
            execution.completed_at = datetime.now()
            execution.error = str(e)
            
            logger.error(f"工作流异步执行失败: {workflow_id} ({execution_id}): {e}")
            raise

    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            Optional[WorkflowExecution]: 执行状态，如果不存在则返回None
        """
        return self._active_executions.get(execution_id)

    def list_active_executions(self) -> List[WorkflowExecution]:
        """列出所有活跃的执行
        
        Returns:
            List[WorkflowExecution]: 执行列表
        """
        return list(self._active_executions.values())

    def cleanup_execution(self, execution_id: str) -> None:
        """清理执行记录
        
        Args:
            execution_id: 执行ID
        """
        if execution_id in self._active_executions:
            del self._active_executions[execution_id]
            logger.info(f"清理执行记录: {execution_id}")

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """获取编排器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "registered_workflows": len(self._workflow_templates),
            "active_executions": len(self._active_executions),
            "total_executions": len(self._active_executions),  # 简化实现
            "workflow_ids": list(self._workflow_templates.keys())
        }