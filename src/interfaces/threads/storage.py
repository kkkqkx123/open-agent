"""线程仓储接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.core.threads.entities import Thread, ThreadStatus


class IThreadRepository(ABC):
    """线程仓储接口 - 协调所有线程存储操作"""
    
    @abstractmethod
    async def create(self, thread: 'Thread') -> bool:
        """创建线程
        
        Args:
            thread: 线程实体
            
        Returns:
            是否创建成功
        """
        pass
    
    @abstractmethod
    async def get(self, thread_id: str) -> Optional['Thread']:
        """获取线程
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程实体，不存在返回None
        """
        pass
    
    @abstractmethod
    async def update(self, thread: 'Thread') -> bool:
        """更新线程
        
        Args:
            thread: 线程实体
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete(self, thread_id: str) -> bool:
        """删除线程
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_by_session(self, session_id: str) -> List['Thread']:
        """按会话列线程
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程列表
        """
        pass
    
    @abstractmethod
    async def list_by_status(self, status: 'ThreadStatus') -> List['Thread']:
        """按状态列线程
        
        Args:
            status: 线程状态
            
        Returns:
            线程列表
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        session_id: Optional[str] = None, 
        limit: int = 10
    ) -> List['Thread']:
        """搜索线程
        
        Args:
            query: 查询字符串
            session_id: 会话ID过滤（可选）
            limit: 返回数量限制
            
        Returns:
            线程列表
        """
        pass
    
    @abstractmethod
    async def get_count_by_session(self, session_id: str) -> int:
        """获取会话的线程数量
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程数量
        """
        pass
    
    @abstractmethod
    async def cleanup_old(self, max_age_days: int = 30) -> int:
        """清理旧线程
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的线程数量
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