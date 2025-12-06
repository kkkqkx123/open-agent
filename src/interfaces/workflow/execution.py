"""Workflow execution interfaces.

This module contains interfaces related to workflow execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import IWorkflow
    from ..state import IWorkflowState
    from src.infrastructure.error_management.impl.workflow import WorkflowValidator
from src.interfaces.workflow.exceptions import WorkflowError
# 延迟导入以避免循环导入
def _get_error_handler_functions():
    from src.infrastructure.error_management.impl.workflow import handle_workflow_error, create_workflow_error_context
    return handle_workflow_error, create_workflow_error_context


class IWorkflowExecutor(ABC):
    """工作流执行器接口"""

    @abstractmethod
    def execute(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState', 
                context: Optional[Dict[str, Any]] = None) -> 'IWorkflowState':
        """同步执行工作流"""
        pass

    @abstractmethod
    async def execute_async(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState',
                           context: Optional[Dict[str, Any]] = None) -> 'IWorkflowState':
        """异步执行工作流"""
        pass

    @abstractmethod
    def execute_stream(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState',
                       context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """流式执行工作流"""
        pass

    @abstractmethod
    def execute_stream_async(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState',
                                  context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流"""
        pass

    @abstractmethod
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行状态信息
        """
        pass
    
    @abstractmethod
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功取消
        """
        pass


class INodeExecutor(ABC):
    """节点执行器接口
    
    定义节点执行的统一接口，支持不同类型的节点执行策略。
    """
    
    @abstractmethod
    def execute_node(
        self,
        node_config: Any,
        state: 'IWorkflowState',
        config: Optional[Dict[str, Any]] = None
    ) -> 'IWorkflowState':
        """执行节点
        
        Args:
            node_config: 节点配置
            state: 当前状态
            config: 执行配置
            
        Returns:
            执行后的状态
        """
        pass
    
    @abstractmethod
    async def execute_node_async(
        self,
        node_config: Any,
        state: 'IWorkflowState',
        config: Optional[Dict[str, Any]] = None
    ) -> 'IWorkflowState':
        """异步执行节点
        
        Args:
            node_config: 节点配置
            state: 当前状态
            config: 执行配置
            
        Returns:
            执行后的状态
        """
        pass
    
    @abstractmethod
    def can_execute(self, node_type: str) -> bool:
        """检查是否可以执行指定类型的节点
        
        Args:
            node_type: 节点类型
            
        Returns:
            是否可以执行
        """
        pass
    
    @abstractmethod
    def get_supported_node_types(self) -> List[str]:
        """获取支持的节点类型
        
        Returns:
            支持的节点类型列表
        """
        pass
    
    @abstractmethod
    def get_execution_metadata(self) -> Dict[str, Any]:
        """获取执行器元数据
        
        Returns:
            执行器元数据，包含版本、支持的功能等信息
        """
        pass


class IExecutionStrategy(ABC):
    """执行策略接口
    
    定义不同的执行策略接口。
    """
    
    @abstractmethod
    def should_continue(self, state: 'IWorkflowState', context: Dict[str, Any]) -> bool:
        """判断是否应该继续执行
        
        Args:
            state: 当前状态
            context: 执行上下文
            
        Returns:
            是否应该继续
        """
        pass
    
    @abstractmethod
    def get_next_step(self, state: 'IWorkflowState', context: Dict[str, Any]) -> Optional[str]:
        """获取下一步执行节点
        
        Args:
            state: 当前状态
            context: 执行上下文
            
        Returns:
            下一个节点ID，如果None则表示结束
        """
        pass
    
    def handle_error(self, error: Exception, state: 'IWorkflowState', context: Dict[str, Any]) -> 'IWorkflowState':
        """处理执行错误
        
        默认实现使用统一错误处理框架
        
        Args:
            error: 异常
            state: 当前状态
            context: 执行上下文
            
        Returns:
            处理后的状态
        """
        # 创建错误上下文
        workflow_id = getattr(state, 'workflow_id', None)
        step_id = context.get('step_id')
        execution_id = context.get('execution_id')
        
        # 延迟导入错误处理函数以避免循环导入
        handle_workflow_error, create_workflow_error_context = _get_error_handler_functions()
        
        error_context = create_workflow_error_context(
            workflow_id=workflow_id,
            step_id=step_id,
            execution_id=execution_id,
            state_data=state.to_dict() if hasattr(state, 'to_dict') else None,
            error=error,
            **context
        )
        
        # 使用统一错误处理
        handle_workflow_error(error, error_context)
        
        # 如果是工作流错误，尝试恢复
        if isinstance(error, WorkflowError):
            # 这里可以添加恢复逻辑
            pass
        
        return state


class IExecutionObserver(ABC):
    """执行观察者接口
    
    定义执行过程中的观察和回调机制。
    """
    
    @abstractmethod
    def on_execution_start(self, execution_id: str, workflow: Any, initial_state: 'IWorkflowState') -> None:
        """执行开始回调
        
        Args:
            execution_id: 执行ID
            workflow: 工作流实例
            initial_state: 初始状态
        """
        pass
    
    @abstractmethod
    def on_node_start(self, execution_id: str, node_id: str, state: 'IWorkflowState') -> None:
        """节点开始执行回调
        
        Args:
            execution_id: 执行ID
            node_id: 节点ID
            state: 当前状态
        """
        pass
    
    @abstractmethod
    def on_node_complete(self, execution_id: str, node_id: str, state: 'IWorkflowState') -> None:
        """节点执行完成回调
        
        Args:
            execution_id: 执行ID
            node_id: 节点ID
            state: 执行后状态
        """
        pass
    
    @abstractmethod
    def on_node_error(self, execution_id: str, node_id: str, error: Exception, state: 'IWorkflowState') -> None:
        """节点执行错误回调
        
        Args:
            execution_id: 执行ID
            node_id: 节点ID
            error: 异常
            state: 当前状态
        """
        pass
    
    @abstractmethod
    def on_execution_complete(self, execution_id: str, final_state: 'IWorkflowState') -> None:
        """执行完成回调
        
        Args:
            execution_id: 执行ID
            final_state: 最终状态
        """
        pass


class IStreamingExecutor(ABC):
    """流式执行器接口
    
    定义流式执行工作流的接口，支持同步和异步流式执行。
    """
    
    @abstractmethod
    def execute_stream(
        self,
        workflow: Any,
        initial_state: 'IWorkflowState',
        context: Any
    ) -> List[Dict[str, Any]]:
        """流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            List[Dict[str, Any]]: 执行事件列表
        """
        pass