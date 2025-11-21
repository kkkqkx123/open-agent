"""Session生命周期管理器"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from src.interfaces.sessions import ISessionManager
from src.core.sessions import SessionStatus


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
    """Session生命周期管理器"""
    
    def __init__(self, session_manager: ISessionManager):
        """初始化生命周期管理器
        
        Args:
            session_manager: 会话管理器
        """
        self._session_manager = session_manager
        self._event_handlers = {}
    
    def register_event_handler(self, event: SessionLifecycleEvent, handler) -> None:
        """注册事件处理器
        
        Args:
            event: 事件类型
            handler: 事件处理器函数
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def unregister_event_handler(self, event: SessionLifecycleEvent, handler) -> None:
        """注销事件处理器
        
        Args:
            event: 事件类型
            handler: 事件处理器函数
        """
        if event in self._event_handlers and handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)
    
    async def _emit_event(self, event: SessionLifecycleEvent, session_id: str, data: Optional[Dict[str, Any]] = None) -> None:
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
                await handler(event_data)
            except Exception as e:
                # 记录异常但不中断其他处理器
                print(f"Error in session lifecycle event handler: {e}")
    
    async def create_session(self, graph_id: Optional[str] = None, **kwargs) -> str:
        """创建会话并触发创建事件
        
        Args:
            graph_id: 关联的图ID
            **kwargs: 其他参数
            
        Returns:
            会话ID
        """
        session_id = await self._session_manager.create_session(graph_id=graph_id, **kwargs)
        
        # 触发创建事件
        await self._emit_event(SessionLifecycleEvent.CREATED, session_id, {
            "graph_id": graph_id,
            **kwargs
        })
        
        # 如果是活动状态，触发激活事件
        session = await self._session_manager.get_session(session_id)
        if session and session.get("status") == SessionStatus.ACTIVE.value:
            await self._emit_event(SessionLifecycleEvent.ACTIVATED, session_id)
        
        return session_id
    
    async def activate_session(self, session_id: str) -> bool:
        """激活会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            成功返回True，失败返回False
        """
        success = await self._session_manager.update_session_status(
            session_id, SessionStatus.ACTIVE.value
        )
        
        if success:
            await self._emit_event(SessionLifecycleEvent.ACTIVATED, session_id)
        
        return success
    
    async def pause_session(self, session_id: str) -> bool:
        """暂停会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            成功返回True，失败返回False
        """
        success = await self._session_manager.update_session_status(
            session_id, SessionStatus.PAUSED.value
        )
        
        if success:
            await self._emit_event(SessionLifecycleEvent.PAUSED, session_id)
        
        return success
    
    async def resume_session(self, session_id: str) -> bool:
        """恢复会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            成功返回True，失败返回False
        """
        success = await self._session_manager.update_session_status(
            session_id, SessionStatus.ACTIVE.value
        )
        
        if success:
            await self._emit_event(SessionLifecycleEvent.RESUMED, session_id)
        
        return success
    
    async def complete_session(self, session_id: str) -> bool:
        """完成会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            成功返回True，失败返回False
        """
        success = await self._session_manager.update_session_status(
            session_id, SessionStatus.COMPLETED.value
        )
        
        if success:
            await self._emit_event(SessionLifecycleEvent.COMPLETED, session_id)
        
        return success
    
    async def fail_session(self, session_id: str, error_info: Optional[Dict[str, Any]] = None) -> bool:
        """失败会话
        
        Args:
            session_id: 会话ID
            error_info: 错误信息
            
        Returns:
            成功返回True，失败返回False
        """
        success = await self._session_manager.update_session_status(
            session_id, SessionStatus.FAILED.value
        )
        
        if success:
            await self._emit_event(SessionLifecycleEvent.FAILED, session_id, error_info)
        
        return success
    
    async def archive_session(self, session_id: str) -> bool:
        """归档会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            成功返回True，失败返回False
        """
        success = await self._session_manager.update_session_status(
            session_id, SessionStatus.ARCHIVED.value
        )
        
        if success:
            await self._emit_event(SessionLifecycleEvent.ARCHIVED, session_id)
        
        return success
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            成功返回True，失败返回False
        """
        # 先触发删除事件
        await self._emit_event(SessionLifecycleEvent.DELETED, session_id)
        
        # 然后执行删除
        return await self._session_manager.delete_session(session_id)
    
    async def get_session_lifecycle_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话生命周期状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            生命周期状态信息，不存在时返回None
        """
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