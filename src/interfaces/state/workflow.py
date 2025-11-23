"""
工作流状态接口定义

提供类型安全的状态管理接口，支持不可变状态模式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime


class IWorkflowState(Protocol):
    """工作流状态接口
    
    继承自 IState 接口，提供工作流特定的功能。
    注意：这是一个向后兼容的接口，新代码应该直接使用 IState。
    """
    
    # 继承 IState 的所有方法和属性
    # 这里保持 Protocol 定义以确保类型检查兼容性
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """从状态中获取数据（继承自 IState）"""
        ...
    
    def set_data(self, key: str, value: Any) -> None:
        """在状态中设置数据（继承自 IState）"""
        ...
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """从状态中获取元数据（继承自 IState）"""
        ...
    
    def set_metadata(self, key: str, value: Any) -> None:
        """在状态中设置元数据（继承自 IState）"""
        ...
    
    def get_id(self) -> Optional[str]:
        """获取状态ID（继承自 IState）"""
        ...
    
    def set_id(self, id: str) -> None:
        """设置状态ID（继承自 IState）"""
        ...
    
    def get_created_at(self) -> datetime:
        """获取创建时间戳（继承自 IState）"""
        ...
    
    def get_updated_at(self) -> datetime:
        """获取最后更新时间戳（继承自 IState）"""
        ...
    
    def is_complete(self) -> bool:
        """检查状态是否完成（继承自 IState）"""
        ...
    
    def mark_complete(self) -> None:
        """将状态标记为完成（继承自 IState）"""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典表示（继承自 IState）"""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IWorkflowState':
        """从字典创建状态实例（继承自 IState）"""
        ...
    
    # IWorkflowState 特有的属性
    @property
    def messages(self) -> List[Any]:
        """消息列表"""
        ...
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据字典"""
        ...
    
    @property
    def fields(self) -> Dict[str, Any]:
        """字段字典"""
        ...
    
    @property
    def created_at(self) -> datetime:
        """创建时间"""
        ...
    
    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        ...
    
    # IWorkflowState 特有的方法
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