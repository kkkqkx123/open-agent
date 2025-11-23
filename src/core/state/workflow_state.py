"""
工作流状态实现

提供不可变的工作流状态实现，支持类型安全的状态操作
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...interfaces.state.workflow import IWorkflowState


@dataclass(frozen=True)
class WorkflowState(IWorkflowState):
    """工作流状态实现
    
    现在也实现了统一的 IState 接口功能。
    """
    
    messages: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # IState 接口的内部状态
    _id: Optional[str] = field(default=None, init=False)
    _complete: bool = field(default=False, init=False)
    _data: Dict[str, Any] = field(default_factory=dict, init=False)
    
    def with_messages(self, messages: List[Any]) -> 'WorkflowState':
        """创建包含新消息的状态"""
        return WorkflowState(
            messages=messages,
            metadata=self.metadata,
            fields=self.fields,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def with_metadata(self, metadata: Dict[str, Any]) -> 'WorkflowState':
        """创建包含新元数据的状态"""
        return WorkflowState(
            messages=self.messages,
            metadata=metadata,
            fields=self.fields,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        return self.fields.get(key, default)
    
    def set_field(self, key: str, value: Any) -> 'WorkflowState':
        """创建包含新字段值的状态"""
        new_fields = self.fields.copy()
        new_fields[key] = value
        return WorkflowState(
            messages=self.messages,
            metadata=self.metadata,
            fields=new_fields,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def copy(self) -> 'WorkflowState':
        """创建状态的深拷贝"""
        return WorkflowState(
            messages=self.messages.copy(),
            metadata=self.metadata.copy(),
            fields=self.fields.copy(),
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def __post_init__(self) -> None:
        """验证状态的一致性"""
        if not isinstance(self.messages, list):
            raise ValueError("messages 必须是列表类型")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata 必须是字典类型")
        if not isinstance(self.fields, dict):
            raise ValueError("fields 必须是字典类型")
    
    # IState 接口实现
    def get_data(self, key: str, default: Any = None) -> Any:
        """从状态中获取数据（IState 接口）"""
        return self._data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """在状态中设置数据（IState 接口）
        
        注意：由于这是不可变状态，这个操作会抛出异常
        """
        raise NotImplementedError("不可变状态不支持 set_data 操作，请使用 set_field")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """从状态中获取元数据（IState 接口）"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """在状态中设置元数据（IState 接口）
        
        注意：由于这是不可变状态，这个操作会抛出异常
        """
        raise NotImplementedError("不可变状态不支持 set_metadata 操作，请使用 with_metadata")
    
    def get_id(self) -> Optional[str]:
        """获取状态ID（IState 接口）"""
        return self._id
    
    def set_id(self, id: str) -> None:
        """设置状态ID（IState 接口）
        
        注意：由于这是不可变状态，这个操作会抛出异常
        """
        raise NotImplementedError("不可变状态不支持 set_id 操作")
    
    def get_created_at(self) -> datetime:
        """获取创建时间戳（IState 接口）"""
        return self.created_at
    
    def get_updated_at(self) -> datetime:
        """获取最后更新时间戳（IState 接口）"""
        return self.updated_at
    
    def is_complete(self) -> bool:
        """检查状态是否完成（IState 接口）"""
        return self._complete
    
    def mark_complete(self) -> None:
        """将状态标记为完成（IState 接口）
        
        注意：由于这是不可变状态，这个操作会抛出异常
        """
        raise NotImplementedError("不可变状态不支持 mark_complete 操作")
    
    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典表示（IState 接口）"""
        return {
            'messages': self.messages,
            'metadata': self.metadata,
            'fields': self.fields,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'id': self._id,
            'complete': self._complete,
            'data': self._data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """从字典创建状态实例（IState 接口）"""
        instance = cls(
            messages=data.get('messages', []),
            metadata=data.get('metadata', {}),
            fields=data.get('fields', {}),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now())
        )
        
        # 设置内部状态
        object.__setattr__(instance, '_id', data.get('id'))
        object.__setattr__(instance, '_complete', data.get('complete', False))
        object.__setattr__(instance, '_data', data.get('data', {}))
        
        return instance


class WorkflowStateValidator:
    """工作流状态验证器"""
    
    def validate_state(self, state: IWorkflowState) -> List[str]:
        """验证状态，返回错误列表"""
        errors = []
        
        # 验证消息列表
        if not isinstance(state.messages, list):
            errors.append("messages 必须是列表类型")
        
        # 验证元数据
        if not isinstance(state.metadata, dict):
            errors.append("metadata 必须是字典类型")
        
        # 验证字段
        if not isinstance(state.fields, dict):
            errors.append("fields 必须是字典类型")
        
        # 验证时间戳
        if not isinstance(state.created_at, datetime):
            errors.append("created_at 必须是 datetime 类型")
        
        if not isinstance(state.updated_at, datetime):
            errors.append("updated_at 必须是 datetime 类型")
        
        # 验证时间逻辑
        if state.updated_at < state.created_at:
            errors.append("updated_at 不能早于 created_at")
        
        return errors
    
    def validate_field(self, key: str, value: Any) -> Optional[str]:
        """验证字段，返回错误信息"""
        if not isinstance(key, str):
            return "字段键必须是字符串类型"
        
        if not key.strip():
            return "字段键不能为空"
        
        # 检查保留字段名
        reserved_keys = {'messages', 'metadata', 'fields', 'created_at', 'updated_at'}
        if key in reserved_keys:
            return f"字段键 '{key}' 是保留字段名"
        
        return None


def create_initial_state(
    messages: Optional[List[Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    fields: Optional[Dict[str, Any]] = None
) -> WorkflowState:
    """创建初始状态"""
    return WorkflowState(
        messages=messages or [],
        metadata=metadata or {},
        fields=fields or {}
    )


def create_state_from_dict(data: Dict[str, Any]) -> WorkflowState:
    """从字典创建状态"""
    return WorkflowState(
        messages=data.get('messages', []),
        metadata=data.get('metadata', {}),
        fields=data.get('fields', {}),
        created_at=data.get('created_at', datetime.now()),
        updated_at=data.get('updated_at', datetime.now())
    )