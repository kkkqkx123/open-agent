"""配置缓存管理

提供线程安全的配置缓存功能。
"""

import threading
from typing import Dict, Any, Optional


class ConfigCache:
    """配置缓存管理器"""
    
    def __init__(self):
        """初始化配置缓存"""
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