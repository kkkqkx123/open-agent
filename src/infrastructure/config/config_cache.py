"""配置缓存管理

提供线程安全的配置缓存功能。
"""

from ..utils.cache import Cache


class ConfigCache:
    """配置缓存管理器 - 向后兼容适配器
    
    注意：此类已迁移到 src/infrastructure/utils/cache.py
    建议直接使用新的 Cache 工具类。
    """
    
    def __init__(self):
        """初始化配置缓存"""
        self._cache = Cache("config")
    
    def get(self, key: str):
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        return self._cache.get(key)
    
    def set(self, key: str, value) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        self._cache.set(key, value)
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
    
    def remove(self, key: str) -> bool:
        """移除指定缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功移除
        """
        return self._cache.remove(key)
    
    def remove_by_pattern(self, pattern: str) -> int:
        """根据模式移除缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            移除的缓存项数量
        """
        return self._cache.remove_by_pattern(pattern)
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        return self._cache.size()
    
    def keys(self) -> list:
        """获取所有缓存键
        
        Returns:
            缓存键列表
        """
        return self._cache.keys()
    
    def has(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        return self._cache.has(key)