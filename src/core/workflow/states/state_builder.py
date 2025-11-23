"""工作流状态构建器

简化的状态构建器，使用整合后的 WorkflowState 实现。
"""

from typing import Any, Dict, List, Optional, Union

from src.interfaces.state.workflow import IWorkflowState, IWorkflowStateBuilder
from .workflow_state import (
    WorkflowState, BaseMessage, HumanMessage, AIMessage,
    SystemMessage, ToolMessage, MessageRole
)


class WorkflowStateBuilder(IWorkflowStateBuilder):
    """工作流状态构建器
    
    提供流畅的API来构建和配置工作流状态。
    """
    
    def __init__(self) -> None:
        """初始化构建器"""
        self._state = WorkflowState()
    
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
            msg = _create_message_from_dict(message)
        else:
            msg = message
        
        self._state.add_message(msg)
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
    
    def set_field(self, key: str, value: Any) -> "WorkflowStateBuilder":
        """设置字段
        
        Args:
            key: 字段键
            value: 字段值
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.set_field(key, value)
        return self
    
    def set_metadata(self, key: str, value: Any) -> "WorkflowStateBuilder":
        """设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.set_metadata(key, value)
        return self
    
    def build(self) -> WorkflowState:
        """构建工作流状态
        
        Returns:
            WorkflowState: 构建的工作流状态
        """
        return self._state
    
    # 其他便利方法
    def with_data(self, data: Dict[str, Any]) -> "WorkflowStateBuilder":
        """设置状态数据
        
        Args:
            data: 状态数据字典
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state._data.update(data)
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> "WorkflowStateBuilder":
        """设置元数据（别名方法）
        
        Args:
            metadata: 元数据字典
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state._metadata.update(metadata)
        return self
    
    def with_id(self, id: str) -> "WorkflowStateBuilder":
        """设置状态ID
        
        Args:
            id: 状态ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.set_id(id)
        return self
    
    def with_thread_id(self, thread_id: str) -> "WorkflowStateBuilder":
        """设置线程ID
        
        Args:
            thread_id: 线程ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.set_thread_id(thread_id)
        return self
    
    def with_session_id(self, session_id: str) -> "WorkflowStateBuilder":
        """设置会话ID
        
        Args:
            session_id: 会话ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.set_session_id(session_id)
        return self
    
    def with_current_node(self, node: str) -> "WorkflowStateBuilder":
        """设置当前节点
        
        Args:
            node: 节点ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.set_current_node(node)
        return self
    
    def with_max_iterations(self, max_iterations: int) -> "WorkflowStateBuilder":
        """设置最大迭代次数
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state._max_iterations = max_iterations
        return self
    
    def with_messages(self, messages: List[Union[BaseMessage, str, Dict[str, Any]]]) -> "WorkflowStateBuilder":
        """添加多个消息（别名方法）
        
        Args:
            messages: 消息列表
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        return self.add_messages(messages)
    
    def with_human_message(self, content: str) -> "WorkflowStateBuilder":
        """添加人类消息
        
        Args:
            content: 消息内容
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.add_message(HumanMessage(content=content))
        return self
    
    def with_ai_message(self, content: str) -> "WorkflowStateBuilder":
        """添加AI消息
        
        Args:
            content: 消息内容
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.add_message(AIMessage(content=content))
        return self
    
    def with_system_message(self, content: str) -> "WorkflowStateBuilder":
        """添加系统消息
        
        Args:
            content: 消息内容
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.add_message(SystemMessage(content=content))
        return self
    
    def with_tool_message(self, content: str, tool_call_id: str = "") -> "WorkflowStateBuilder":
        """添加工具消息
        
        Args:
            content: 消息内容
            tool_call_id: 工具调用ID
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.add_message(ToolMessage(content=content, tool_call_id=tool_call_id))
        return self
    
    def with_error(self, error: str) -> "WorkflowStateBuilder":
        """添加错误
        
        Args:
            error: 错误信息
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.add_error(error)
        return self
    
    def with_field(self, key: str, value: Any) -> "WorkflowStateBuilder":
        """设置工作流字段（别名方法）
        
        Args:
            key: 字段键
            value: 字段值
            
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        return self.set_field(key, value)
    
    def mark_complete(self) -> "WorkflowStateBuilder":
        """标记为完成
        
        Returns:
            WorkflowStateBuilder: 构建器实例
        """
        self._state.mark_complete()
        return self
    
    def reset(self) -> "WorkflowStateBuilder":
        """重置构建器
        
        Returns:
            WorkflowStateBuilder: 重置后的构建器实例
        """
        self._state = WorkflowState()
        return self


def create_empty_state() -> WorkflowState:
    """创建空的工作流状态
    
    Returns:
        WorkflowState: 空的工作流状态
    """
    return WorkflowState()


def create_state_from_dict(data: Dict[str, Any]) -> WorkflowState:
    """从字典创建工作流状态
    
    Args:
        data: 状态数据字典
        
    Returns:
        WorkflowState: 工作流状态
    """
    return WorkflowState.from_dict(data)


def create_state_with_messages(messages: List[Union[BaseMessage, str, Dict[str, Any]]]) -> WorkflowState:
    """创建包含消息的工作流状态
    
    Args:
        messages: 消息列表
        
    Returns:
        WorkflowState: 工作流状态
    """
    return (WorkflowStateBuilder()
            .with_messages(messages)
            .build())


def create_state_with_conversation(human_message: str, ai_message: Optional[str] = None) -> WorkflowState:
    """创建包含对话的工作流状态
    
    Args:
        human_message: 人类消息
        ai_message: AI消息（可选）
        
    Returns:
        WorkflowState: 工作流状态
    """
    builder = WorkflowStateBuilder().with_human_message(human_message)
    
    if ai_message:
        builder.with_ai_message(ai_message)
    
    return builder.build()


def _create_message_from_dict(data: Dict[str, Any]) -> BaseMessage:
    """从字典创建消息
    
    Args:
        data: 消息数据字典
        
    Returns:
        BaseMessage: 消息对象
    """
    content = data.get("content", "")
    role = data.get("role", MessageRole.UNKNOWN)
    
    if role == MessageRole.HUMAN:
        return HumanMessage(content=content)
    elif role == MessageRole.AI:
        return AIMessage(content=content)
    elif role == MessageRole.SYSTEM:
        return SystemMessage(content=content)
    elif role == MessageRole.TOOL:
        tool_call_id = data.get("tool_call_id", "")
        return ToolMessage(content=content, tool_call_id=tool_call_id)
    else:
        return BaseMessage(content=content, role=role)


# 便捷函数
def builder() -> WorkflowStateBuilder:
    """创建新的状态构建器
    
    Returns:
        WorkflowStateBuilder: 新的构建器实例
    """
    return WorkflowStateBuilder()


def from_dict(data: Dict[str, Any]) -> WorkflowState:
    """从字典创建状态的便捷函数
    
    Args:
        data: 状态数据字典
        
    Returns:
        WorkflowState: 工作流状态
    """
    return create_state_from_dict(data)


def with_messages(messages: List[Union[BaseMessage, str, Dict[str, Any]]]) -> WorkflowState:
    """创建包含消息的状态的便捷函数
    
    Args:
        messages: 消息列表
        
    Returns:
        WorkflowState: 工作流状态
    """
    return create_state_with_messages(messages)


def conversation(human_message: str, ai_message: Optional[str] = None) -> WorkflowState:
    """创建对话状态的便捷函数
    
    Args:
        human_message: 人类消息
        ai_message: AI消息（可选）
        
    Returns:
        WorkflowState: 工作流状态
    """
    return create_state_with_conversation(human_message, ai_message)