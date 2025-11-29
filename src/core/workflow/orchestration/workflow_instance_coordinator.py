"""工作流实例协调器 - 改造自 WorkflowOrchestrator

专注于单个工作流实例的协调，充分利用现有Core层组件。
"""

from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime

from src.interfaces.workflow.core import IWorkflow, ExecutionContext
from src.interfaces.state import IWorkflowState
from src.core.workflow.entities import WorkflowExecution
from src.core.state.implementations.workflow_state import WorkflowState
from src.core.workflow.execution.core.workflow_executor import WorkflowExecutor
from src.core.workflow.execution.core.execution_context import ExecutionResult
from src.core.workflow.management.workflow_validator import WorkflowValidator, ValidationSeverity
from src.core.workflow.execution.utils.next_nodes_resolver import NextNodesResolver


logger = logging.getLogger(__name__)


class WorkflowInstanceCoordinator:
    """工作流实例协调器
    
    专注于单个工作流实例的协调，整合现有的Core层组件。
    改造自 WorkflowOrchestrator，职责更加明确。
    """
    
    def __init__(
        self,
        workflow: IWorkflow,
        executor: Optional[WorkflowExecutor] = None,
        execution_manager: Optional[Any] = None
    ):
        """初始化工作流实例协调器
        
        Args:
            workflow: 工作流实例
            executor: 工作流执行器（可选，默认创建）
            execution_manager: 执行管理器（可选，已废弃，保留以兼容）
        """
        self.workflow = workflow
        self.executor = executor or WorkflowExecutor()
        # execution_manager 已废弃，不再使用
        self.execution_manager = execution_manager
        
        # 初始化其他现有组件
        self.validator = WorkflowValidator()
        self.next_nodes_resolver = NextNodesResolver()
        
        # 执行记录管理
        self._active_executions: Dict[str, WorkflowExecution] = {}
        
        logger.debug(f"工作流实例协调器初始化完成: {workflow.workflow_id}")
    
    def execute_workflow(
        self, 
        initial_state: IWorkflowState,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """执行工作流 - 使用现有的执行管理器
        
        Args:
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        
        # 创建执行上下文
        context = ExecutionContext(
            workflow_id=self.workflow.workflow_id,
            execution_id=execution_id,
            config=config or {
                "initial_data": initial_state.values if hasattr(initial_state, 'values') else {},
                "coordinator_timestamp": datetime.now().isoformat()
            },
            metadata={}
        )
        
        # 记录执行开始
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=self.workflow.workflow_id,
            status="running",
            started_at=datetime.now()
        )
        self._active_executions[execution_id] = execution
        
        try:
            # 使用现有的执行管理器执行工作流
            initial_data = initial_state.values if hasattr(initial_state, 'values') else {}
            
            # 检查工作流是否有编译的图
            if not hasattr(self.workflow, 'compiled_graph') or not self.workflow.compiled_graph:
                raise ValueError("工作流图未编译，无法执行")
            
            # 直接使用编译的图执行
            result_state = self._execute_with_compiled_graph(initial_data, config)
            
            # 更新执行状态
            status = result_state.get_field("status", "completed")
            execution.status = status
            execution.completed_at = datetime.now()
            if status == "failed":
                error_info = result_state.get_field("error", "未知错误")
                execution.error = error_info
            
            logger.info(f"工作流执行完成: {self.workflow.workflow_id} ({execution_id})")
            
            return result_state
            
        except Exception as e:
            # 更新执行状态
            execution.status = "failed"
            execution.completed_at = datetime.now()
            execution.error = str(e)
            
            logger.error(f"工作流执行失败: {self.workflow.workflow_id} ({execution_id}): {e}")
            raise
    
    async def execute_workflow_async(
        self, 
        initial_state: IWorkflowState,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """异步执行工作流 - 使用现有的执行管理器
        
        Args:
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        
        # 创建执行上下文
        context = ExecutionContext(
            workflow_id=self.workflow.workflow_id,
            execution_id=execution_id,
            config=config or {
                "initial_data": initial_state.values if hasattr(initial_state, 'values') else {},
                "coordinator_timestamp": datetime.now().isoformat()
            },
            metadata={}
        )
        
        # 记录执行开始
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=self.workflow.workflow_id,
            status="running",
            started_at=datetime.now()
        )
        self._active_executions[execution_id] = execution
        
        try:
            # 使用现有的执行管理器异步执行工作流
            initial_data = initial_state.values if hasattr(initial_state, 'values') else {}
            
            # 检查工作流是否有编译的图
            compiled_graph = getattr(self.workflow, 'compiled_graph', None)
            if not compiled_graph:
                raise ValueError("工作流图未编译，无法执行")
            
            # 直接使用编译的图执行，绕过已废弃的 run_async() 方法
            result_state = await self._execute_with_compiled_graph_async(initial_data, config)
            
            # 更新执行状态
            status = result_state.get_field("status", "completed")
            execution.status = status
            execution.completed_at = datetime.now()
            if status == "failed":
                error_info = result_state.get_field("error", "未知错误")
                execution.error = error_info
            
            logger.info(f"工作流异步执行完成: {self.workflow.workflow_id} ({execution_id})")
            
            return result_state
            
        except Exception as e:
            # 更新执行状态
            execution.status = "failed"
            execution.completed_at = datetime.now()
            execution.error = str(e)
            
            logger.error(f"工作流异步执行失败: {self.workflow.workflow_id} ({execution_id}): {e}")
            raise
    
    def get_next_nodes(self, node_id: str, state: Any, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点 - 使用现有的导航解析器
        
        Args:
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        return self.next_nodes_resolver.get_next_nodes(self.workflow, node_id, state, config)
    
    async def get_next_nodes_async(self, node_id: str, state: Any, config: Dict[str, Any]) -> List[str]:
        """异步获取下一个节点 - 使用现有的导航解析器
        
        Args:
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        return await self.next_nodes_resolver.get_next_nodes_async(self.workflow, node_id, state, config)
    
    def validate_workflow(self) -> List[str]:
        """验证工作流 - 使用现有的验证器
        
        Returns:
            List[str]: 验证错误列表
        """
        # 尝试使用工作流本身的验证方法
        try:
            validation_errors = self.workflow.validate()
            if validation_errors:
                return validation_errors
        except Exception as e:
            logger.warning(f"工作流验证异常: {e}")
        
        return []
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            Optional[WorkflowExecution]: 执行状态
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
    
    def get_coordinator_stats(self) -> Dict[str, Any]:
        """获取协调器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "workflow_id": self.workflow.workflow_id,
            "workflow_name": self.workflow.name,
            "active_executions": len(self._active_executions),
            "total_executions": len(self._active_executions),  # 简化实现
            "execution_ids": list(self._active_executions.keys())
        }
    
    def _execute_with_compiled_graph(
        self,
        initial_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """使用编译的图直接执行工作流
        
        Args:
            initial_data: 初始数据
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # 准备运行配置
            run_config = config or {}
            if "recursion_limit" not in run_config:
                run_config["recursion_limit"] = 10
            
            # 使用编译的图执行
            compiled_graph = getattr(self.workflow, 'compiled_graph', None)
            if not compiled_graph:
                raise ValueError("工作流图未编译")
            result = compiled_graph.invoke(initial_data, config=run_config)
            
            # 创建结果状态
            return WorkflowState(
                id=execution_id,
                data=result if isinstance(result, dict) else {},
                status="completed",
                workflow_id=self.workflow.workflow_id,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"图执行失败: {e}")
            return WorkflowState(
                id=execution_id,
                data={},
                status="failed",
                workflow_id=self.workflow.workflow_id,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_with_compiled_graph_async(
        self,
        initial_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """使用编译的图异步执行工作流
        
        Args:
            initial_data: 初始数据
            config: 执行配置
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # 准备运行配置
            run_config = config or {}
            if "recursion_limit" not in run_config:
                run_config["recursion_limit"] = 10
            
            # 使用编译的图异步执行
            compiled_graph = getattr(self.workflow, 'compiled_graph', None)
            if not compiled_graph:
                raise ValueError("工作流图未编译")
                
            if hasattr(compiled_graph, 'ainvoke'):
                result = await compiled_graph.ainvoke(initial_data, config=run_config)
            else:
                # 如果不支持异步，使用同步方式
                import asyncio
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    compiled_graph.invoke,
                    initial_data,
                    run_config
                )
            
            # 创建结果状态
            return WorkflowState(
                id=execution_id,
                data=result if isinstance(result, dict) else {},
                status="completed",
                workflow_id=self.workflow.workflow_id,
                execution_time=(datetime.now() - start_time).total_seconds(),
                execution_mode="async"
            )
            
        except Exception as e:
            logger.error(f"异步图执行失败: {e}")
            return WorkflowState(
                id=execution_id,
                data={},
                status="failed",
                workflow_id=self.workflow.workflow_id,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                execution_mode="async"
            )