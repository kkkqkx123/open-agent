"""统一工作流执行器

基于新架构原则，专注于工作流执行逻辑，不包含验证和管理功能。
"""

from src.interfaces.dependency_injection import get_logger
import uuid
from typing import Dict, Any, Optional, AsyncIterator, List
from datetime import datetime
from enum import Enum

from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state import IWorkflowState
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.core.workflow.core.builder import WorkflowBuilder

logger = get_logger(__name__)


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionContext:
    """执行上下文"""
    
    def __init__(
        self,
        workflow_id: str,
        execution_id: str,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化执行上下文
        
        Args:
            workflow_id: 工作流ID
            execution_id: 执行ID
            config: 执行配置
            metadata: 元数据
        """
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.config = config or {}
        self.metadata = metadata or {}
        self.status = ExecutionStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error: Optional[str] = None
    
    def mark_started(self) -> None:
        """标记为开始执行"""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()
    
    def mark_completed(self) -> None:
        """标记为完成"""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = datetime.now()
    
    def mark_failed(self, error: Optional[str] = None) -> None:
        """标记为失败"""
        self.status = ExecutionStatus.FAILED
        self.end_time = datetime.now()
        self.error = error
    
    def mark_cancelled(self) -> None:
        """标记为取消"""
        self.status = ExecutionStatus.CANCELLED
        self.end_time = datetime.now()
    
    @property
    def execution_time(self) -> float:
        """获取执行时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0


class WorkflowExecutor(IWorkflowExecutor):
    """统一工作流执行器
    
    专注于工作流执行逻辑，提供统一的同步和异步执行接口。
    不包含验证和管理功能，这些由 WorkflowManager 负责。
    """
    
    def __init__(self, workflow_builder: Optional[WorkflowBuilder] = None):
        """初始化工作流执行器
        
        Args:
            workflow_builder: 工作流构建器
        """
        self.workflow_builder = workflow_builder or WorkflowBuilder()
        
        # 执行记录管理
        self._active_executions: Dict[str, ExecutionContext] = {}
        
        logger.debug("工作流执行器初始化完成")
    
    def execute(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        
        try:
            logger.debug(f"开始执行工作流: {workflow.workflow_id} ({execution_id})")
            
            # 创建执行上下文
            exec_context = self._create_execution_context(workflow, execution_id, context)
            
            # 确保工作流已编译
            self._ensure_workflow_compiled(workflow)
            
            # 执行工作流
            result_state = self._execute_with_compiled_graph(workflow, initial_state, context, execution_id)
            
            # 更新执行状态
            exec_context.mark_completed()
            
            # 记录执行完成
            self._cleanup_execution(execution_id)
            
            logger.info(f"工作流执行完成: {workflow.workflow_id} ({execution_id})")
            return result_state
            
        except Exception as e:
            # 更新执行状态为失败
            if execution_id in self._active_executions:
                self._active_executions[execution_id].mark_failed(str(e))
            
            logger.error(f"工作流执行失败: {workflow.workflow_id} ({execution_id}): {e}")
            raise
    
    async def execute_async(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        
        try:
            logger.debug(f"开始异步执行工作流: {workflow.workflow_id} ({execution_id})")
            
            # 创建执行上下文
            exec_context = self._create_execution_context(workflow, execution_id, context)
            
            # 确保工作流已编译
            self._ensure_workflow_compiled(workflow)
            
            # 异步执行工作流
            result_state = await self._execute_with_compiled_graph_async(
                workflow, initial_state, context, execution_id
            )
            
            # 更新执行状态
            exec_context.mark_completed()
            
            # 记录执行完成
            self._cleanup_execution(execution_id)
            
            logger.info(f"工作流异步执行完成: {workflow.workflow_id} ({execution_id})")
            return result_state
            
        except Exception as e:
            # 更新执行状态为失败
            if execution_id in self._active_executions:
                self._active_executions[execution_id].mark_failed(str(e))
            
            logger.error(f"工作流异步执行失败: {workflow.workflow_id} ({execution_id}): {e}")
            raise
    
    async def execute_stream(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        logger.debug(f"开始流式执行工作流: {workflow.workflow_id}")
        
        execution_id = str(uuid.uuid4())
        exec_context = self._create_execution_context(workflow, execution_id, context)
        
        try:
            # 确保工作流已编译
            self._ensure_workflow_compiled(workflow)
            
            # 发送开始事件
            yield {
                "type": "execution_start",
                "execution_id": execution_id,
                "workflow_id": workflow.workflow_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 执行工作流（简化实现，实际应该支持真正的流式执行）
            result_state = self._execute_with_compiled_graph(workflow, initial_state, context, execution_id)
            
            # 发送完成事件
            result_data = {}
            if hasattr(result_state, 'values'):
                result_data = result_state.values
            elif hasattr(result_state, 'get'):
                result_data = result_state.get('data', {})
                
            yield {
                "type": "execution_complete",
                "execution_id": execution_id,
                "workflow_id": workflow.workflow_id,
                "timestamp": datetime.now().isoformat(),
                "result": result_data
            }
            
            exec_context.mark_completed()
            self._cleanup_execution(execution_id)
            
        except Exception as e:
            exec_context.mark_failed(str(e))
            self._cleanup_execution(execution_id)
            
            # 发送错误事件
            yield {
                "type": "execution_error",
                "execution_id": execution_id,
                "workflow_id": workflow.workflow_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def execute_stream_async(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        logger.debug(f"开始异步流式执行工作流: {workflow.workflow_id}")
        
        execution_id = str(uuid.uuid4())
        exec_context = self._create_execution_context(workflow, execution_id, context)
        
        try:
            # 确保工作流已编译
            self._ensure_workflow_compiled(workflow)
            
            # 发送开始事件
            yield {
                "type": "execution_start",
                "execution_id": execution_id,
                "workflow_id": workflow.workflow_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 异步执行工作流
            result_state = await self._execute_with_compiled_graph_async(
                workflow, initial_state, context, execution_id
            )
            
            # 发送完成事件
            result_data = {}
            if hasattr(result_state, 'values'):
                result_data = result_state.values
            elif hasattr(result_state, 'get'):
                result_data = result_state.get('data', {})
                
            yield {
                "type": "execution_complete",
                "execution_id": execution_id,
                "workflow_id": workflow.workflow_id,
                "timestamp": datetime.now().isoformat(),
                "result": result_data
            }
            
            exec_context.mark_completed()
            self._cleanup_execution(execution_id)
            
        except Exception as e:
            exec_context.mark_failed(str(e))
            self._cleanup_execution(execution_id)
            
            # 发送错误事件
            yield {
                "type": "execution_error",
                "execution_id": execution_id,
                "workflow_id": workflow.workflow_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            Dict[str, Any]: 执行状态信息
        """
        if execution_id not in self._active_executions:
            return {
                "execution_id": execution_id,
                "status": "not_found"
            }
        
        context = self._active_executions[execution_id]
        return {
            "execution_id": execution_id,
            "workflow_id": context.workflow_id,
            "status": context.status.value,
            "start_time": context.start_time.isoformat() if context.start_time else None,
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "execution_time": context.execution_time,
            "error": context.error
        }
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            bool: 是否成功取消
        """
        if execution_id not in self._active_executions:
            return False
        
        context = self._active_executions[execution_id]
        context.mark_cancelled()
        
        # 清理执行记录
        self._cleanup_execution(execution_id)
        
        logger.info(f"取消执行: {execution_id}")
        return True
    
    def list_active_executions(self) -> List[Dict[str, Any]]:
        """列出所有活跃的执行
        
        Returns:
            List[Dict[str, Any]]: 执行状态列表
        """
        return [
            {
                "execution_id": execution_id,
                "workflow_id": context.workflow_id,
                "status": context.status.value,
                "start_time": context.start_time.isoformat() if context.start_time else None,
                "execution_time": context.execution_time
            }
            for execution_id, context in self._active_executions.items()
        ]
    
    def get_executor_statistics(self) -> Dict[str, Any]:
        """获取执行器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "active_executions": len(self._active_executions),
            "execution_ids": list(self._active_executions.keys())
        }
    
    def _create_execution_context(
        self,
        workflow: IWorkflow,
        execution_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """创建执行上下文
        
        Args:
            workflow: 工作流实例
            execution_id: 执行ID
            context: 执行配置
            
        Returns:
            ExecutionContext: 执行上下文
        """
        exec_context = ExecutionContext(
            workflow_id=workflow.workflow_id,
            execution_id=execution_id,
            config=context or {},
            metadata={
                "workflow_name": workflow.name,
                "workflow_version": workflow.version,
                "executor_timestamp": datetime.now().isoformat()
            }
        )
        
        # 记录执行开始
        self._active_executions[execution_id] = exec_context
        exec_context.mark_started()
        
        return exec_context
    
    def _ensure_workflow_compiled(self, workflow: IWorkflow) -> None:
        """确保工作流已编译
        
        Args:
            workflow: 工作流实例
            
        Raises:
            ValueError: 编译失败
        """
        if not workflow.compiled_graph:
            try:
                # 使用构建器编译图
                self.workflow_builder.build_and_set_graph(workflow)  # type: ignore
            except Exception as e:
                logger.error(f"工作流图编译失败: {e}")
                raise ValueError(f"工作流图编译失败: {e}") from e
    
    def _execute_with_compiled_graph(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> IWorkflowState:
        """使用编译的图执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            execution_id: 执行ID
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        start_time = datetime.now()
        exec_id = execution_id or str(uuid.uuid4())
        
        try:
            # 准备运行配置
            run_config = context or {}
            if "recursion_limit" not in run_config:
                run_config["recursion_limit"] = 10
            
            # 使用编译的图执行
            compiled_graph = workflow.compiled_graph
            if not compiled_graph:
                raise ValueError("工作流图未编译")
            
            # 准备初始数据
            initial_data = initial_state.values if hasattr(initial_state, 'values') else {}
            
            # 执行图
            result = compiled_graph.invoke(initial_data, config=run_config)  # type: ignore
            
            # 创建结果状态
            from src.core.state.implementations.workflow_state import WorkflowState
            return WorkflowState(
                workflow_id=workflow.workflow_id,
                execution_id=exec_id,
                status="completed",
                data=result if isinstance(result, dict) else {},
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"图执行失败: {e}")
            from src.core.state.implementations.workflow_state import WorkflowState
            return WorkflowState(
                workflow_id=workflow.workflow_id,
                execution_id=exec_id,
                status="failed",
                data={},
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_with_compiled_graph_async(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> IWorkflowState:
        """使用编译的图异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            execution_id: 执行ID
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        start_time = datetime.now()
        exec_id = execution_id or str(uuid.uuid4())
        
        try:
            # 准备运行配置
            run_config = context or {}
            if "recursion_limit" not in run_config:
                run_config["recursion_limit"] = 10
            
            # 使用编译的图异步执行
            compiled_graph = workflow.compiled_graph
            if not compiled_graph:
                raise ValueError("工作流图未编译")
            
            # 准备初始数据
            initial_data = initial_state.values if hasattr(initial_state, 'values') else {}
            
            # 异步执行图
            if hasattr(compiled_graph, 'ainvoke'):
                result = await compiled_graph.ainvoke(initial_data, config=run_config)  # type: ignore
            else:
                # 如果不支持异步，使用同步方式
                import asyncio
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    compiled_graph.invoke,  # type: ignore
                    initial_data,
                    run_config
                )
            
            # 创建结果状态
            from src.core.state.implementations.workflow_state import WorkflowState
            return WorkflowState(
                workflow_id=workflow.workflow_id,
                execution_id=exec_id,
                status="completed",
                data=result if isinstance(result, dict) else {},
                execution_time=(datetime.now() - start_time).total_seconds(),
                execution_mode="async"
            )
            
        except Exception as e:
            logger.error(f"异步图执行失败: {e}")
            from src.core.state.implementations.workflow_state import WorkflowState
            return WorkflowState(
                workflow_id=workflow.workflow_id,
                execution_id=exec_id,
                status="failed",
                data={},
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                execution_mode="async"
            )
    
    def _cleanup_execution(self, execution_id: str) -> None:
        """清理执行记录
        
        Args:
            execution_id: 执行ID
        """
        if execution_id in self._active_executions:
            del self._active_executions[execution_id]
            logger.debug(f"清理执行记录: {execution_id}")


# 创建默认执行器实例
default_executor = WorkflowExecutor()


def execute_workflow(
    workflow: IWorkflow,
    initial_state: IWorkflowState,
    context: Optional[Dict[str, Any]] = None
) -> IWorkflowState:
    """便捷函数：执行工作流
    
    Args:
        workflow: 工作流实例
        initial_state: 初始状态
        context: 执行配置
        
    Returns:
        IWorkflowState: 执行结果状态
    """
    return default_executor.execute(workflow, initial_state, context)


async def execute_workflow_async(
    workflow: IWorkflow,
    initial_state: IWorkflowState,
    context: Optional[Dict[str, Any]] = None
) -> IWorkflowState:
    """便捷函数：异步执行工作流
    
    Args:
        workflow: 工作流实例
        initial_state: 初始状态
        context: 执行配置
        
    Returns:
        IWorkflowState: 执行结果状态
    """
    return await default_executor.execute_async(workflow, initial_state, context)