"""Thread管理API路由器"""

from fastapi import APIRouter, Path, Body, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.responses import ThreadResponse, ThreadListResponse, OperationResponse
from ..models.requests import ThreadCreateRequest, ThreadForkRequest, ThreadRollbackRequest, ThreadSnapshotRequest
from ..services.session_service import SessionService
from ....domain.threads.interfaces import IThreadManager
from ....application.checkpoint.interfaces import ICheckpointManager

router = APIRouter(prefix="/api/threads", tags=["threads"])


# 依赖注入获取服务
def get_thread_manager() -> IThreadManager:
    """获取Thread管理器"""
    # 这里需要从依赖注入容器获取，暂时使用占位符
    from ....infrastructure.container import get_global_container
    return get_global_container().get(IThreadManager)


def get_checkpoint_manager() -> ICheckpointManager:
    """获取Checkpoint管理器"""
    # 这里需要从依赖注入容器获取，暂时使用占位符
    from ....infrastructure.container import get_global_container
    return get_global_container().get(ICheckpointManager)


# Session-Thread映射器已删除，Session将直接管理多个Thread


@router.post("/{thread_id}/fork", response_model=ThreadResponse)
async def fork_thread(
    thread_id: str = Path(..., description="Thread ID"),
    request: ThreadForkRequest = Body(...),
    thread_manager: IThreadManager = Depends(get_thread_manager),
    checkpoint_manager: ICheckpointManager = Depends(get_checkpoint_manager)
) -> ThreadResponse:
    """创建thread分支"""
    try:
        # 验证thread存在
        if not await thread_manager.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 验证checkpoint存在
        checkpoint = await checkpoint_manager.get_checkpoint(thread_id, request.checkpoint_id)
        if not checkpoint:
            raise HTTPException(status_code=404, detail=f"Checkpoint不存在: {request.checkpoint_id}")
        
        # 创建分支
        new_thread_id = await thread_manager.fork_thread(
            thread_id,
            request.checkpoint_id,
            request.branch_name,
            request.metadata
        )
        
        # 获取新thread信息
        thread_info = await thread_manager.get_thread_info(new_thread_id)
        if not thread_info:
            raise HTTPException(status_code=500, detail=f"创建分支成功但无法获取thread信息: {new_thread_id}")

        return ThreadResponse(
        thread_id=new_thread_id,
        graph_id=thread_info.get("graph_id", ""),
        status=thread_info.get("status", "active"),
        created_at=thread_info.get("created_at", datetime.now()),
        updated_at=thread_info.get("updated_at", datetime.now()),
            metadata=thread_info.get("metadata"),
            branch_name=thread_info.get("branch_name")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分支失败: {str(e)}")


@router.post("/{thread_id}/rollback", response_model=OperationResponse)
async def rollback_thread(
    thread_id: str = Path(..., description="Thread ID"),
    request: ThreadRollbackRequest = Body(...),
    thread_manager: IThreadManager = Depends(get_thread_manager)
) -> OperationResponse:
    """回滚thread到指定checkpoint"""
    try:
        # 验证thread存在
        if not await thread_manager.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 执行回滚
        success = await thread_manager.rollback_thread(thread_id, request.checkpoint_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"回滚失败: checkpoint不存在或无效")
        
        return OperationResponse(
        success=True,
        message=f"Thread {thread_id} 已成功回滚到 checkpoint {request.checkpoint_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回滚失败: {str(e)}")


@router.post("/{thread_id}/snapshots", response_model=OperationResponse)
async def create_thread_snapshot(
    thread_id: str = Path(..., description="Thread ID"),
    request: ThreadSnapshotRequest = Body(...),
    thread_manager: IThreadManager = Depends(get_thread_manager)
) -> OperationResponse:
    """创建thread快照"""
    try:
        # 验证thread存在
        if not await thread_manager.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 创建快照
        snapshot_id = await thread_manager.create_thread_snapshot(
            thread_id,
            request.snapshot_name,
            request.description
        )
        
        return OperationResponse(
        success=True,
        message=f"快照 {snapshot_id} 创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建快照失败: {str(e)}")


@router.get("/{thread_id}/history", response_model=ThreadListResponse)
async def get_thread_history(
    thread_id: str = Path(..., description="Thread ID"),
    limit: Optional[int] = Query(None, description="返回结果数量限制"),
    thread_manager: IThreadManager = Depends(get_thread_manager)
) -> ThreadListResponse:
    """获取thread历史记录"""
    try:
        # 验证thread存在
        if not await thread_manager.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 获取历史记录
        history = await thread_manager.get_thread_history(thread_id, limit)

        # 转换历史记录为ThreadResponse对象
        thread_responses = [
            ThreadResponse(
                thread_id=item.get("thread_id", ""),
                graph_id=item.get("graph_id", ""),
                status=item.get("status", "active"),
                created_at=item.get("created_at", datetime.now()),
                updated_at=item.get("updated_at", datetime.now()),
                metadata=item.get("metadata"),
                branch_name=item.get("branch_name")
            )
            for item in history
        ]

        return ThreadListResponse(
            threads=thread_responses,
            total=len(thread_responses)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


