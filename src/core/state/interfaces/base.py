"""基础状态接口定义

定义状态管理系统的基础接口，所有状态对象和管理器必须遵循此接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class IState(ABC):
    """统一状态接口
    
    定义状态对象的基本契约，所有状态实现必须遵循此接口。
    这是纯粹的状态抽象，不包含特定于任何执行引擎的功能。
    """
    
    # 基础状态操作
    @abstractmethod
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据"""
        pass
    
    @abstractmethod
    def set_data(self, key: str, value: Any) -> None:
        """设置状态数据"""
        pass
    
    @abstractmethod
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        pass
    
    # 生命周期管理
    @abstractmethod
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        pass
    
    @abstractmethod
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """检查是否完成"""
        pass
    
    @abstractmethod
    def mark_complete(self) -> None:
        """标记为完成"""
        pass
    
    # 序列化支持
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IState':
        """从字典创建状态"""
        pass


class IStateManager(ABC):
    """统一状态管理器接口"""
    
    @abstractmethod
    def create_state(self, state_type: str, **kwargs) -> IState:
        """创建状态"""
        pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> Optional[IState]:
        """获取状态"""
        pass
    
    @abstractmethod
    def save_state(self, state: IState) -> bool:
        """保存状态"""
        pass
    
    @abstractmethod
    def delete_state(self, state_id: str) -> bool:
        """删除状态"""
        pass
    
    @abstractmethod
    def list_states(self, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """列出状态ID"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass


class IStateSerializer(ABC):
    """状态序列化器接口"""
    
    @abstractmethod
    def serialize(self, state: IState) -> Union[str, bytes]:
        """序列化状态"""
        pass
    
    @abstractmethod
    def deserialize(self, data: Union[str, bytes]) -> IState:
        """反序列化状态"""
        pass


class IStateValidator(ABC):
    """状态验证器接口"""
    
    @abstractmethod
    def validate_state(self, state: IState) -> List[str]:
        """验证状态，返回错误列表"""
        pass
    
    @abstractmethod
    def validate_state_data(self, data: Dict[str, Any]) -> List[str]:
        """验证状态数据"""
        pass


class IStateLifecycleManager(ABC):
    """状态生命周期管理器接口"""
    
    @abstractmethod
    def register_state(self, state: IState) -> None:
        """注册状态"""
        pass
    
    @abstractmethod
    def unregister_state(self, state_id: str) -> None:
        """注销状态"""
        pass
    
    @abstractmethod
    def on_state_saved(self, state: IState) -> None:
        """状态保存事件"""
        pass
    
    @abstractmethod
    def on_state_deleted(self, state_id: str) -> None:
        """状态删除事件"""
        pass
    
    @abstractmethod
    def on_state_error(self, state: IState, error: Exception) -> None:
        """状态错误事件"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass


class IStateCache(ABC):
    """状态缓存接口"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[IState]:
        """获取缓存状态"""
        pass
    
    @abstractmethod
    def put(self, key: str, state: IState) -> None:
        """设置缓存状态"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存状态"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """获取缓存大小"""
        pass
    
    @abstractmethod
    def get_all_keys(self) -> List[str]:
        """获取所有键"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        pass
    
    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, IState]:
        """批量获取缓存状态"""
        pass
    
    @abstractmethod
    def set_many(self, states: Dict[str, IState]) -> None:
        """批量设置缓存状态"""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """清理过期缓存项"""
        pass


class IStateStorageAdapter(ABC):
    """状态存储适配器接口"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Union[str, bytes]]:
        """获取存储数据"""
        pass
    
    @abstractmethod
    def save(self, key: str, data: Union[str, bytes]) -> bool:
        """保存存储数据"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除存储数据"""
        pass
    
    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """列出所有键"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        pass

