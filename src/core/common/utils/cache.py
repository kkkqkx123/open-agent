"""通用缓存工具

提供线程安全的缓存功能，可被多个模块使用。
"""

import threading
from typing import Dict, Any, Optional


class Cache:
    """通用缓存管理器"""
    
    def __init__(self, name: str = "default"):
        """初始化缓存
        
        Args:
            name: 缓存名称，用于标识不同的缓存实例
        """
        self.name = name
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        with self._lock:
            return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            self._cache[key] = value
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def remove(self, key: str) -> bool:
        """移除指定缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def remove_by_pattern(self, pattern: str) -> int:
        """根据模式移除缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            移除的缓存项数量
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list:
        """获取所有缓存键
        
        Returns:
            缓存键列表
        """
        with self._lock:
            return list(self._cache.keys())
    
    def has(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            return key in self._cache
    
    def get_or_set(self, key: str, factory_func) -> Any:
        """获取缓存值，如果不存在则通过工厂函数创建
        
        Args:
            key: 缓存键
            factory_func: 工厂函数，用于创建缓存值
            
        Returns:
            缓存值
        """
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            
            value = factory_func()
            self._cache[key] = value
            return value
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._lock:
            return {
                "name": self.name,
                "size": len(self._cache),
                "keys": list(self._cache.keys())
            }