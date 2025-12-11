"""Session生命周期管理器 - 简化实现"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from src.core.sessions.entities import SessionStatus

if TYPE_CHECKING:
    from .service import SessionService
    from .manager import SessionManager

logger = get_logger(__name__)


class SessionLifecycleEvent(str, Enum):
    """会话生命周期事件"""
    CREATED = "created"
    ACTIVATED = "activated"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class SessionLifecycleManager:
    """Session生命周期管理器
    
    管理会话的生命周期事件，支持事件处理器注册和触发
    """
    
    def __init__(
        self, 
        session_manager: Optional['SessionManager'] = None,
        session_service: Optional['SessionService'] = None
    ):
        """初始化生命周期管理器
        
        Args:
            session_manager: 会话管理器（可选）
            session_service: 会话服务（可选）
        """
        self._session_manager = session_manager
        self._session_service = session_service
        self._event_handlers: Dict[SessionLifecycleEvent, List[Callable]] = {}
    
    def register_event_handler(
        self, 
        event: SessionLifecycleEvent, 
        handler: Callable
    ) -> None:
        """注册事件处理器
        
        Args:
            event: 事件类型
            handler: 事件处理器函数
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
        logger.debug(f"Registered handler for event: {event.value}")
    
    def unregister_event_handler(
        self, 
        event: SessionLifecycleEvent, 
        handler: Callable
    ) -> None:
        """注销事件处理器
        
        Args:
            event: 事件类型
            handler: 事件处理器函数
        """
        if event in self._event_handlers and handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)
            logger.debug(f"Unregistered handler for event: {event.value}")
    
    async def _emit_event(
        self, 
        event: SessionLifecycleEvent, 
        session_id: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """触发事件
        
        Args:
            event: 事件类型
            session_id: 会话ID
            data: 事件数据
        """
        event_data = {
            "event": event.value,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                if callable(handler):
                    result = handler(event_data)
                    # 支持异步处理器
                    if hasattr(result, '__await__'):
                        await result
            except Exception as e:
                logger.error(f"Error in session lifecycle event handler: {e}")
    
    async def create_session(
        self, 
        graph_id: Optional[str] = None, 
        **kwargs
    ) -> str:
        """创建会话并触发创建事件
        
        Args:
            graph_id: 关联的图ID
            **kwargs: 其他参数
            
        Returns:
            会话ID
        """
        if self._session_manager:
            session_id = await self._session_manager.create_session(
                graph_id=graph_id, 
                **kwargs
            )
            
            # 触发创建事件
            await self._emit_event(
                SessionLifecycleEvent.CREATED, 
                session_id, 
                {"graph_id": graph_id, **kwargs}
            )
            
            # 获取会话并检查状态
            if self._session_manager:
                session = await self._session_manager.get_session(session_id)
                if session and session.get("status") == SessionStatus.ACTIVE.value:
                    await self._emit_event(SessionLifecycleEvent.ACTIVATED, session_id)
            
            return session_id
        
        raise RuntimeError("session_manager is not configured")
    
    async def activate_session(self, session_id: str) -> bool:
        """激活会话"""
        if self._session_manager:
            success = await self._session_manager.update_session_status(
                session_id, 
                SessionStatus.ACTIVE.value
            )
            if success:
                await self._emit_event(SessionLifecycleEvent.ACTIVATED, session_id)
            return success
        return False
    
    async def pause_session(self, session_id: str) -> bool:
        """暂停会话"""
        if self._session_manager:
            success = await self._session_manager.update_session_status(
                session_id, 
                SessionStatus.PAUSED.value
            )
            if success:
                await self._emit_event(SessionLifecycleEvent.PAUSED, session_id)
            return success
        return False
    
    async def resume_session(self, session_id: str) -> bool:
        """恢复会话"""
        if self._session_manager:
            success = await self._session_manager.update_session_status(
                session_id, 
                SessionStatus.ACTIVE.value
            )
            if success:
                await self._emit_event(SessionLifecycleEvent.RESUMED, session_id)
            return success
        return False
    
    async def complete_session(self, session_id: str) -> bool:
        """完成会话"""
        if self._session_manager:
            success = await self._session_manager.update_session_status(
                session_id, 
                SessionStatus.COMPLETED.value
            )
            if success:
                await self._emit_event(SessionLifecycleEvent.COMPLETED, session_id)
            return success
        return False
    
    async def fail_session(
        self, 
        session_id: str, 
        error_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """失败会话"""
        if self._session_manager:
            success = await self._session_manager.update_session_status(
                session_id, 
                SessionStatus.FAILED.value
            )
            if success:
                await self._emit_event(
                    SessionLifecycleEvent.FAILED, 
                    session_id, 
                    error_info
                )
            return success
        return False
    
    async def archive_session(self, session_id: str) -> bool:
        """归档会话"""
        if self._session_manager:
            success = await self._session_manager.update_session_status(
                session_id, 
                SessionStatus.ARCHIVED.value
            )
            if success:
                await self._emit_event(SessionLifecycleEvent.ARCHIVED, session_id)
            return success
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if self._session_manager:
            # 先触发删除事件
            await self._emit_event(SessionLifecycleEvent.DELETED, session_id)
            
            # 然后执行删除
            return await self._session_manager.delete_session(session_id)
        return False
    
    async def get_session_lifecycle_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话生命周期状态"""
        if self._session_manager:
            session = await self._session_manager.get_session(session_id)
            if not session:
                return None
            
            return {
                "session_id": session_id,
                "status": session.get("status"),
                "created_at": session.get("created_at"),
                "updated_at": session.get("updated_at"),
                "message_count": session.get("message_count", 0),
                "checkpoint_count": session.get("checkpoint_count", 0)
            }
        return None
