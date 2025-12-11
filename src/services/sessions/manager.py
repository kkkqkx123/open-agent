"""Session管理器服务 - 简化适配器"""

import uuid
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

from src.core.sessions.entities import SessionStatus, UserRequestEntity

if TYPE_CHECKING:
    from .service import SessionService

logger = get_logger(__name__)


class SessionManager:
    """Session管理器 - SessionService 的适配器
    
    提供与 ISessionManager 接口兼容的方法，内部代理给 SessionService
    """
    
    def __init__(
        self, 
        session_service: Optional['SessionService'] = None
    ):
        """初始化Session管理器
        
        Args:
            session_service: 会话服务实例（可选）
        """
        self._session_service = session_service
    
    async def create_session(
        self, 
        graph_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建新会话"""
        if self._session_service:
            user_request = UserRequestEntity(
                request_id=f"req_{uuid.uuid4().hex[:8]}",
                user_id=None,
                content=f"创建会话: graph={graph_id}, thread={thread_id}",
                metadata={
                    "graph_id": graph_id, 
                    "thread_id": thread_id, 
                    **(metadata or {}), 
                    "config": config
                },
                timestamp=datetime.now()
            )
            return await self._session_service.create_session(user_request)
        
        return str(uuid.uuid4())
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if self._session_service:
            return await self._session_service.get_session_info(session_id)
        return None
    
    async def update_session(
        self, 
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """更新会话信息"""
        if self._session_service:
            try:
                return await self._session_service.update_session_metadata(
                    session_id, 
                    updates
                )
            except Exception as e:
                logger.error(f"Failed to update session {session_id}: {e}")
                return False
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if self._session_service:
            try:
                return await self._session_service.delete_session(session_id)
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
                return False
        return False
    
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出会话"""
        if self._session_service:
            try:
                return await self._session_service.list_sessions()
            except Exception as e:
                logger.error(f"Failed to list sessions: {e}")
                return []
        return []
    
    async def update_session_status(
        self, 
        session_id: str,
        new_status: str
    ) -> bool:
        """更新会话状态"""
        if self._session_service:
            try:
                return await self._session_service.update_session_metadata(
                    session_id,
                    {"status": new_status}
                )
            except Exception as e:
                logger.error(f"Failed to update session status {session_id}: {e}")
                return False
        return False
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        if self._session_service:
            try:
                return await self._session_service.get_session_summary(session_id)
            except Exception as e:
                logger.error(f"Failed to get session summary {session_id}: {e}")
                return None
        return None
    
    async def archive_session(self, session_id: str) -> bool:
        """归档会话"""
        return await self.update_session_status(session_id, SessionStatus.ARCHIVED.value)
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """获取活动会话列表"""
        if self._session_service:
            try:
                return await self._session_service.list_sessions_by_status(
                    SessionStatus.ACTIVE.value
                )
            except Exception as e:
                logger.error(f"Failed to get active sessions: {e}")
                return []
        return []
    
    async def get_session_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """获取会话数量"""
        sessions = await self.list_sessions(filters)
        return len(sessions)
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        if self._session_service:
            try:
                return await self._session_service.session_exists(session_id)
            except Exception as e:
                logger.error(f"Failed to check session existence {session_id}: {e}")
                return False
        return False
