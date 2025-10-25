"""WebSocket API路由"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set
import json
import asyncio
from datetime import datetime

from ..services.websocket_service import websocket_service, ConnectionManager
from ..dependencies import get_websocket_service

router = APIRouter()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    service = Depends(get_websocket_service)
):
    """WebSocket连接端点"""
    await service.connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理消息
            await service.handle_client_message(client_id, message)
            
    except WebSocketDisconnect:
        await service.connection_manager.disconnect(client_id)
    except Exception as e:
        await service.connection_manager.send_message(client_id, {
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        await service.connection_manager.disconnect(client_id)


@router.get("/ws/stats")
async def get_websocket_stats(
    service = Depends(get_websocket_service)
) -> dict:
    """获取WebSocket连接统计"""
    try:
        return await service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取WebSocket统计失败: {str(e)}")


# 便捷函数，供其他服务调用
async def push_session_update(session_id: str, update_data: dict):
    """推送会话更新"""
    await websocket_service.broadcast_event("session_update", update_data, session_id)


async def push_workflow_state(session_id: str, state_data: dict):
    """推送工作流状态更新"""
    await websocket_service.broadcast_event("workflow_state", state_data, session_id)


async def push_performance_metrics(metrics_data: dict, session_id: str = None):
    """推送性能指标"""
    await websocket_service.broadcast_event("performance_metrics", metrics_data, session_id)


async def push_error_event(error_data: dict, session_id: str = None):
    """推送错误事件"""
    await websocket_service.broadcast_event("error_event", error_data, session_id)


async def push_stream_update(session_id: str, chunk: str, is_final: bool = False):
    """推送流式更新"""
    await websocket_service.broadcast_event("stream_update", {
        "chunk": chunk,
        "is_final": is_final
    }, session_id)