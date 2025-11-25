"""工作流状态构建器

提供构建工作流状态对象的构建器类。
"""

from typing import Any, Dict, List, Optional, Union

from src.interfaces.state.workflow import IWorkflowState
from ..implementations.workflow_state import WorkflowState
from ..implementations.workflow_state import (
    HumanMessage, AIMessage, SystemMessage, ToolMessage,
    BaseMessage
)
from .state_builder import StateBuilder


class WorkflowStateBuilder(StateBuilder[IWorkflowState]):
    """工作流状态构建器
    
    提供流畅的API来构建和配置工作流状态。
    """
    
    def __init__(self) -> None:
        """初始化构建器"""
        super().__init__()
        
        # 工作流特定字段
        self._current_node: Optional[str] = None
        self._iteration_count: int = 0
        self._thread_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._max_iterations: int = 10
        self._messages: List[BaseMessage] = []
        self._execution_history: List[Dict[str, Any]] = []
        self._errors: List[str] = []
    
    def build(self) -> IWorkflowState:
        """构建工作流状态
        
        Returns:
            IWorkflowState: 工作流状态对象
        """
        # 准备基础参数
        args = self._prepare_build_args()
        
        # 添加工作流特定参数
        args.update({
            "current_node": self._current_node,
            "iteration_count": self._iteration_count,
            "thread_id": self._thread_id,
            "session_id": self._session_id,
            "max_iterations": self._max_iterations,
            "messages": self._messages.copy(),
            "execution_history": self._execution_history.copy(),
            "errors": self._errors.copy()
        })
        
        return WorkflowState(**args)
    
    def with_current_node(self, node: str) -> "WorkflowStateBuilder":
        """设置当前节点
        
        Args:
            node: 节点ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._current_node = node
        return self
    
    def with_iteration_count(self, count: int) -> "WorkflowStateBuilder":
        """设置迭代计数
        
        Args:
            count: 迭代次数
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._iteration_count = count
        return self
    
    def with_thread_id(self, thread_id: str) -> "WorkflowStateBuilder":
        """设置线程ID
        
        Args:
            thread_id: 线程ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._thread_id = thread_id
        return self
    
    def with_session_id(self, session_id: str) -> "WorkflowStateBuilder":
        """设置会话ID
        
        Args:
            session_id: 会话ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._session_id = session_id
        return self
    
    def with_max_iterations(self, max_iterations: int) -> "WorkflowStateBuilder":
        """设置最大迭代次数
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._max_iterations = max_iterations
        return self
    
    def with_messages(self, messages: List[Union[BaseMessage, str, Dict[str, Any]]]) -> "WorkflowStateBuilder":
        """设置消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._messages.clear()
        for message in messages:
            self.add_message(message)
        return self
    
    def add_message(self, message: Union[BaseMessage, str, Dict[str, Any]]) -> "WorkflowStateBuilder":
        """添加消息
        
        Args:
            message: 消息对象、字符串或消息字典
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        if isinstance(message, str):
            # 默认为人类消息
            msg = HumanMessage(content=message)
        elif isinstance(message, dict):
            msg = self._create_message_from_dict(message)
        else:
            msg = message
        
        self._messages.append(msg)
        return self
    
    def add_messages(self, messages: List[Union[BaseMessage, str, Dict[str, Any]]]) -> "WorkflowStateBuilder":
        """添加多个消息
        
        Args:
            messages: 消息列表
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        for message in messages:
            self.add_message(message)
        return self
    
    def with_human_message(self, content: str) -> "WorkflowStateBuilder":
        """添加人类消息
        
        Args:
            content: 消息内容
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._messages.append(HumanMessage(content=content))
        return self
    
    def with_ai_message(self, content: str) -> "WorkflowStateBuilder":
        """添加AI消息
        
        Args:
            content: 消息内容
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._messages.append(AIMessage(content=content))
        return self
    
    def with_system_message(self, content: str) -> "WorkflowStateBuilder":
        """添加系统消息
        
        Args:
            content: 消息内容
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._messages.append(SystemMessage(content=content))
        return self
    
    def with_tool_message(self, content: str, tool_call_id: str = "") -> "WorkflowStateBuilder":
        """添加工具消息
        
        Args:
            content: 消息内容
            tool_call_id: 工具调用ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
        return self
    
    def with_execution_history(self, history: List[Dict[str, Any]]) -> "WorkflowStateBuilder":
        """设置执行历史
        
        Args:
            history: 执行历史列表
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._execution_history = history.copy()
        return self
    
    def add_execution_step(self, step: Dict[str, Any]) -> "WorkflowStateBuilder":
        """添加执行步骤
        
        Args:
            step: 执行步骤
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._execution_history.append(step)
        return self
    
    def with_errors(self, errors: List[str]) -> "WorkflowStateBuilder":
        """设置错误列表
        
        Args:
            errors: 错误列表
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._errors = errors.copy()
        return self
    
    def add_error(self, error: str) -> "WorkflowStateBuilder":
        """添加错误
        
        Args:
            error: 错误信息
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._errors.append(error)
        return self
    
    def clear_messages(self) -> "WorkflowStateBuilder":
        """清除所有消息
        
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._messages.clear()
        return self
    
    def clear_errors(self) -> "WorkflowStateBuilder":
        """清除所有错误
        
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._errors.clear()
        return self
    
    def clear_execution_history(self) -> "WorkflowStateBuilder":
        """清除执行历史
        
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._execution_history.clear()
        return self
    
    def increment_iteration(self) -> "WorkflowStateBuilder":
        """增加迭代计数
        
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._iteration_count += 1
        return self
    
    def reset_iteration(self) -> "WorkflowStateBuilder":
        """重置迭代计数
        
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._iteration_count = 0
        return self
    
    def _create_message_from_dict(self, data: Dict[str, Any]) -> BaseMessage:
        """从字典创建消息
        
        Args:
            data: 消息数据字典
            
        Returns:
            BaseMessage: 消息对象
        """
        content = data.get("content", "")
        role = data.get("role", "unknown")
        
        if role == "human":
            return HumanMessage(content=content)
        elif role == "ai":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        elif role == "tool":
            tool_call_id = data.get("tool_call_id", "")
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            return HumanMessage(content=content)  # 默认为人类消息
    
    def reset(self) -> "WorkflowStateBuilder":
        """重置构建器
        
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        super().reset()
        self._current_node = None
        self._iteration_count = 0
        self._thread_id = None
        self._session_id = None
        self._max_iterations = 10
        self._messages.clear()
        self._execution_history.clear()
        self._errors.clear()
        return self


# 便捷函数
def create_workflow_builder() -> WorkflowStateBuilder:
    """创建工作流状态构建器的便捷函数
    
    Returns:
        WorkflowStateBuilder: 工作流状态构建器实例
    """
    return WorkflowStateBuilder()


def workflow_state() -> WorkflowStateBuilder:
    """创建工作流状态构建器的便捷函数（流式API）
    
    Returns:
        WorkflowStateBuilder: 工作流状态构建器实例
    """
    return WorkflowStateBuilder()