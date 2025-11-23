"""WebSocket服务"""
from typing import Dict, Any, Optional, Set
import json
import asyncio
from datetime import datetime

from ..models.websocket import (
    WebSocketMessage,
    SessionUpdateMessage,
    WorkflowStateMessage,
    PerformanceMetricsMessage,
    ErrorMessage,
    StreamMessage
)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self) -> None:
        self.active_connections: Dict[str, Any] = {}  # client_id -> WebSocket
        self.subscriptions: Dict[str, Set[str]] = {}  # session_id -> set of client_ids
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: Any, client_id: str) -> None:
        """建立WebSocket连接"""
        async with self._lock:
            await websocket.accept()
            self.active_connections[client_id] = websocket
    
    async def disconnect(self, client_id: str) -> None:
        """断开WebSocket连接"""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            
            # 清理订阅
            for session_id, subscribers in self.subscriptions.items():
                if client_id in subscribers:
                    subscribers.remove(client_id)
    
    async def send_message(self, client_id: str, message: Dict[str, Any]) -> bool:
        """向特定客户端发送消息"""
        async with self._lock:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(json.dumps(message, ensure_ascii=False))
                    return True
                except Exception:
                    # 连接已断开，清理
                    del self.active_connections[client_id]
                    return False
            return False
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]) -> int:
        """向会话的所有订阅者广播消息"""
        async with self._lock:
            if session_id in self.subscriptions:
                success_count = 0
                failed_clients = []
                
                for client_id in self.subscriptions[session_id].copy():
                    if await self.send_message(client_id, message):
                        success_count += 1
                    else:
                        failed_clients.append(client_id)
                
                # 清理失败的客户端
                for client_id in failed_clients:
                    self.subscriptions[session_id].discard(client_id)
                
                return success_count
            return 0
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """向所有连接的客户端广播消息"""
        async with self._lock:
            success_count = 0
            failed_clients = []
            
            for client_id in list(self.active_connections.keys()):
                if await self.send_message(client_id, message):
                    success_count += 1
                else:
                    failed_clients.append(client_id)
            
            # 清理失败的客户端
            for client_id in failed_clients:
                if client_id in self.active_connections:
                    del self.active_connections[client_id]
            
            return success_count
    
    def subscribe_to_session(self, client_id: str, session_id: str) -> None:
        """订阅会话更新"""
        if session_id not in self.subscriptions:
            self.subscriptions[session_id] = set()
        self.subscriptions[session_id].add(client_id)
    
    def unsubscribe_from_session(self, client_id: str, session_id: str) -> None:
        """取消会话订阅"""
        if session_id in self.subscriptions and client_id in self.subscriptions[session_id]:
            self.subscriptions[session_id].remove(client_id)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        async with self._lock:
            total_connections = len(self.active_connections)
            total_subscriptions = sum(len(subscribers) for subscribers in self.subscriptions.values())
            
            return {
                "total_connections": total_connections,
                "total_subscriptions": total_subscriptions,
                "sessions_with_subscribers": len(self.subscriptions)
            }


class WebSocketService:
    """WebSocket服务"""
    
    def __init__(self) -> None:
        self.connection_manager = ConnectionManager()
        self._event_handlers = {
            "session_update": self._handle_session_update,
            "workflow_state": self._handle_workflow_state,
            "performance_metrics": self._handle_performance_metrics,
            "error_event": self._handle_error_event,
            "stream_update": self._handle_stream_update
        }
    
    async def broadcast_event(self, event_type: str, data: dict, session_id: Optional[str] = None) -> None:
        """广播事件"""
        if event_type in self._event_handlers:
            await self._event_handlers[event_type](data, session_id)
    
    async def _handle_session_update(self, data: dict, session_id: Optional[str]) -> None:
        """处理会话更新"""
        if session_id:
            message = SessionUpdateMessage(
                session_id=session_id,
                data=data
            )
            await self.connection_manager.broadcast_to_session(
                session_id, 
                message.model_dump()
            )
    
    async def _handle_workflow_state(self, data: dict, session_id: Optional[str]) -> None:
        """处理工作流状态更新"""
        if session_id:
            message = WorkflowStateMessage(
                session_id=session_id,
                data=data
            )
            await self.connection_manager.broadcast_to_session(
                session_id, 
                message.model_dump()
            )
    
    async def _handle_performance_metrics(self, data: dict, session_id: Optional[str]) -> None:
        """处理性能指标更新"""
        message = PerformanceMetricsMessage(data=data)
        if session_id:
            await self.connection_manager.broadcast_to_session(session_id, message.model_dump())
        else:
            await self.connection_manager.broadcast_to_all(message.model_dump())
    
    async def _handle_error_event(self, data: dict, session_id: Optional[str]) -> None:
        """处理错误事件"""
        message = ErrorMessage(
            error=data.get("error", "未知错误"),
            error_type=data.get("error_type"),
            session_id=session_id,
            data=None
        )
        if session_id:
            await self.connection_manager.broadcast_to_session(session_id, message.model_dump())
        else:
            await self.connection_manager.broadcast_to_all(message.model_dump())
    
    async def _handle_stream_update(self, data: dict, session_id: Optional[str]) -> None:
        """处理流式更新"""
        if session_id:
            message = StreamMessage(
                session_id=session_id,
                chunk=data.get("chunk", ""),
                is_final=data.get("is_final", False),
                data=None
            )
            await self.connection_manager.broadcast_to_session(
                session_id, 
                message.model_dump()
            )
    
    async def handle_client_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """处理客户端消息"""
        message_type = message.get("type")
        
        if message_type == "subscribe":
            # 订阅会话更新
            session_id = message.get("session_id")
            if session_id:
                self.connection_manager.subscribe_to_session(client_id, session_id)
                await self.connection_manager.send_message(client_id, {
                    "type": "subscribed",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
        
        elif message_type == "unsubscribe":
            # 取消会话订阅
            session_id = message.get("session_id")
            if session_id:
                self.connection_manager.unsubscribe_from_session(client_id, session_id)
                await self.connection_manager.send_message(client_id, {
                    "type": "unsubscribed",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
        
        elif message_type == "ping":
            # 心跳响应
            await self.connection_manager.send_message(client_id, {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
        
        elif message_type == "get_stats":
            # 获取连接统计
            stats = await self.connection_manager.get_connection_stats()
            await self.connection_manager.send_message(client_id, {
                "type": "stats",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            })
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取WebSocket服务统计信息"""
        return await self.connection_manager.get_connection_stats()
    
    async def cleanup_inactive_connections(self) -> None:
        """清理不活跃的连接"""
        # 这里可以实现心跳检测逻辑
        # 定期检查连接是否仍然活跃
        pass


# 全局WebSocket服务实例
websocket_service = WebSocketService()


# 便捷函数
async def push_session_update(session_id: str, update_data: dict) -> None:
    """推送会话更新"""
    await websocket_service.broadcast_event("session_update", update_data, session_id)


async def push_workflow_state(session_id: str, state_data: dict) -> None:
    """推送工作流状态更新"""
    await websocket_service.broadcast_event("workflow_state", state_data, session_id)


async def push_performance_metrics(metrics_data: dict, session_id: Optional[str] = None) -> None:
    """推送性能指标"""
    await websocket_service.broadcast_event("performance_metrics", metrics_data, session_id)


async def push_error_event(error_data: dict, session_id: Optional[str] = None) -> None:
    """推送错误事件"""
    await websocket_service.broadcast_event("error_event", error_data, session_id)


async def push_stream_update(session_id: str, chunk: str, is_final: bool = False) -> None:
    """推送流式更新"""
    await websocket_service.broadcast_event("stream_update", {
        "chunk": chunk,
        "is_final": is_final
    }, session_id)