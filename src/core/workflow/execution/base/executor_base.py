"""执行器基类

提供执行器的基础接口和抽象实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from src.interfaces.workflow.execution import IStreamingExecutor
from src.interfaces.workflow.core import IWorkflow, ExecutionContext
from src.interfaces.state.workflow import IWorkflowState


class BaseExecutor(IStreamingExecutor, ABC):
    """执行器基类
    
    提供执行器的通用实现和模板方法。
    """
    
    def __init__(self) -> None:
        """初始化执行器"""
        self._execution_context: Optional[ExecutionContext] = None
    
    @property
    def execution_context(self) -> Optional[ExecutionContext]:
        """获取执行上下文
        
        Returns:
            Optional[ExecutionContext]: 执行上下文
        """
        return self._execution_context
    
    def _set_execution_context(self, context: ExecutionContext) -> None:
        """设置执行上下文
        
        Args:
            context: 执行上下文
        """
        self._execution_context = context
    
    def _validate_workflow(self, workflow: IWorkflow) -> None:
        """验证工作流
        
        Args:
            workflow: 工作流实例
            
        Raises:
            ValueError: 工作流无效
        """
        if not workflow.entry_point:
            raise ValueError("工作流未设置入口点")
    
    def _get_node(self, workflow: IWorkflow, node_id: str) -> Any:
        """获取节点
        
        Args:
            workflow: 工作流实例
            node_id: 节点ID
            
        Returns:
            节点实例
            
        Raises:
            ValueError: 节点不存在
        """
        node = workflow.get_node(node_id)
        if not node:
            raise ValueError(f"节点不存在: {node_id}")
        return node
    
    def _handle_execution_error(self, state: IWorkflowState, error: Exception) -> None:
        """处理执行错误
        
        Args:
            state: 当前状态
            error: 错误对象
        """
        state.set_field("error", str(error))
    
    def _create_event(self, event_type: str, **kwargs: Any) -> Dict[str, Any]:
        """创建事件
        
        Args:
            event_type: 事件类型
            **kwargs: 事件参数
            
        Returns:
            Dict[str, Any]: 事件字典
        """
        from ..utils import TimestampHelper
        
        event = {
            "type": event_type,
            "timestamp": TimestampHelper.get_timestamp()
        }
        
        if self._execution_context:
            event["workflow_id"] = self._execution_context.workflow_id
            event["execution_id"] = self._execution_context.execution_id
        
        event.update(kwargs)
        return event
    
    def _create_workflow_started_event(self) -> Dict[str, Any]:
        """创建工作流开始事件
        
        Returns:
            Dict[str, Any]: 工作流开始事件
        """
        return self._create_event("workflow_started")
    
    def _create_workflow_completed_event(self, final_state: IWorkflowState) -> Dict[str, Any]:
        """创建工作流完成事件
        
        Args:
            final_state: 最终状态
            
        Returns:
            Dict[str, Any]: 工作流完成事件
        """
        return self._create_event(
            "workflow_completed",
            final_state=final_state.get_field("error") is None
        )
    
    def _create_node_started_event(self, node_id: str, node_type: str) -> Dict[str, Any]:
        """创建节点开始事件
        
        Args:
            node_id: 节点ID
            node_type: 节点类型
            
        Returns:
            Dict[str, Any]: 节点开始事件
        """
        return self._create_event(
            "node_started",
            node_id=node_id,
            node_type=node_type
        )
    
    def _create_node_completed_event(self, node_id: str, node_type: str, 
                                   result: Dict[str, Any]) -> Dict[str, Any]:
        """创建节点完成事件
        
        Args:
            node_id: 节点ID
            node_type: 节点类型
            result: 执行结果
            
        Returns:
            Dict[str, Any]: 节点完成事件
        """
        return self._create_event(
            "node_completed",
            node_id=node_id,
            node_type=node_type,
            result=result
        )
    
    def _create_node_error_event(self, node_id: Optional[str], node_type: str,
                               error: Exception) -> Dict[str, Any]:
        """创建节点错误事件
        
        Args:
            node_id: 节点ID
            node_type: 节点类型
            error: 错误对象
            
        Returns:
            Dict[str, Any]: 节点错误事件
        """
        return self._create_event(
            "node_error",
            node_id=node_id,
            node_type=node_type,
            error=str(error)
        )
    
    @abstractmethod
    def _get_next_nodes(self, workflow: IWorkflow, node_id: str,
                        state: IWorkflowState, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        pass
    
    @abstractmethod
    async def _get_next_nodes_async(self, workflow: IWorkflow, node_id: str,
                                   state: IWorkflowState, config: Dict[str, Any]) -> List[str]:
        """异步获取下一个节点列表
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        pass