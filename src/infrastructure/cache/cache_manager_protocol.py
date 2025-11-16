"""缓存管理器协议 - 避免基础设施层直接依赖展示层"""

from typing import Any, Optional, Dict, Protocol


class CacheManagerProtocol(Protocol):
    """缓存管理器协议 - 定义缓存管理器的基本接口
    
    该协议允许基础设施层的组件使用缓存功能，
    而不需要直接依赖展示层的具体实现。
    """
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        ...
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认值
            
        Returns:
            是否设置成功
        """
        ...
    
    async def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        ...
    
    async def clear(self) -> bool:
        """清空缓存
        
        Returns:
            是否清空成功
        """
        ...
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        ...