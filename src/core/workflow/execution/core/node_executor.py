"""节点执行器

提供节点的核心执行功能。
"""

from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Any, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

from ..modes.mode_base import IExecutionMode
from .execution_context import ExecutionContext, NodeResult

if TYPE_CHECKING:
    from src.interfaces import IWorkflowState
    from src.interfaces.workflow.core import INode

logger = get_logger(__name__)


class INodeExecutor(ABC):
    """节点执行器接口"""
    
    @abstractmethod
    def execute_node(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> NodeResult:
        """执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        pass
    
    @abstractmethod
    async def execute_node_async(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> NodeResult:
        """异步执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        pass
    
    @abstractmethod
    def set_mode(self, mode: IExecutionMode) -> None:
        """设置执行模式
        
        Args:
            mode: 执行模式
        """
        pass


class NodeExecutor(INodeExecutor):
    """节点执行器实现
    
    提供节点的核心执行功能，支持不同的执行模式。
    """
    
    def __init__(self, mode: Optional[IExecutionMode] = None):
        """初始化节点执行器
        
        Args:
            mode: 执行模式
        """
        self._mode = mode
        logger.debug(f"节点执行器初始化完成，模式: {mode.get_mode_name() if mode else '默认'}")
    
    def execute_node(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> NodeResult:
        """执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"开始执行节点: {getattr(node, 'node_id', 'unknown')}")
            
            # 验证输入
            self._validate_inputs(node, state, context)
            
            # 使用执行模式执行节点
            if self._mode:
                result = self._mode.execute_node(node, state, context)
            else:
                result = self._default_execute_node(node, state, context)
            
            # 设置执行时间
            result.execution_time = time.time() - start_time
            
            logger.debug(f"节点执行完成: {getattr(node, 'node_id', 'unknown')}, 耗时: {result.execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"节点执行失败: {str(e)}"
            logger.error(error_msg)
            
            # 创建错误结果
            if self._mode:
                result = self._mode.handle_execution_error(e, node, state)
            else:
                result = self._create_error_result(e, node, state)
            
            result.execution_time = execution_time
            return result
    
    async def execute_node_async(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> NodeResult:
        """异步执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"开始异步执行节点: {getattr(node, 'node_id', 'unknown')}")
            
            # 验证输入
            self._validate_inputs(node, state, context)
            
            # 检查是否支持异步
            if self._mode and self._mode.supports_async():
                result = await self._mode.execute_node_async(node, state, context)
            elif hasattr(node, 'execute_async'):
                # 节点本身支持异步（将IWorkflowState作为IState使用）
                node_result = await node.execute_async(state, context.config)  # type: ignore
                result = self._process_node_result(node_result, state, context)
            else:
                # 使用默认异步执行
                result = await self._default_execute_node_async(node, state, context)
            
            # 设置执行时间
            result.execution_time = time.time() - start_time
            
            logger.debug(f"节点异步执行完成: {getattr(node, 'node_id', 'unknown')}, 耗时: {result.execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"节点异步执行失败: {str(e)}"
            logger.error(error_msg)
            
            # 创建错误结果
            if self._mode:
                result = self._mode.handle_execution_error(e, node, state)
            else:
                result = self._create_error_result(e, node, state)
            
            result.execution_time = execution_time
            return result
    
    def set_mode(self, mode: IExecutionMode) -> None:
        """设置执行模式
        
        Args:
            mode: 执行模式
        """
        self._mode = mode
        logger.debug(f"节点执行器模式已设置为: {mode.get_mode_name()}")
    
    def _validate_inputs(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> None:
        """验证输入参数
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Raises:
            ValueError: 输入参数无效
        """
        if not node:
            raise ValueError("节点不能为空")
        if not state:
            raise ValueError("状态不能为空")
        if not context:
            raise ValueError("执行上下文不能为空")
    
    def _default_execute_node(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> NodeResult:
        """默认节点执行逻辑
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        # 执行节点（将IWorkflowState作为IState使用）
        node_result = node.execute(state, context.config)  # type: ignore
        
        # 处理执行结果
        return self._process_node_result(node_result, state, context)
    
    async def _default_execute_node_async(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> NodeResult:
        """默认异步节点执行逻辑
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        import asyncio
        
        # 在线程池中执行同步节点（将IWorkflowState作为IState使用）
        loop = asyncio.get_event_loop()
        node_result = await loop.run_in_executor(None, node.execute, state, context.config)  # type: ignore
        
        # 处理执行结果
        return self._process_node_result(node_result, state, context)
    
    def _process_node_result(
        self, 
        node_result: Any, 
        original_state: 'IWorkflowState', 
        context: ExecutionContext
    ) -> NodeResult:
        """处理节点执行结果
        
        Args:
            node_result: 节点执行结果
            original_state: 原始状态
            context: 执行上下文
            
        Returns:
            NodeResult: 处理后的节点执行结果
        """
        # 提取状态
        if hasattr(node_result, 'state'):
            final_state = node_result.state
        elif isinstance(node_result, dict):
            # 如果返回的是字典，尝试更新状态
            final_state = original_state
            for key, value in node_result.items():
                if hasattr(final_state, key):
                    setattr(final_state, key, value)
                else:
                    final_state = final_state.set_field(key, value)
        else:
            # 其他情况，保持原始状态
            final_state = original_state
        
        # 提取下一个节点
        next_node = None
        if hasattr(node_result, 'next_node'):
            next_node = node_result.next_node  # type: ignore
        elif isinstance(node_result, dict):
            next_node = node_result.get('next_node')  # type: ignore
        
        # 提取元数据
        metadata: Dict[str, Any] = {}
        if hasattr(node_result, 'metadata'):
            metadata = node_result.metadata  # type: ignore
        elif isinstance(node_result, dict):
            metadata = node_result.get('metadata', {})  # type: ignore
        
        # 添加节点信息到元数据
        metadata.update({
            "node_id": getattr(node_result, 'node_id', getattr(original_state, 'current_node_id', 'unknown')),
            "node_type": getattr(node_result, 'node_type', 'unknown'),
            "execution_timestamp": time.time()
        })
        
        return NodeResult(
            success=True,
            state=final_state,
            next_node=next_node,
            metadata=metadata,
            mode_name=self._mode.get_mode_name() if self._mode else "default"
        )
    
    def _create_error_result(
        self, 
        error: Exception, 
        node: 'INode', 
        state: 'IWorkflowState'
    ) -> NodeResult:
        """创建错误结果
        
        Args:
            error: 异常
            node: 节点实例
            state: 当前状态
            
        Returns:
            NodeResult: 错误结果
        """
        return NodeResult(
            success=False,
            state=state,
            error=str(error),
            metadata={
                "error_type": type(error).__name__,
                "node_id": getattr(node, 'node_id', 'unknown'),
                "node_type": getattr(node, 'node_type', 'unknown'),
                "execution_timestamp": time.time()
            },
            mode_name=self._mode.get_mode_name() if self._mode else "default"
        )