"""存储后端接口

定义存储后端的抽象接口，支持不同的存储实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IStorageBackend(ABC):
    """存储后端接口
    
    定义存储后端的抽象操作，支持不同的存储实现。
    """
    
    @abstractmethod
    async def save_impl(self, data: Dict[str, Any]) -> str:
        """保存数据
        
        Args:
            data: 要保存的数据
            
        Returns:
            str: 保存的数据ID
        """
        pass
    
    @abstractmethod
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            id: 数据ID
            
        Returns:
            Optional[Dict[str, Any]]: 加载的数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def list_impl(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出数据
        
        Args:
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 数据列表
        """
        pass
    
    @abstractmethod
    async def delete_impl(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists_impl(self, id: str) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    async def clear_impl(self) -> bool:
        """清空所有数据
        
        Returns:
            bool: 是否清空成功
        """
        pass