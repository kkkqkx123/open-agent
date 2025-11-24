"""基础状态实现

提供状态的基础实现，所有具体状态类型都可以继承此类。
"""

import uuid
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from ..core.base import BaseState
from ..interfaces.base import IState


logger = logging.getLogger(__name__)


class BaseStateImpl(BaseState):
    """基础状态实现类
    
    提供状态的基础功能实现，所有具体状态类型都可以继承此类。
    """
    
    def __init__(self, **kwargs):
        """初始化基础状态实现"""
        super().__init__(**kwargs)
        
        # 如果没有提供ID，生成一个
        if not self._id:
            self._id = f"state_{uuid.uuid4().hex[:8]}"
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._id = id
        self._updated_at = datetime.now()
    
    def update_data(self, updates: Dict[str, Any]) -> None:
        """批量更新状态数据
        
        Args:
            updates: 更新的数据字典
        """
        self._data.update(updates)
        self._updated_at = datetime.now()
    
    def clear_data(self) -> None:
        """清空状态数据"""
        self._data.clear()
        self._updated_at = datetime.now()
    
    def has_data(self, key: str) -> bool:
        """检查是否包含指定数据
        
        Args:
            key: 数据键
            
        Returns:
            是否包含
        """
        return key in self._data
    
    def get_data_keys(self) -> list:
        """获取所有数据键
        
        Returns:
            数据键列表
        """
        return list(self._data.keys())
    
    def get_data_size(self) -> int:
        """获取数据大小
        
        Returns:
            数据项数量
        """
        return len(self._data)
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """批量更新元数据
        
        Args:
            updates: 更新的元数据字典
        """
        self._metadata.update(updates)
        self._updated_at = datetime.now()
    
    def clear_metadata(self) -> None:
        """清空元数据"""
        self._metadata.clear()
        self._updated_at = datetime.now()
    
    def has_metadata(self, key: str) -> bool:
        """检查是否包含指定元数据
        
        Args:
            key: 元数据键
            
        Returns:
            是否包含
        """
        return key in self._metadata
    
    def get_metadata_keys(self) -> list:
        """获取所有元数据键
        
        Returns:
            元数据键列表
        """
        return list(self._metadata.keys())
    
    def get_metadata_size(self) -> int:
        """获取元数据大小
        
        Returns:
            元数据项数量
        """
        return len(self._metadata)
    
    def clone(self) -> 'BaseStateImpl':
        """创建状态克隆
        
        Returns:
            克隆的状态实例
        """
        cloned_data = self.to_dict()
        return self.from_dict(cloned_data)
    
    def merge(self, other: IState) -> 'BaseStateImpl':
        """合并另一个状态
        
        Args:
            other: 另一个状态
            
        Returns:
            合并后的状态实例
        """
        if not isinstance(other, IState):
            raise ValueError("只能合并IState实例")
        
        # 合并数据
        other_data = other.to_dict().get('data', {})
        self._data.update(other_data)
        
        # 合并元数据
        other_metadata = other.to_dict().get('metadata', {})
        self._metadata.update(other_metadata)
        
        self._updated_at = datetime.now()
        return self
    
    def get_age(self) -> float:
        """获取状态年龄（秒）
        
        Returns:
            状态年龄
        """
        return (datetime.now() - self._created_at).total_seconds()
    
    def get_last_modified_age(self) -> float:
        """获取最后修改年龄（秒）
        
        Returns:
            最后修改年龄
        """
        return (datetime.now() - self._updated_at).total_seconds()
    
    def is_recent(self, max_age_seconds: float = 300) -> bool:
        """检查是否为最近创建的状态
        
        Args:
            max_age_seconds: 最大年龄（秒）
            
        Returns:
            是否为最近创建
        """
        return self.get_age() <= max_age_seconds
    
    def is_recently_modified(self, max_age_seconds: float = 60) -> bool:
        """检查是否为最近修改的状态
        
        Args:
            max_age_seconds: 最大年龄（秒）
            
        Returns:
            是否为最近修改
        """
        return self.get_last_modified_age() <= max_age_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data": self._data,
            "metadata": self._metadata,
            "id": self._id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "complete": self._complete,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseStateImpl':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        # 处理时间
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        return instance
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(id={self._id}, complete={self._complete})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"{self.__class__.__name__}(id={self._id}, "
                f"created_at={self._created_at.isoformat()}, "
                f"updated_at={self._updated_at.isoformat()}, "
                f"complete={self._complete}, "
                f"data_size={len(self._data)}, "
                f"metadata_size={len(self._metadata)})")
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, BaseStateImpl):
            return False
        
        return (self._id == other._id and 
                self._data == other._data and 
                self._metadata == other._metadata and
                self._complete == other._complete)
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self._id) if self._id else hash(id(self))