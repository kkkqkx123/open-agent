"""
状态构建器实现

提供流畅的状态构建接口，支持不可变状态模式
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ...interfaces.state.workflow import IWorkflowState, IStateBuilder
from .workflow_state import WorkflowState


class StateBuilder(IStateBuilder):
    """状态构建器实现"""
    
    def __init__(self, initial_state: Optional[IWorkflowState] = None):
        """初始化构建器"""
        self._messages: List[Any] = list(initial_state.messages) if initial_state else []
        self._metadata: Dict[str, Any] = dict(initial_state.metadata) if initial_state else {}
        self._fields: Dict[str, Any] = dict(initial_state.fields) if initial_state else {}
        self._created_at: datetime = initial_state.created_at if initial_state else datetime.now()
    
    def add_message(self, message: Any) -> 'StateBuilder':
        """添加消息"""
        self._messages.append(message)
        return self
    
    def add_messages(self, messages: List[Any]) -> 'StateBuilder':
        """添加多个消息"""
        self._messages.extend(messages)
        return self
    
    def set_metadata(self, key: str, value: Any) -> 'StateBuilder':
        """设置元数据"""
        self._metadata[key] = value
        return self
    
    def update_metadata(self, metadata: Dict[str, Any]) -> 'StateBuilder':
        """更新元数据"""
        self._metadata.update(metadata)
        return self
    
    def set_field(self, key: str, value: Any) -> 'StateBuilder':
        """设置字段"""
        self._fields[key] = value
        return self
    
    def update_fields(self, fields: Dict[str, Any]) -> 'StateBuilder':
        """更新多个字段"""
        self._fields.update(fields)
        return self
    
    def build(self) -> IWorkflowState:
        """构建状态"""
        return WorkflowState(
            messages=self._messages.copy(),
            metadata=self._metadata.copy(),
            fields=self._fields.copy(),
            created_at=self._created_at,
            updated_at=datetime.now()
        )
    
    def reset(self) -> 'StateBuilder':
        """重置构建器"""
        self._messages = []
        self._metadata = {}
        self._fields = {}
        self._created_at = datetime.now()
        return self
    
    def copy_from(self, state: IWorkflowState) -> 'StateBuilder':
        """从现有状态复制"""
        self._messages = list(state.messages)
        self._metadata = dict(state.metadata)
        self._fields = dict(state.fields)
        self._created_at = state.created_at
        return self


class FluentStateBuilder:
    """流畅的状态构建器，提供更丰富的构建选项"""
    
    def __init__(self, initial_state: Optional[IWorkflowState] = None):
        """初始化流畅构建器"""
        self._builder = StateBuilder(initial_state)
    
    def with_message(self, message: Any) -> 'FluentStateBuilder':
        """添加消息"""
        self._builder.add_message(message)
        return self
    
    def with_messages(self, messages: List[Any]) -> 'FluentStateBuilder':
        """添加多个消息"""
        self._builder.add_messages(messages)
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'FluentStateBuilder':
        """设置元数据"""
        self._builder.set_metadata(key, value)
        return self
    
    def with_metadata_dict(self, metadata: Dict[str, Any]) -> 'FluentStateBuilder':
        """设置元数据字典"""
        self._builder.update_metadata(metadata)
        return self
    
    def with_field(self, key: str, value: Any) -> 'FluentStateBuilder':
        """设置字段"""
        self._builder.set_field(key, value)
        return self
    
    def with_fields(self, fields: Dict[str, Any]) -> 'FluentStateBuilder':
        """设置多个字段"""
        self._builder.update_fields(fields)
        return self
    
    def build(self) -> IWorkflowState:
        """构建状态"""
        return self._builder.build()
    
    def reset(self) -> 'FluentStateBuilder':
        """重置构建器"""
        self._builder.reset()
        return self


def create_empty_state() -> IWorkflowState:
    """创建空状态"""
    return StateBuilder().build()


def create_state_with_message(message: Any) -> IWorkflowState:
    """创建包含单个消息的状态"""
    return StateBuilder().add_message(message).build()


def create_state_with_messages(messages: List[Any]) -> IWorkflowState:
    """创建包含多个消息的状态"""
    return StateBuilder().add_messages(messages).build()


def create_state_with_metadata(key: str, value: Any) -> IWorkflowState:
    """创建包含元数据的状态"""
    return StateBuilder().set_metadata(key, value).build()


def create_state_with_field(key: str, value: Any) -> IWorkflowState:
    """创建包含字段的状态"""
    return StateBuilder().set_field(key, value).build()


def create_state_from_existing(state: IWorkflowState) -> IWorkflowState:
    """从现有状态创建新状态"""
    return StateBuilder(state).build()


def create_modified_state(state: IWorkflowState, **kwargs) -> IWorkflowState:
    """创建修改后的状态"""
    builder = StateBuilder(state)
    
    if 'messages' in kwargs:
        builder = StateBuilder()  # 重置消息
        builder.add_messages(kwargs['messages'])
    
    if 'metadata' in kwargs:
        builder.update_metadata(kwargs['metadata'])
    
    if 'fields' in kwargs:
        builder.update_fields(kwargs['fields'])
    
    return builder.build()