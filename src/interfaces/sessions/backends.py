"""会话存储后端接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ISessionStorageBackend(ABC):
    """会话存储后端接口 - 单一存储实现"""
    
    @abstractmethod
    async def save(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据字典
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，不存在返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有会话键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            会话ID列表
        """
        pass
    
    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭后端连接"""
        pass
