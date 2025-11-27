"""执行模式基类

提供执行模式的基础接口和抽象实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from src.interfaces import IWorkflowState
    from src.interfaces.workflow.core import INode
    from src.core.workflow.execution.core.execution_context import ExecutionContext, NodeResult

class IExecutionMode(ABC):
    """执行模式接口
    
    定义不同的执行模式接口。
    
    设计原则：
    1. 每个模式只实现其主要方法
    2. SyncMode: 实现execute_node()用于同步执行
    3. AsyncMode: 实现execute_node_async()用于异步执行
    4. 禁止跨模式调用（调用另一种方法）
    """
    
    @abstractmethod
    def execute_node(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """同步执行节点
        
        仅在SyncMode中使用。AsyncMode必须使用execute_node_async()。
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
            
        Raises:
            RuntimeError: 在不支持的模式中调用
        """
        pass
    
    @abstractmethod
    async def execute_node_async(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """异步执行节点
        
        仅在AsyncMode中使用。SyncMode必须使用execute_node()。
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
            
        Raises:
            RuntimeError: 在不支持的模式中调用
        """
        pass
    
    @abstractmethod
    def supports_async(self) -> bool:
        """是否支持异步执行
        
        Returns:
            bool: 是否支持异步
        """
        pass
    
    @abstractmethod
    def get_mode_name(self) -> str:
        """获取模式名称
        
        Returns:
            str: 模式名称
        """
        pass
    
    @abstractmethod
    def handle_execution_error(
        self, 
        error: Exception, 
        node: 'INode', 
        state: 'IWorkflowState'
    ) -> 'NodeResult':
        """处理执行错误
        
        Args:
            error: 异常
            node: 节点实例
            state: 当前状态
            
        Returns:
            NodeResult: 错误结果
        """
        pass
    
    def supports_streaming(self) -> bool:
        """是否支持流式执行
        
        Returns:
            bool: 是否支持流式
        """
        return False
    
    def execute_node_stream(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 流式事件
        """
        raise NotImplementedError(f"{self.get_mode_name()} 模式不支持流式执行")


class BaseMode(IExecutionMode):
    """执行模式基类
    
    提供执行模式的通用实现。
    """
    
    def __init__(self, name: str, supports_async: bool = False):
        """初始化模式
        
        Args:
            name: 模式名称
            supports_async: 是否支持异步
        """
        self._name = name
        self._supports_async = supports_async
    
    def get_mode_name(self) -> str:
        """获取模式名称"""
        return self._name
    
    def supports_async(self) -> bool:
        """是否支持异步执行"""
        return self._supports_async
    
    def validate_inputs(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
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
    
    def create_node_result(
        self,
        success: bool,
        state: 'IWorkflowState',
        next_node: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'NodeResult':
        """创建节点执行结果
        
        Args:
            success: 是否成功
            state: 执行后状态
            next_node: 下一个节点
            error: 错误信息
            metadata: 元数据
            
        Returns:
            NodeResult: 节点执行结果
        """
        from ..core.execution_context import NodeResult
        
        return NodeResult(
            success=success,
            state=state,
            next_node=next_node,
            error=error,
            metadata=metadata or {},
            mode_name=self._name
        )
    
    def handle_execution_error(
        self, 
        error: Exception, 
        node: 'INode', 
        state: 'IWorkflowState'
    ) -> 'NodeResult':
        """处理执行错误
        
        Args:
            error: 异常
            node: 节点实例
            state: 当前状态
            
        Returns:
            NodeResult: 错误结果
        """
        return self.create_node_result(
            success=False,
            state=state,
            error=str(error),
            metadata={
                "error_type": type(error).__name__,
                "node_id": getattr(node, 'node_id', 'unknown'),
                "node_type": getattr(node, 'node_type', 'unknown')
            }
        )