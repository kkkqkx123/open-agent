"""工作流执行器

提供工作流的核心执行功能。
"""

import logging
import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from abc import ABC, abstractmethod

from ..strategies.strategy_base import IExecutionStrategy
from ..modes.mode_base import IExecutionMode
from .execution_context import ExecutionContext, ExecutionResult
from .node_executor import INodeExecutor, NodeExecutor

if TYPE_CHECKING:
    from src.interfaces import IWorkflowState
    from src.interfaces.workflow.core import IWorkflow
    from src.core.workflow.workflow_instance import WorkflowInstance

logger = logging.getLogger(__name__)


class IWorkflowExecutor(ABC):
    """工作流执行器接口"""
    
    @abstractmethod
    def execute(
        self, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> ExecutionResult:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def execute_async(
        self, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> ExecutionResult:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    def set_strategy(self, strategy: IExecutionStrategy) -> None:
        """设置执行策略
        
        Args:
            strategy: 执行策略
        """
        pass
    
    @abstractmethod
    def set_mode(self, mode: IExecutionMode) -> None:
        """设置执行模式
        
        Args:
            mode: 执行模式
        """
        pass
    
    @abstractmethod
    def set_node_executor(self, executor: INodeExecutor) -> None:
        """设置节点执行器
        
        Args:
            executor: 节点执行器
        """
        pass


class WorkflowExecutor(IWorkflowExecutor):
    """工作流执行器实现
    
    提供工作流的核心执行功能，支持不同的执行策略和模式。
    """
    
    def __init__(
        self, 
        strategy: Optional[IExecutionStrategy] = None,
        mode: Optional[IExecutionMode] = None,
        node_executor: Optional[INodeExecutor] = None
    ):
        """初始化工作流执行器
        
        Args:
            strategy: 执行策略
            mode: 执行模式
            node_executor: 节点执行器
        """
        self._strategy = strategy
        self._mode = mode
        self._node_executor = node_executor or NodeExecutor(mode)
        
        logger.debug(f"工作流执行器初始化完成，策略: {strategy.get_strategy_name() if strategy else '默认'}")
    
    def execute(
        self, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> ExecutionResult:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"开始执行工作流: {workflow.config.name}")
            
            # 标记开始执行
            context.mark_started()
            
            # 验证输入
            self._validate_inputs(workflow, context)
            
            # 使用执行策略执行工作流
            if self._strategy:
                result = self._strategy.execute(self, workflow, context)
            else:
                result = self._default_execute(workflow, context)
            
            # 设置执行时间
            result.execution_time = time.time() - start_time
            result.start_time = context.start_time
            result.end_time = context.end_time
            
            # 标记完成状态
            if result.success:
                context.mark_completed()
            else:
                context.mark_failed()
            
            logger.debug(f"工作流执行完成: {workflow.config.name}, 耗时: {result.execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工作流执行失败: {str(e)}"
            logger.error(error_msg)
            
            # 标记失败状态
            context.mark_failed()
            
            # 创建错误结果
            result = self._create_error_result(e, workflow, context)
            result.execution_time = execution_time
            result.start_time = context.start_time
            result.end_time = context.end_time
            
            return result
    
    async def execute_async(
        self, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> ExecutionResult:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"开始异步执行工作流: {workflow.config.name}")
            
            # 标记开始执行
            context.mark_started()
            
            # 验证输入
            self._validate_inputs(workflow, context)
            
            # 使用执行策略执行工作流
            if self._strategy:
                # 检查策略是否支持异步
                if hasattr(self._strategy, 'execute_async'):
                    result = await self._strategy.execute_async(self, workflow, context)  # type: ignore
                else:
                    # 在线程池中执行同步策略
                    import asyncio
                    import functools
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, 
                        functools.partial(self._strategy.execute, self, workflow, context)
                    )
            else:
                result = await self._default_execute_async(workflow, context)
            
            # 设置执行时间
            result.execution_time = time.time() - start_time
            result.start_time = context.start_time
            result.end_time = context.end_time
            
            # 标记完成状态
            if result.success:
                context.mark_completed()
            else:
                context.mark_failed()
            
            logger.debug(f"工作流异步执行完成: {workflow.config.name}, 耗时: {result.execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工作流异步执行失败: {str(e)}"
            logger.error(error_msg)
            
            # 标记失败状态
            context.mark_failed()
            
            # 创建错误结果
            result = self._create_error_result(e, workflow, context)
            result.execution_time = execution_time
            result.start_time = context.start_time
            result.end_time = context.end_time
            
            return result
    
    def set_strategy(self, strategy: IExecutionStrategy) -> None:
        """设置执行策略
        
        Args:
            strategy: 执行策略
        """
        self._strategy = strategy
        logger.debug(f"工作流执行器策略已设置为: {strategy.get_strategy_name()}")
    
    def set_mode(self, mode: IExecutionMode) -> None:
        """设置执行模式
        
        Args:
            mode: 执行模式
        """
        self._mode = mode
        self._node_executor.set_mode(mode)
        logger.debug(f"工作流执行器模式已设置为: {mode.get_mode_name()}")
    
    def set_node_executor(self, executor: INodeExecutor) -> None:
        """设置节点执行器
        
        Args:
            executor: 节点执行器
        """
        self._node_executor = executor
        logger.debug("工作流执行器的节点执行器已更新")
    
    def _validate_inputs(
        self, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> None:
        """验证输入参数
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Raises:
            ValueError: 输入参数无效
        """
        if not workflow:
            raise ValueError("工作流不能为空")
        if not context:
            raise ValueError("执行上下文不能为空")
        if not workflow.config.entry_point:
            raise ValueError("工作流未设置入口点")
    
    def _default_execute(
        self, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> ExecutionResult:
        """默认工作流执行逻辑
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 获取初始数据
        initial_data = context.get_config("initial_data")
        
        # 执行工作流
        final_state = workflow.run(initial_data, **context.config)
        
        # 创建执行结果
        return ExecutionResult(
            success=True,
            result=final_state if isinstance(final_state, dict) else (final_state.to_dict() if hasattr(final_state, 'to_dict') else {}),
            metadata={
                "workflow_name": workflow.config.name,
                "workflow_id": workflow.config.name,  # 使用name作为id
                "execution_id": context.execution_id,
                "total_nodes": len(workflow.config.nodes) if hasattr(workflow.config, 'nodes') else 0
            },
            strategy_name=self._strategy.get_strategy_name() if self._strategy else "default"
        )
    
    async def _default_execute_async(
        self, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> ExecutionResult:
        """默认异步工作流执行逻辑
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 获取初始数据
        initial_data = context.get_config("initial_data")
        
        # 异步执行工作流
        if hasattr(workflow, 'run_async'):
            final_state = await workflow.run_async(initial_data, **context.config)
        else:
            # 在线程池中执行同步工作流
            import asyncio
            import functools
            loop = asyncio.get_event_loop()
            final_state = await loop.run_in_executor(
                None, 
                functools.partial(workflow.run, initial_data, **context.config)
            )
        
        # 创建执行结果
        return ExecutionResult(
            success=True,
            result=final_state if isinstance(final_state, dict) else (final_state.to_dict() if hasattr(final_state, 'to_dict') else {}),
            metadata={
                "workflow_name": workflow.config.name,
                "workflow_id": workflow.config.name,  # 使用name作为id
                "execution_id": context.execution_id,
                "total_nodes": len(workflow.config.nodes) if hasattr(workflow.config, 'nodes') else 0,
                "execution_mode": "async"
            },
            strategy_name=self._strategy.get_strategy_name() if self._strategy else "default"
        )
    
    def _create_error_result(
        self, 
        error: Exception, 
        workflow: 'WorkflowInstance', 
        context: ExecutionContext
    ) -> ExecutionResult:
        """创建错误结果
        
        Args:
            error: 异常
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 错误结果
        """
        return ExecutionResult(
            success=False,
            error=str(error),
            metadata={
                "workflow_name": workflow.config.name,
                "workflow_id": workflow.config.name,  # 使用name作为id
                "execution_id": context.execution_id,
                "error_type": type(error).__name__,
                "error_timestamp": time.time()
            },
            strategy_name=self._strategy.get_strategy_name() if self._strategy else "default"
        )