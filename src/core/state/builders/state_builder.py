"""基础状态构建器

提供构建状态对象的基础构建器类。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from src.interfaces.state.base import IState
else:
    from src.interfaces.state.base import IState

T = TypeVar('T', bound=IState)


class StateBuilder(Generic[T], ABC):
    """基础状态构建器抽象类
    
    提供构建状态对象的通用接口和方法。
    """
    
    def __init__(self) -> None:
        """初始化构建器"""
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._id: Optional[str] = None
        self._created_at: Optional[datetime] = None
        self._updated_at: Optional[datetime] = None
        self._complete: bool = False
    
    @abstractmethod
    def build(self) -> T:
        """构建状态对象
        
        Returns:
            T: 状态对象
        """
        pass
    
    def with_data(self, data: Dict[str, Any]) -> "StateBuilder[T]":
        """设置状态数据
        
        Args:
            data: 状态数据字典
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._data.update(data)
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> "StateBuilder[T]":
        """设置元数据
        
        Args:
            metadata: 元数据字典
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._metadata.update(metadata)
        return self
    
    def with_id(self, id: str) -> "StateBuilder[T]":
        """设置状态ID
        
        Args:
            id: 状态ID
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._id = id
        return self
    
    def with_created_at(self, created_at: datetime) -> "StateBuilder[T]":
        """设置创建时间
        
        Args:
            created_at: 创建时间
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._created_at = created_at
        return self
    
    def with_updated_at(self, updated_at: datetime) -> "StateBuilder[T]":
        """设置更新时间
        
        Args:
            updated_at: 更新时间
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._updated_at = updated_at
        return self
    
    def mark_complete(self) -> "StateBuilder[T]":
        """标记为完成
        
        Returns:
            StateBuilder: 构建器实例
        """
        self._complete = True
        return self
    
    def mark_incomplete(self) -> "StateBuilder[T]":
        """标记为未完成
        
        Returns:
            StateBuilder: 构建器实例
        """
        self._complete = False
        return self
    
    def add_data(self, key: str, value: Any) -> "StateBuilder[T]":
        """添加状态数据
        
        Args:
            key: 数据键
            value: 数据值
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._data[key] = value
        return self
    
    def add_metadata(self, key: str, value: Any) -> "StateBuilder[T]":
        """添加元数据
        
        Args:
            key: 元数据键
            value: 元数据值
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._metadata[key] = value
        return self
    
    def remove_data(self, key: str) -> "StateBuilder[T]":
        """移除状态数据
        
        Args:
            key: 数据键
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._data.pop(key, None)
        return self
    
    def remove_metadata(self, key: str) -> "StateBuilder[T]":
        """移除元数据
        
        Args:
            key: 元数据键
            
        Returns:
            StateBuilder: 构建器实例
        """
        self._metadata.pop(key, None)
        return self
    
    def clear_data(self) -> "StateBuilder[T]":
        """清除所有状态数据
        
        Returns:
            StateBuilder: 构建器实例
        """
        self._data.clear()
        return self
    
    def clear_metadata(self) -> "StateBuilder[T]":
        """清除所有元数据
        
        Returns:
            StateBuilder: 构建器实例
        """
        self._metadata.clear()
        return self
    
    def reset(self) -> "StateBuilder[T]":
        """重置构建器
        
        Returns:
            StateBuilder: 构建器实例
        """
        self._data.clear()
        self._metadata.clear()
        self._id = None
        self._created_at = None
        self._updated_at = None
        self._complete = False
        return self
    
    def get_data(self) -> Dict[str, Any]:
        """获取当前状态数据
        
        Returns:
            Dict[str, Any]: 状态数据字典
        """
        return self._data.copy()
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取当前元数据
        
        Returns:
            Dict[str, Any]: 元数据字典
        """
        return self._metadata.copy()
    
    def get_id(self) -> Optional[str]:
        """获取当前状态ID
        
        Returns:
            Optional[str]: 状态ID
        """
        return self._id
    
    def is_complete(self) -> bool:
        """检查是否标记为完成
        
        Returns:
            bool: 是否完成
        """
        return self._complete
    
    def _prepare_build_args(self) -> Dict[str, Any]:
        """准备构建参数
        
        Returns:
            Dict[str, Any]: 构建参数字典
        """
        args = {
            "data": self._data.copy(),
            "metadata": self._metadata.copy(),
            "complete": self._complete
        }
        
        if self._id:
            args["id"] = self._id
        
        if self._created_at:
            args["created_at"] = self._created_at
        
        if self._updated_at:
            args["updated_at"] = self._updated_at
        
        return args
    
    def __enter__(self) -> "StateBuilder[T]":
        """上下文管理器入口
        
        Returns:
            StateBuilder: 构建器实例
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        pass


class BaseStateBuilder(StateBuilder[T]):
    """基础状态构建器实现
    
    提供基础状态构建器的具体实现。
    """
    
    def __init__(self, state_class: Type[T]) -> None:
        """初始化构建器
        
        Args:
            state_class: 状态类
        """
        super().__init__()
        self._state_class = state_class
    
    def build(self) -> T:
        """构建状态对象
        
        Returns:
            T: 状态对象
        """
        args = self._prepare_build_args()
        return self._state_class(**args)


# 便捷函数
def create_builder(state_class: Type[T]) -> StateBuilder[T]:
    """创建状态构建器的便捷函数
    
    Args:
        state_class: 状态类
        
    Returns:
        StateBuilder: 状态构建器实例
    """
    return BaseStateBuilder(state_class)