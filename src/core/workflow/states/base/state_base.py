"""状态基类

提供状态管理的基础接口和抽象实现。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.interfaces.state.interfaces import IState


class BaseState(IState, ABC):
    """状态基类
    
    提供状态管理的通用实现。
    """
    
    def __init__(self):
        """初始化状态"""
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._created_at: datetime = datetime.now()
        self._updated_at: datetime = datetime.now()
        self._id: Optional[str] = None
        self._complete: bool = False
    
    # IState interface implementation
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            Any: 状态数据
        """
        return self._data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置状态数据
        
        Args:
            key: 键名
            value: 值
        """
        self._data[key] = value
        self._updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            Any: 元数据
        """
        return self._metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        Args:
            key: 键名
            value: 值
        """
        self._metadata[key] = value
        self._updated_at = datetime.now()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID
        
        Returns:
            Optional[str]: 状态ID
        """
        return self._id
    
    def set_id(self, id: str) -> None:
        """设置状态ID
        
        Args:
            id: 状态ID
        """
        self._id = id
        self._updated_at = datetime.now()
    
    def get_created_at(self) -> datetime:
        """获取创建时间
        
        Returns:
            datetime: 创建时间
        """
        return self._created_at
    
    def get_updated_at(self) -> datetime:
        """获取更新时间
        
        Returns:
            datetime: 更新时间
        """
        return self._updated_at
    
    def is_complete(self) -> bool:
        """检查是否完成
        
        Returns:
            bool: 是否完成
        """
        return self._complete
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self._complete = True
        self._updated_at = datetime.now()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取数据（向后兼容）
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            Any: 数据
        """
        return self.get_data(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "data": self._data,
            "metadata": self._metadata,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "id": self._id,
            "complete": self._complete
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseState":
        """从字典创建状态
        
        Args:
            data: 字典数据
            
        Returns:
            BaseState: 状态实例
        """
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        return instance
    
    def clone(self) -> "BaseState":
        """克隆状态
        
        Returns:
            BaseState: 克隆的状态
        """
        return self.from_dict(self.to_dict())
    
    def merge(self, other: "BaseState") -> None:
        """合并另一个状态
        
        Args:
            other: 另一个状态
        """
        self._data.update(other._data)
        self._metadata.update(other._metadata)
        self._updated_at = datetime.now()
    
    def reset(self) -> None:
        """重置状态"""
        self._data.clear()
        self._metadata.clear()
        self._complete = False
        self._updated_at = datetime.now()