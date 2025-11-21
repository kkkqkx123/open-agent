"""会话业务服务实现"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.core.sessions.interfaces import ISessionCore
from src.core.sessions.entities import SessionStatus
from src.interfaces.sessions import ISessionService, ISessionStore
from src.core.common.exceptions import EntityNotFoundError, ValidationError


class SessionService(ISessionService):
    """会话业务服务实现"""
    
    def __init__(
        self,
        session_core: ISessionCore,
        session_store: ISessionStore
    ):
        self._session_core = session_core
        self._session_store = session_store
    
    async def create_session_with_thread(
        self, 
        session_config: Dict[str, Any],
        thread_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建会话并关联线程"""
        try:
            # 创建会话实体
            session_id = await self._session_core.create_session(session_config)
            
            # 如果需要，创建关联线程
            if thread_config:
                # 这里简化处理，实际应用中可能需要调用线程服务
                pass
            
            return session_id
        except Exception as e:
            raise ValidationError(f"Failed to create session with thread: {str(e)}")
    
    async def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """更新会话元数据"""
        try:
            # 验证会话存在
            session = await self._session_store.get_session(session_id)
            if not session:
                raise EntityNotFoundError(f"Session {session_id} not found")
            
            # 更新元数据
            session.metadata.update(metadata)
            session.updated_at = datetime.now()
            
            # 保存更新
            success = await self._session_store.update_session(session_id, session)
            return success
        except Exception as e:
            raise ValidationError(f"Failed to update session metadata: {str(e)}")
    
    async def increment_message_count(self, session_id: str) -> int:
        """增加消息计数"""
        try:
            session = await self._session_store.get_session(session_id)
            if not session:
                raise EntityNotFoundError(f"Session {session_id} not found")
            
            session.message_count += 1
            session.updated_at = datetime.now()
            
            await self._session_store.update_session(session_id, session)
            return session.message_count
        except Exception as e:
            raise ValidationError(f"Failed to increment message count: {str(e)}")
    
    async def increment_checkpoint_count(self, session_id: str) -> int:
        """增加检查点计数"""
        try:
            session = await self._session_store.get_session(session_id)
            if not session:
                raise EntityNotFoundError(f"Session {session_id} not found")
            
            session.checkpoint_count += 1
            session.updated_at = datetime.now()
            
            await self._session_store.update_session(session_id, session)
            return session.checkpoint_count
        except Exception as e:
            raise ValidationError(f"Failed to increment checkpoint count: {str(e)}")
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要信息"""
        try:
            session = await self._session_store.get_session(session_id)
            if not session:
                raise EntityNotFoundError(f"Session {session_id} not found")
            
            return {
                "session_id": session.session_id,
                "status": session.status.value,
                "message_count": session.message_count,
                "checkpoint_count": session.checkpoint_count,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "metadata": session.metadata,
                "tags": session.tags,
                "thread_count": len(session.thread_ids) if hasattr(session, 'thread_ids') else 0
            }
        except Exception as e:
            raise ValidationError(f"Failed to get session summary: {str(e)}")
    
    async def list_sessions_by_status(self, status: str) -> List[Dict[str, Any]]:
        """按状态列会话"""
        try:
            # 验证状态有效性
            try:
                session_status = SessionStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid session status: {status}")
            
            sessions = await self._session_store.list_sessions_by_status(session_status)
            
            return [
                {
                    "session_id": session.session_id,
                    "status": session.status.value,
                    "message_count": session.message_count,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "metadata": session.metadata
                }
                for session in sessions
            ]
        except Exception as e:
            raise ValidationError(f"Failed to list sessions by status: {str(e)}")
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """清理不活动的会话"""
        try:
            # 获取所有非活动会话
            inactive_sessions = await self._session_store.list_sessions_by_status(SessionStatus.COMPLETED)
            failed_sessions = await self._session_store.list_sessions_by_status(SessionStatus.FAILED)
            
            all_sessions = inactive_sessions + failed_sessions
            
            # 筛选出超过指定时间的会话
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            sessions_to_cleanup = [
                session for session in all_sessions
                if session.updated_at < cutoff_time
            ]
            
            # 清理会话
            cleaned_count = 0
            for session in sessions_to_cleanup:
                success = await self._session_store.delete_session(session.session_id)
                if success:
                    cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            raise ValidationError(f"Failed to cleanup inactive sessions: {str(e)}")