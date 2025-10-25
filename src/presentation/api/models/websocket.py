"""WebSocket消息模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class WebSocketMessage(BaseModel):
    """WebSocket基础消息"""
    type: str = Field(..., description="消息类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    data: Optional[Dict[str, Any]] = Field(None, description="消息数据")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "ping",
                "timestamp": "2024-10-22T17:50:00Z",
                "data": {}
            }
        }
    )


class SubscribeMessage(WebSocketMessage):
    """订阅消息"""
    type: str = Field(default="subscribe", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "subscribe",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8"
            }
        }
    )


class UnsubscribeMessage(WebSocketMessage):
    """取消订阅消息"""
    type: str = Field(default="unsubscribe", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "unsubscribe",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8"
            }
        }
    )


class PingMessage(WebSocketMessage):
    """心跳消息"""
    type: str = Field(default="ping", description="消息类型")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "ping",
                "timestamp": "2024-10-22T17:50:00Z"
            }
        }
    )


class PongMessage(WebSocketMessage):
    """心跳响应消息"""
    type: str = Field(default="pong", description="消息类型")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "pong",
                "timestamp": "2024-10-22T17:50:00Z"
            }
        }
    )


class SessionUpdateMessage(WebSocketMessage):
    """会话更新消息"""
    type: str = Field(default="session_update", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    data: Optional[Dict[str, Any]] = Field(default=None, description="会话更新数据")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "type": "session_update",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8",
                "data": {
                    "status": "completed",
                    "updated_at": "2024-10-22T17:50:00Z"
                }
            }
        }
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "type": "session_update",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8",
                "data": {
                    "status": "completed",
                    "updated_at": "2024-10-22T17:50:00Z"
                }
            }
        }
    )


class WorkflowStateMessage(WebSocketMessage):
    """工作流状态消息"""
    type: str = Field(default="workflow_state", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    data: Optional[Dict[str, Any]] = Field(default=None, description="工作流状态数据")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "type": "workflow_state",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8",
                "data": {
                    "current_node": "think",
                    "iteration": 3,
                    "state": "running"
                }
            }
        }
    )


class PerformanceMetricsMessage(WebSocketMessage):
    """性能指标消息"""
    type: str = Field(default="performance_metrics", description="消息类型")
    data: Optional[Dict[str, Any]] = Field(default=None, description="性能指标数据")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "type": "performance_metrics",
                "timestamp": "2024-10-22T17:50:00Z",
                "data": {
                    "response_time": 1250.5,
                    "memory_usage": 512,
                    "cpu_usage": 45.2
                }
            }
        }
    )


class ErrorMessage(WebSocketMessage):
    """错误消息"""
    type: str = Field(default="error", description="消息类型")
    error: str = Field(..., description="错误信息")
    error_type: Optional[str] = Field(None, description="错误类型")
    session_id: Optional[str] = Field(None, description="会话ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "error",
                "timestamp": "2024-10-22T17:50:00Z",
                "error": "API调用失败",
                "error_type": "APIError",
                "session_id": "react-251022-174800-1f73e8"
            }
        }
    )


class SubscribedMessage(WebSocketMessage):
    """订阅成功消息"""
    type: str = Field(default="subscribed", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "subscribed",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8"
            }
        }
    )


class UnsubscribedMessage(WebSocketMessage):
    """取消订阅成功消息"""
    type: str = Field(default="unsubscribed", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "unsubscribed",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8"
            }
        }
    )


class StreamMessage(WebSocketMessage):
    """流式消息"""
    type: str = Field(default="stream", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    chunk: str = Field(..., description="消息块")
    is_final: bool = Field(default=False, description="是否为最后一块")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "stream",
                "timestamp": "2024-10-22T17:50:00Z",
                "session_id": "react-251022-174800-1f73e8",
                "chunk": "这是回答的一部分",
                "is_final": False
            }
        }
    )