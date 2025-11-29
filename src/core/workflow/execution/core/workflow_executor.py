"""工作流执行器

提供工作流的核心执行功能。
"""

import logging
import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING, AsyncIterator
from abc import ABC, abstractmethod
import uuid

from ..strategies.strategy_base import IExecutionStrategy
from ..modes.mode_base import IExecutionMode
from .execution_context import ExecutionContext, ExecutionResult
from .node_executor import INodeExecutor, NodeExecutor
from src.interfaces.workflow.execution import IWorkflowExecutor

if TYPE_CHECKING:
    from src.interfaces import IWorkflowState
    from src.interfaces.workflow.core import IWorkflow
    from core.workflow.workflow_instance import WorkflowInstance

logger = logging.getLogger(__name__)


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
        workflow: 'IWorkflow', 
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
        start_time = time.time()
        
        try:
            logger.debug(f"开始执行工作流")
            
            # 创建执行上下文
            exec_context = ExecutionContext(
                workflow_id=str(getattr(workflow, 'id', 'unknown')),
                execution_id=str(uuid.uuid4()),
                config=context or {}
            )
            exec_context.mark_started()
            
            # 验证输入
            if not workflow:
                raise ValueError("工作流不能为空")
            if not initial_state:
                raise ValueError("初始状态不能为空")
            
            # 使用执行策略执行工作流
            if self._strategy:
                # 策略的返回类型可能不同，需要转换
                result = self._strategy.execute(self, workflow, exec_context)  # type: ignore
                if isinstance(result, ExecutionResult):
                    return initial_state
            else:
                result = initial_state
            
            exec_context.mark_completed()
            logger.debug(f"工作流执行完成，耗时: {time.time() - start_time:.3f}s")
            
            return result if hasattr(result, '__dict__') else initial_state
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            raise
    
    async def execute_async(
        self, 
        workflow: 'IWorkflow', 
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
        start_time = time.time()
        
        try:
            logger.debug(f"开始异步执行工作流")
            
            # 创建执行上下文
            exec_context = ExecutionContext(
                workflow_id=str(getattr(workflow, 'id', 'unknown')),
                execution_id=str(uuid.uuid4()),
                config=context or {}
            )
            exec_context.mark_started()
            
            # 验证输入
            if not workflow:
                raise ValueError("工作流不能为空")
            if not initial_state:
                raise ValueError("初始状态不能为空")
            
            # 使用执行策略执行工作流
            if self._strategy:
                # 检查策略是否支持异步
                if hasattr(self._strategy, 'execute_async'):
                    result = await self._strategy.execute_async(self, workflow, exec_context)  # type: ignore
                else:
                    # 在线程池中执行同步策略
                    import asyncio
                    import functools
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, 
                        functools.partial(self._strategy.execute, self, workflow, exec_context)  # type: ignore
                    )
                if isinstance(result, ExecutionResult):
                    return initial_state
            else:
                result = initial_state
            
            exec_context.mark_completed()
            logger.debug(f"工作流异步执行完成，耗时: {time.time() - start_time:.3f}s")
            
            return result if hasattr(result, '__dict__') else initial_state
            
        except Exception as e:
            logger.error(f"工作流异步执行失败: {str(e)}")
            raise
    
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
    
    def execute_stream(
        self,
        workflow: 'IWorkflow',
        initial_state: 'IWorkflowState',
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        logger.debug("开始流式执行工作流")
        # 默认实现：不生成任何事件
        return
        yield  # type: ignore
    
    def execute_stream_async(
        self,
        workflow: 'IWorkflow',
        initial_state: 'IWorkflowState',
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        logger.debug("开始异步流式执行工作流")
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
        logger.debug(f"获取执行状态: {execution_id}")
        return {
            "execution_id": execution_id,
            "status": "unknown"
        }
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            bool: 是否成功取消
        """
        logger.debug(f"取消执行: {execution_id}")
        return False
    
