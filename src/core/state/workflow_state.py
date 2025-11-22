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
    """工作流状态实现"""
    
    messages: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
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