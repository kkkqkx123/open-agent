"""Session事件管理器 - 简化实现"""

import asyncio
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .service import SessionService
    from .manager import SessionManager

logger = get_logger(__name__)


class SessionEventType(str, Enum):
    """会话事件类型"""
    CREATED = "session.created"
    UPDATED = "session.updated"
    DELETED = "session.deleted"
    STATUS_CHANGED = "session.status_changed"
    MESSAGE_ADDED = "session.message_added"
    CHECKPOINT_CREATED = "session.checkpoint_created"
    METADATA_UPDATED = "session.metadata_updated"
    CONFIG_UPDATED = "session.config_updated"


class SessionEventManager:
    """Session事件管理器
    
    管理会话相关事件，支持监听器注册和事件触发
    """
    
    def __init__(
        self, 
        session_manager: Optional['SessionManager'] = None,
        session_service: Optional['SessionService'] = None
    ):
        """初始化事件管理器
        
        Args:
            session_manager: 会话管理器（可选）
            session_service: 会话服务（可选）
        """
        self._session_manager = session_manager
        self._session_service = session_service
        self._event_listeners: Dict[SessionEventType, List[Callable]] = {}
        self._global_listeners: List[Callable] = []
        self._event_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
    
    def add_event_listener(
        self, 
        event_type: SessionEventType, 
        listener: Callable[[Dict[str, Any]], None]
    ) -> None:
        """添加事件监听器
        
        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(listener)
        logger.debug(f"Added event listener for {event_type.value}")
    
    def remove_event_listener(
        self, 
        event_type: SessionEventType, 
        listener: Callable[[Dict[str, Any]], None]
    ) -> None:
        """移除事件监听器
        
        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        if event_type in self._event_listeners and listener in self._event_listeners[event_type]:
            self._event_listeners[event_type].remove(listener)
            logger.debug(f"Removed event listener for {event_type.value}")
    
    def add_global_event_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """添加全局事件监听器
        
        Args:
            listener: 监听器函数
        """
        self._global_listeners.append(listener)
        logger.debug("Added global event listener")
    
    def remove_global_event_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """移除全局事件监听器
        
        Args:
            listener: 监听器函数
        """
        if listener in self._global_listeners:
            self._global_listeners.remove(listener)
            logger.debug("Removed global event listener")
    
    async def emit_event(
        self, 
        event_type: SessionEventType, 
        session_id: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """触发事件
        
        Args:
            event_type: 事件类型
            session_id: 会话ID
            data: 事件数据
        """
        event_data = {
            "event_type": event_type.value,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        # 添加到事件历史
        self._add_to_history(event_data)
        
        # 触发特定事件监听器
        listeners = self._event_listeners.get(event_type, [])
        await self._notify_listeners(listeners, event_data)
        
        # 触发全局监听器
        await self._notify_listeners(self._global_listeners, event_data)
    
    async def _notify_listeners(
        self, 
        listeners: List[Callable], 
        event_data: Dict[str, Any]
    ) -> None:
        """通知监听器
        
        Args:
            listeners: 监听器列表
            event_data: 事件数据
        """
        tasks = []
        for listener in listeners:
            try:
                # 支持异步和同步监听器
                if asyncio.iscoroutinefunction(listener):
                    tasks.append(listener(event_data))
                else:
                    # 同步函数在异步环境中执行
                    tasks.append(asyncio.create_task(
                        asyncio.to_thread(listener, event_data)
                    ))
            except Exception as e:
                logger.error(f"Error creating listener task: {e}")
        
        # 并行执行所有监听器
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _add_to_history(self, event_data: Dict[str, Any]) -> None:
        """添加到事件历史
        
        Args:
            event_data: 事件数据
        """
        self._event_history.append(event_data)
        
        # 限制历史记录大小
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
    
    def get_event_history(
        self, 
        session_id: Optional[str] = None,
        event_type: Optional[SessionEventType] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取事件历史
        
        Args:
            session_id: 会话ID过滤
            event_type: 事件类型过滤
            limit: 限制返回数量
            
        Returns:
            事件历史列表
        """
        history = self._event_history.copy()
        
        # 按会话ID过滤
        if session_id:
            history = [event for event in history if event.get("session_id") == session_id]
        
        # 按事件类型过滤
        if event_type:
            history = [event for event in history if event.get("event_type") == event_type.value]
        
        # 限制数量
        if limit:
            history = history[-limit:]
        
        return history
    
    def clear_event_history(self, session_id: Optional[str] = None) -> None:
        """清除事件历史
        
        Args:
            session_id: 指定会话ID清除，None则清除所有
        """
        if session_id is None:
            self._event_history.clear()
        else:
            self._event_history = [
                event for event in self._event_history 
                if event.get("session_id") != session_id
            ]
    
    async def monitor_session_created(self, session_id: str, **kwargs) -> None:
        """监控会话创建"""
        await self.emit_event(SessionEventType.CREATED, session_id, kwargs)
    
    async def monitor_session_updated(self, session_id: str, updates: Dict[str, Any]) -> None:
        """监控会话更新"""
        await self.emit_event(SessionEventType.UPDATED, session_id, {"updates": updates})
    
    async def monitor_session_deleted(self, session_id: str) -> None:
        """监控会话删除"""
        await self.emit_event(SessionEventType.DELETED, session_id)
    
    async def monitor_status_changed(
        self, 
        session_id: str, 
        old_status: str, 
        new_status: str
    ) -> None:
        """监控状态变更"""
        await self.emit_event(SessionEventType.STATUS_CHANGED, session_id, {
            "old_status": old_status,
            "new_status": new_status
        })
    
    async def monitor_message_added(self, session_id: str, message_count: int) -> None:
        """监控消息添加"""
        await self.emit_event(SessionEventType.MESSAGE_ADDED, session_id, {
            "message_count": message_count
        })
    
    async def monitor_checkpoint_created(self, session_id: str, checkpoint_count: int) -> None:
        """监控检查点创建"""
        await self.emit_event(SessionEventType.CHECKPOINT_CREATED, session_id, {
            "checkpoint_count": checkpoint_count
        })
    
    async def monitor_metadata_updated(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """监控元数据更新"""
        await self.emit_event(SessionEventType.METADATA_UPDATED, session_id, {
            "metadata": metadata
        })
    
    async def monitor_config_updated(self, session_id: str, config: Dict[str, Any]) -> None:
        """监控配置更新"""
        await self.emit_event(SessionEventType.CONFIG_UPDATED, session_id, {
            "config": config
        })
