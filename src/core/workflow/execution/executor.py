"""统一工作流执行器

整合所有执行逻辑，提供统一的工作流执行接口。
"""

import logging
import uuid
from typing import Dict, Any, Optional, AsyncIterator, List
from datetime import datetime

from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state import IWorkflowState
from src.core.workflow.execution.core.execution_context import ExecutionContext
from src.core.workflow.execution.core.node_executor import INodeExecutor, NodeExecutor
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.core.workflow.core.builder import WorkflowBuilder
from src.core.workflow.core.validator import WorkflowValidator

logger = logging.getLogger(__name__)


class WorkflowExecutor(IWorkflowExecutor):
    """统一工作流执行器
    
    整合所有执行逻辑，提供统一的同步和异步执行接口。
    移除了WorkflowInstanceCoordinator中的重复执行逻辑。
    """
    
    def __init__(
        self,
        node_executor: Optional[INodeExecutor] = None,
        workflow_builder: Optional[WorkflowBuilder] = None,
        workflow_validator: Optional[WorkflowValidator] = None
    ):
        """初始化统一工作流执行器
        
        Args:
            node_executor: 节点执行器
            workflow_builder: 工作流构建器
            workflow_validator: 工作流验证器
        """
        self.node_executor = node_executor or NodeExecutor()
        self.workflow_builder = workflow_builder or WorkflowBuilder()
        self.workflow_validator = workflow_validator or WorkflowValidator()
        
        # 执行记录管理
        self._active_executions: Dict[str, ExecutionContext] = {}
        
        logger.debug("统一工作流执行器初始化完成")
    
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
        start_time = datetime.now()
        
        try:
            logger.debug(f"开始执行工作流: {workflow.workflow_id} ({execution_id})")
            
            # 创建执行上下文
            exec_context = self._create_execution_context(workflow, execution_id, context)
            
            # 验证工作流
            self._validate_workflow(workflow)
            
            # 确保工作流已编译
            self._ensure_workflow_compiled(workflow)
            
            # 执行工作流
            result_state = self._execute_with_compiled_graph(workflow, initial_state, context)
            
            # 更新执行状态
            exec_context.mark_completed()
            
            # 记录执行完成
            self._cleanup_execution(execution_id)
            
            logger.info(f"工作流执行完成: {workflow.workflow_id} ({execution_id})")
            return result_state
            
        except Exception as e:
            # 更新执行状态为失败
            if execution_id in self._active_executions:
                self._active_executions[execution_id].mark_failed()
            
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
        start_time = datetime.now()
        
        try:
            logger.debug(f"开始异步执行工作流: {workflow.workflow_id} ({execution_id})")
            
            # 创建执行上下文
            exec_context = self._create_execution_context(workflow, execution_id, context)
            
            # 验证工作流
            self._validate_workflow(workflow)
            
            # 确保工作流已编译
            self._ensure_workflow_compiled(workflow)
            
            # 异步执行工作流
            result_state = await self._execute_with_compiled_graph_async(workflow, initial_state, context)
            
            # 更新执行状态
            exec_context.mark_completed()
            
            # 记录执行完成
            self._cleanup_execution(execution_id)
            
            logger.info(f"工作流异步执行完成: {workflow.workflow_id} ({execution_id})")
            return result_state
            
        except Exception as e:
            # 更新执行状态为失败
            if execution_id in self._active_executions:
                self._active_executions[execution_id].mark_failed()
            
            logger.error(f"工作流异步执行失败: {workflow.workflow_id} ({execution_id}): {e}")
            raise
    
    def execute_stream(
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
        # 默认实现：不生成任何事件
        return
        yield  # type: ignore
    
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
        # 默认实现：不生成任何事件
        return
        yield  # type: ignore
    
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
            "execution_time": context.execution_time
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
            "total_executions": len(self._active_executions),  # 简化实现
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
    
    def _validate_workflow(self, workflow: IWorkflow) -> None:
        """验证工作流
        
        Args:
            workflow: 工作流实例
            
        Raises:
            WorkflowValidationError: 验证失败
        """
        try:
            # 获取工作流配置
            config = getattr(workflow, 'config', None)
            if config is None:
                logger.warning("工作流未包含config属性，跳过验证")
                return
                
            # 使用配置验证器验证工作流
            issues = self.workflow_validator.validate_config_object(config)
            
            # 检查是否有错误
            errors = [issue for issue in issues if issue.severity.value == "error"]
            if errors:
                error_messages = [error.message for error in errors]
                from src.core.common.exceptions.workflow import WorkflowValidationError
                raise WorkflowValidationError(f"工作流验证失败: {'; '.join(error_messages)}")
                
        except Exception as e:
            if "WorkflowValidationError" in str(type(e)):
                raise
            logger.warning(f"工作流验证异常: {e}")
    
    def _ensure_workflow_compiled(self, workflow: IWorkflow) -> None:
        """确保工作流已编译
        
        Args:
            workflow: 工作流实例
            
        Raises:
            WorkflowConfigError: 编译失败
        """
        if not workflow.graph:
            try:
                # 使用构建器编译图
                self.workflow_builder.build_and_set_graph(workflow)  # type: ignore
            except Exception as e:
                from src.core.common.exceptions.workflow import WorkflowConfigError
                raise WorkflowConfigError(f"工作流图编译失败: {e}") from e
    
    def _execute_with_compiled_graph(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """使用编译的图执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # 准备运行配置
            run_config = context or {}
            if "recursion_limit" not in run_config:
                run_config["recursion_limit"] = 10
            
            # 使用编译的图执行
            compiled_graph = workflow.graph
            if not compiled_graph:
                raise ValueError("工作流图未编译")
            
            # 准备初始数据
            initial_data = initial_state.values if hasattr(initial_state, 'values') else {}
            
            # 执行图
            result = compiled_graph.invoke(initial_data, config=run_config)  # type: ignore
            
            # 创建结果状态
            from src.core.state.implementations.workflow_state import WorkflowState
            return WorkflowState(
                id=execution_id,
                data=result if isinstance(result, dict) else {},
                status="completed",
                workflow_id=workflow.workflow_id,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"图执行失败: {e}")
            from src.core.state.implementations.workflow_state import WorkflowState
            return WorkflowState(
                id=execution_id,
                data={},
                status="failed",
                workflow_id=workflow.workflow_id,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_with_compiled_graph_async(
        self,
        workflow: IWorkflow,
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """使用编译的图异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # 准备运行配置
            run_config = context or {}
            if "recursion_limit" not in run_config:
                run_config["recursion_limit"] = 10
            
            # 使用编译的图异步执行
            compiled_graph = workflow.graph
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
                id=execution_id,
                data=result if isinstance(result, dict) else {},
                status="completed",
                workflow_id=workflow.workflow_id,
                execution_time=(datetime.now() - start_time).total_seconds(),
                execution_mode="async"
            )
            
        except Exception as e:
            logger.error(f"异步图执行失败: {e}")
            from src.core.state.implementations.workflow_state import WorkflowState
            return WorkflowState(
                id=execution_id,
                data={},
                status="failed",
                workflow_id=workflow.workflow_id,
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
