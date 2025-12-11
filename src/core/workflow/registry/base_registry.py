"""注册表基础抽象类

提供统一的注册表基础实现，包含通用的注册、获取、管理功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from src.interfaces.logger import ILogger
from src.interfaces.dependency_injection import get_logger


class IRegistry(ABC):
    """注册表基础接口"""
    
    @abstractmethod
    def register(self, name: str, item: Any) -> None:
        """注册项目"""
        pass
    
    @abstractmethod
    def get(self, name: str) -> Optional[Any]:
        """获取项目"""
        pass
    
    @abstractmethod
    def unregister(self, name: str) -> bool:
        """注销项目"""
        pass
    
    @abstractmethod
    def list_items(self) -> List[str]:
        """列出所有项目"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有项目"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
    
    @abstractmethod
    def validate_item(self, name: str, item: Any) -> None:
        """验证项目"""
        pass


class BaseRegistry(IRegistry):
    """注册表基础实现"""
    
    def __init__(self, registry_name: str):
        """初始化注册表
        
        Args:
            registry_name: 注册表名称，用于日志记录
        """
        self._registry_name = registry_name
        self._items: Dict[str, Any] = {}
        # 通过依赖注入获取日志记录器
        self._logger = get_logger(f"{__name__}.{registry_name}")
        self._created_at = datetime.now()
        self._last_updated = datetime.now()
    
    def register(self, name: str, item: Any) -> None:
        """注册项目
        
        Args:
            name: 项目名称
            item: 项目对象
            
        Raises:
            ValueError: 项目验证失败
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"{self._registry_name}名称必须是非空字符串")
        
        # 验证项目
        self.validate_item(name, item)
        
        # 检查是否已存在
        if name in self._items:
            self._logger.warning(f"{self._registry_name} '{name}' 已存在，将被覆盖")
        
        self._items[name] = item
        self._last_updated = datetime.now()
        self._logger.debug(f"注册 {self._registry_name}: {name}")
    
    def get(self, name: str) -> Optional[Any]:
        """获取项目
        
        Args:
            name: 项目名称
            
        Returns:
            Optional[Any]: 项目对象，如果不存在返回None
        """
        return self._items.get(name)
    
    def unregister(self, name: str) -> bool:
        """注销项目
        
        Args:
            name: 项目名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._items:
            del self._items[name]
            self._last_updated = datetime.now()
            self._logger.debug(f"注销 {self._registry_name}: {name}")
            return True
        return False
    
    def list_items(self) -> List[str]:
        """列出所有项目名称
        
        Returns:
            List[str]: 项目名称列表
        """
        return list(self._items.keys())
    
    def clear(self) -> None:
        """清除所有项目"""
        count = len(self._items)
        self._items.clear()
        self._last_updated = datetime.now()
        self._logger.debug(f"清除所有 {self._registry_name} (共 {count} 个)")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "registry_name": self._registry_name,
            "total_items": len(self._items),
            "created_at": self._created_at.isoformat(),
            "last_updated": self._last_updated.isoformat(),
            "items": list(self._items.keys())
        }
    
    def validate_item(self, name: str, item: Any) -> None:
        """验证项目
        
        Args:
            name: 项目名称
            item: 项目对象
            
        Raises:
            ValueError: 项目验证失败
        """
        if item is None:
            raise ValueError(f"{self._registry_name}项目不能为None")
    
    def has_item(self, name: str) -> bool:
        """检查项目是否存在
        
        Args:
            name: 项目名称
            
        Returns:
            bool: 项目是否存在
        """
        return name in self._items
    
    def size(self) -> int:
        """获取注册表大小
        
        Returns:
            int: 注册表中的项目数量
        """
        return len(self._items)
    
    def is_empty(self) -> bool:
        """检查注册表是否为空
        
        Returns:
            bool: 注册表是否为空
        """
        return len(self._items) == 0
    
    def get_item_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取项目信息
        
        Args:
            name: 项目名称
            
        Returns:
            Optional[Dict[str, Any]]: 项目信息，如果不存在返回None
        """
        item = self.get(name)
        if item is None:
            return None
        
        return {
            "name": name,
            "type": type(item).__name__,
            "module": item.__class__.__module__,
            "registry": self._registry_name
        }


class TypedRegistry(BaseRegistry):
    """类型化注册表
    
    支持按类型分类管理的注册表。
    """
    
    def __init__(self, registry_name: str, type_categories: Optional[List[str]] = None):
        """初始化类型化注册表
        
        Args:
            registry_name: 注册表名称
            type_categories: 类型分类列表
        """
        super().__init__(registry_name)
        self._type_categories = type_categories or []
        self._items_by_type: Dict[str, List[str]] = {}
        
        # 初始化类型分类
        for category in self._type_categories:
            self._items_by_type[category] = []
    
    def register_with_type(self, name: str, item: Any, item_type: str) -> None:
        """按类型注册项目
        
        Args:
            name: 项目名称
            item: 项目对象
            item_type: 项目类型
        """
        super().register(name, item)
        
        # 按类型分类
        if item_type not in self._items_by_type:
            self._items_by_type[item_type] = []
        
        if name not in self._items_by_type[item_type]:
            self._items_by_type[item_type].append(name)
    
    def get_items_by_type(self, item_type: str) -> List[Any]:
        """按类型获取项目列表
        
        Args:
            item_type: 项目类型
            
        Returns:
            List[Any]: 项目列表
        """
        item_names = self._items_by_type.get(item_type, [])
        return [self.get(name) for name in item_names if self.has_item(name)]
    
    def list_items_by_type(self, item_type: str) -> List[str]:
        """按类型列出项目名称
        
        Args:
            item_type: 项目类型
            
        Returns:
            List[str]: 项目名称列表
        """
        return self._items_by_type.get(item_type, [])
    
    def get_type_categories(self) -> List[str]:
        """获取所有类型分类
        
        Returns:
            List[str]: 类型分类列表
        """
        return list(self._items_by_type.keys())
    
    def unregister(self, name: str) -> bool:
        """注销项目
        
        Args:
            name: 项目名称
            
        Returns:
            bool: 是否成功注销
        """
        if not super().unregister(name):
            return False
        
        # 从类型分类中移除
        for item_type, item_names in self._items_by_type.items():
            if name in item_names:
                item_names.remove(name)
        
        return True
    
    def clear(self) -> None:
        """清除所有项目"""
        super().clear()
        
        # 清除类型分类
        for category in self._items_by_type:
            self._items_by_type[category].clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = super().get_stats()
        stats["type_distribution"] = {
            item_type: len(item_names)
            for item_type, item_names in self._items_by_type.items()
        }
        stats["type_categories"] = self.get_type_categories()
        return stats