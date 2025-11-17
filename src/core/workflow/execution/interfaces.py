"""执行引擎接口

定义工作流执行引擎的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from ..interfaces import IWorkflow, IWorkflowState, ExecutionContext


class IExecutor(ABC):
    """执行器接口"""

    @abstractmethod
    def execute(self, workflow: IWorkflow, initial_state: IWorkflowState, 
                context: ExecutionContext) -> IWorkflowState:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        pass

    @abstractmethod
    async def execute_async(self, workflow: IWorkflow, initial_state: IWorkflowState,
                           context: ExecutionContext) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        pass


class IAsyncExecutor(IExecutor):
    """异步执行器接口"""

    @abstractmethod
    async def execute_async(self, workflow: IWorkflow, initial_state: IWorkflowState,
                           context: ExecutionContext) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        pass


class IStreamingExecutor(IExecutor):
    """流式执行器接口"""

    @abstractmethod
    def execute_stream(self, workflow: IWorkflow, initial_state: IWorkflowState,
                       context: ExecutionContext) -> List[Dict[str, Any]]:
        """流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            List[Dict[str, Any]]: 执行事件列表
        """
        pass

    @abstractmethod
    async def execute_stream_async(self, workflow: IWorkflow, initial_state: IWorkflowState,
                              context: ExecutionContext) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        pass


class IExecutionContext:
    """执行上下文接口"""

    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass

    @property
    @abstractmethod
    def execution_id(self) -> str:
        """执行ID"""
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass

    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        """配置"""
        pass