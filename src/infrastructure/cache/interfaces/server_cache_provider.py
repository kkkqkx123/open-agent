"""基础设施层服务器端缓存接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict


class IServerCacheProvider(ABC):
    """服务器端缓存提供者接口"""
    
    @abstractmethod
    def create_cache(self, contents: List[Any], **kwargs) -> Any:
        """
        创建服务器端缓存
        
        Args:
            contents: 要缓存的内容列表
            **kwargs: 其他参数（system_instruction, ttl, display_name等）
            
        Returns:
            创建的缓存对象
        """
        pass
    
    @abstractmethod
    def get_cache(self, cache_name: str) -> Optional[Any]:
        """
        获取缓存对象
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            缓存对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def use_cache(self, cache_name: str, contents: Any) -> Any:
        """
        使用服务器端缓存生成内容
        
        Args:
            cache_name: 缓存名称
            contents: 查询内容
            
        Returns:
            生成的内容响应
        """
        pass
    
    @abstractmethod
    def delete_cache(self, cache_name: str) -> bool:
        """
        删除缓存
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def list_caches(self) -> List[Any]:
        """
        列出所有缓存
        
        Returns:
            缓存对象列表
        """
        pass
    
    @abstractmethod
    def cleanup_expired_caches(self) -> int:
        """
        清理过期的缓存
        
        Returns:
            清理的缓存数量
        """
        pass
    
    @abstractmethod
    def get_or_create_cache(self, contents: List[Any], **kwargs) -> Any:
        """
        获取或创建缓存
        
        Args:
            contents: 要缓存的内容列表
            **kwargs: 其他参数
            
        Returns:
            缓存对象
        """
        pass
    
    @abstractmethod
    def should_use_server_cache(self, contents: List[Any], threshold: int = 1048576) -> bool:
        """
        判断是否应该使用服务器端缓存
        
        Args:
            contents: 内容列表
            threshold: 大小阈值（字节）
            
        Returns:
            是否应该使用服务器端缓存
        """
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        pass