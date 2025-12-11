"""通用缓存接口定义

提供通用的缓存抽象接口，支持多种缓存场景。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List


class ICacheAdapter(ABC):
    """缓存适配器接口
    
    提供同步缓存操作接口。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），如果为None则使用默认值
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def get_all_keys(self) -> List[str]:
        """获取所有缓存键
        
        Returns:
            缓存键列表
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """清理过期的缓存项
        
        Returns:
            清理的项数量
        """
        pass


class ICacheKeyGenerator(ABC):
    """缓存键生成器接口
    
    定义缓存键生成的契约，支持多种键生成策略。
    """
    
    @abstractmethod
    def generate_key(self, *args, **kwargs) -> str:
        """生成缓存键
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        pass


__all__ = [
    "ICacheAdapter",
    "ICacheKeyGenerator"
]