"""
工作流状态接口定义

提供类型安全的状态管理接口，支持不可变状态模式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime


class IWorkflowState(Protocol):
    """工作流状态接口"""
    
    messages: List[Any]
    metadata: Dict[str, Any]
    fields: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def with_messages(self, messages: List[Any]) -> 'IWorkflowState':
        """创建包含新消息的状态"""
        ...
    
    def with_metadata(self, metadata: Dict[str, Any]) -> 'IWorkflowState':
        """创建包含新元数据的状态"""
        ...
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        ...
    
    def set_field(self, key: str, value: Any) -> 'IWorkflowState':
        """创建包含新字段值的状态"""
        ...
    
    def copy(self) -> 'IWorkflowState':
        """创建状态的深拷贝"""
        ...


class IStateBuilder(ABC):
    """状态构建器接口"""
    
    @abstractmethod
    def add_message(self, message: Any) -> 'IStateBuilder':
        """添加消息"""
        pass
    
    @abstractmethod
    def add_messages(self, messages: List[Any]) -> 'IStateBuilder':
        """添加多个消息"""
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> 'IStateBuilder':
        """设置元数据"""
        pass
    
    @abstractmethod
    def update_metadata(self, metadata: Dict[str, Any]) -> 'IStateBuilder':
        """更新元数据"""
        pass
    
    @abstractmethod
    def set_field(self, key: str, value: Any) -> 'IStateBuilder':
        """设置字段"""
        pass
    
    @abstractmethod
    def update_fields(self, fields: Dict[str, Any]) -> 'IStateBuilder':
        """更新多个字段"""
        pass
    
    @abstractmethod
    def build(self) -> IWorkflowState:
        """构建状态"""
        pass


class IStateValidator(ABC):
    """状态验证器接口"""
    
    @abstractmethod
    def validate_state(self, state: IWorkflowState) -> List[str]:
        """验证状态，返回错误列表"""
        pass
    
    @abstractmethod
    def validate_field(self, key: str, value: Any) -> Optional[str]:
        """验证字段，返回错误信息"""
        pass