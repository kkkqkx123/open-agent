"""线程存储后端接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadStorageBackend(ABC):
    """线程存储后端接口 - 单一存储实现"""
    
    @abstractmethod
    async def save(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据
        
        Args:
            thread_id: 线程ID
            data: 线程数据字典
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程数据，不存在返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, thread_id: str) -> bool:
        """删除线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有线程键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            线程ID列表
        """
        pass
    
    @abstractmethod
    async def exists(self, thread_id: str) -> bool:
        """检查线程是否存在
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭后端连接"""
        pass
