"""会话存储适配器接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.interfaces.common import AbstractSessionData, AbstractSessionStatus


class ISessionStore(ABC):
    """会话存储适配器接口"""
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[AbstractSessionData]:
        """获取会话"""
        pass
    
    @abstractmethod
    async def create_session(self, session: AbstractSessionData) -> bool:
        """创建会话"""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, session: AbstractSessionData) -> bool:
        """更新会话"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass
    
    @abstractmethod
    async def list_sessions_by_status(self, status: AbstractSessionStatus) -> List[AbstractSessionData]:
        """按状态列会话"""
        pass
    
    @abstractmethod
    async def list_sessions_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[AbstractSessionData]:
        """按日期范围列会话"""
        pass
    
    @abstractmethod
    async def search_sessions(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[AbstractSessionData]:
        """搜索会话"""
        pass
    
    @abstractmethod
    async def get_session_count_by_status(self) -> Dict[str, int]:
        """获取各状态会话数量"""
        pass
    
    @abstractmethod
    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """清理旧会话"""
        pass