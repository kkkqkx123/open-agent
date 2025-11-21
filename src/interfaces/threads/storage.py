"""线程存储适配器接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.entities import Thread, ThreadStatus


class IThreadStore(ABC):
    """线程存储适配器接口"""
    
    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """获取线程"""
        pass
    
    @abstractmethod
    async def create_thread(self, thread: Thread) -> bool:
        """创建线程"""
        pass
    
    @abstractmethod
    async def update_thread(self, thread_id: str, thread: Thread) -> bool:
        """更新线程"""
        pass
    
    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程"""
        pass
    
    @abstractmethod
    async def list_threads_by_session(self, session_id: str) -> List[Thread]:
        """按会话列线程"""
        pass
    
    @abstractmethod
    async def list_threads_by_status(self, status: ThreadStatus) -> List[Thread]:
        """按状态列线程"""
        pass
    
    @abstractmethod
    async def get_thread_by_checkpoint(self, checkpoint_id: str) -> Optional[Thread]:
        """按检查点获取线程"""
        pass
    
    @abstractmethod
    async def search_threads(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Thread]:
        """搜索线程"""
        pass
    
    @abstractmethod
    async def get_thread_count_by_session(self, session_id: str) -> int:
        """获取会话线程数量"""
        pass
    
    @abstractmethod
    async def cleanup_old_threads(self, max_age_days: int = 30) -> int:
        """清理旧线程"""
        pass