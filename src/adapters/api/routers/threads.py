"""Thread管理API路由器"""

from fastapi import APIRouter, Path, Body, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.responses import ThreadResponse, ThreadListResponse, OperationResponse
from ..models.requests import ThreadCreateRequest, ThreadForkRequest, ThreadRollbackRequest, ThreadSnapshotRequest
from ..services.session_service import SessionService
from src.interfaces.threads.service import IThreadService
# 移除已删除的Thread checkpoint接口引用

router = APIRouter(prefix="/api/threads", tags=["threads"])


# 依赖注入获取服务
def get_thread_service() -> IThreadService:
    """获取Thread服务"""
    # TODO: 从依赖注入容器获取真实实现
    raise NotImplementedError("Thread service must be provided via dependency injection")


def get_checkpoint_store() -> IThreadCheckpointStorage:
    """获取Checkpoint存储器"""
    # TODO: 从依赖注入容器获取真实实现
    raise NotImplementedError("Checkpoint store must be provided via dependency injection")


def get_thread_checkpoint_storage():
    """获取Thread Checkpoint存储器"""
    # TODO: 从依赖注入容器获取真实实现
    return None


# Session-Thread映射器已删除，Session将直接管理多个Thread


@router.post("/{thread_id}/fork", response_model=ThreadResponse)
async def fork_thread(
    thread_id: str = Path(..., description="Thread ID"),
    request: ThreadForkRequest = Body(...),
    thread_service: IThreadService = Depends(get_thread_service),
    checkpoint_store: IThreadCheckpointStorage = Depends(get_checkpoint_store),
    thread_checkpoint_storage = Depends(get_thread_checkpoint_storage)
) -> ThreadResponse:
    """创建thread分支"""
    try:
        # 验证thread存在
        if not await thread_service.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 验证checkpoint存在
        checkpoint = None
        # 暂时简化处理，移除对已删除接口的依赖
        checkpoint = None
        
        if not checkpoint and checkpoint_store:
            # 回退到旧的checkpoint存储器
            checkpoint = await checkpoint_store.load_by_thread(thread_id, request.checkpoint_id)
        
        if not checkpoint:
            raise HTTPException(status_code=404, detail=f"Checkpoint不存在: {request.checkpoint_id}")
        
        # 创建分支
        new_thread_id = await thread_service.create_branch(
            thread_id,
            request.checkpoint_id,
            request.branch_name,
            request.metadata
        )
        
        # 获取新thread信息
        thread_info = await thread_service.get_thread_info(new_thread_id)
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
    thread_service: IThreadService = Depends(get_thread_service)
) -> OperationResponse:
    """回滚thread到指定checkpoint"""
    try:
        # 验证thread存在
        if not await thread_service.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 执行回滚
        success = await thread_service.rollback_thread(thread_id, request.checkpoint_id)
        
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
    thread_service: IThreadService = Depends(get_thread_service)
) -> OperationResponse:
    """创建thread快照"""
    try:
        # 验证thread存在
        if not await thread_service.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 创建快照
        snapshot_id = await thread_service.create_snapshot(
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
    thread_service: IThreadService = Depends(get_thread_service)
) -> ThreadListResponse:
    """获取thread历史记录"""
    try:
        # 验证thread存在
        if not await thread_service.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail=f"Thread不存在: {thread_id}")
        
        # 获取历史记录
        history = await thread_service.get_thread_history(thread_id, limit)

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


@router.get("/", response_model=ThreadListResponse)
async def list_threads(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[str] = Query(None, description="状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    thread_service: IThreadService = Depends(get_thread_service)
) -> ThreadListResponse:
    """获取Thread列表"""
    try:
        # 构建过滤条件
        filters = {}
        if status:
            filters["status"] = status
        
        # 搜索threads
        if search:
            filters["contains_text"] = search
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取threads
        threads = await thread_service.search_threads(
            filters=filters,
            limit=page_size,
            offset=offset
        )
        
        # 转换为ThreadResponse对象
        thread_responses = [
            ThreadResponse(
                thread_id=thread.get("thread_id", ""),
                graph_id=thread.get("graph_id", ""),
                status=thread.get("status", "active"),
                created_at=datetime.fromisoformat(thread.get("created_at", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(thread.get("updated_at", datetime.now().isoformat())),
                metadata=thread.get("metadata", {}),
                branch_name=thread.get("metadata", {}).get("branch_name")
            )
            for thread in threads
        ]

        return ThreadListResponse(
            threads=thread_responses,
            total=len(thread_responses)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thread列表失败: {str(e)}")


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str = Path(..., description="Thread ID"),
    thread_service: IThreadService = Depends(get_thread_service)
) -> ThreadResponse:
    """获取Thread详情"""
    try:
        # 获取thread信息
        thread_info = await thread_service.get_thread_info(thread_id)
        if not thread_info:
            raise HTTPException(status_code=404, detail="Thread不存在")

        return ThreadResponse(
            thread_id=thread_info.get("thread_id", ""),
            graph_id=thread_info.get("graph_id", ""),
            status=thread_info.get("status", "active"),
            created_at=datetime.fromisoformat(thread_info.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(thread_info.get("updated_at", datetime.now().isoformat())),
            metadata=thread_info.get("metadata", {}),
            branch_name=thread_info.get("metadata", {}).get("branch_name")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thread详情失败: {str(e)}")


@router.delete("/{thread_id}", response_model=OperationResponse)
async def delete_thread(
    thread_id: str = Path(..., description="Thread ID"),
    thread_service: IThreadService = Depends(get_thread_service)
) -> OperationResponse:
    """删除Thread"""
    try:
        # 验证thread存在
        if not await thread_service.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail="Thread不存在")
        
        # 删除thread
        success = await thread_service.delete_thread(thread_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除Thread失败")
        
        return OperationResponse(
            success=True,
            message=f"Thread {thread_id} 已删除"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除Thread失败: {str(e)}")


@router.get("/{thread_id}/branches", response_model=List[Dict[str, Any]])
async def get_thread_branches(
    thread_id: str = Path(..., description="Thread ID"),
    thread_service: IThreadService = Depends(get_thread_service)
) -> List[Dict[str, Any]]:
    """获取Thread的所有分支"""
    try:
        # 验证thread存在
        if not await thread_service.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail="Thread不存在")
        
        # 获取分支信息
        branches = await thread_service.get_thread_branches(thread_id)
        
        return branches
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thread分支失败: {str(e)}")


@router.get("/{thread_id}/snapshots", response_model=List[Dict[str, Any]])
async def get_thread_snapshots(
    thread_id: str = Path(..., description="Thread ID"),
    thread_service: IThreadService = Depends(get_thread_service)
) -> List[Dict[str, Any]]:
    """获取Thread的所有快照"""
    try:
        # 验证thread存在
        if not await thread_service.thread_exists(thread_id):
            raise HTTPException(status_code=404, detail="Thread不存在")
        
        # 获取thread信息
        thread_info = await thread_service.get_thread_info(thread_id)
        if not thread_info:
            raise HTTPException(status_code=404, detail="Thread不存在")
        
        # 返回快照信息
        return thread_info.get("snapshots", [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thread快照失败: {str(e)}")


@router.post("/", response_model=ThreadResponse)
async def create_thread(
    request: ThreadCreateRequest = Body(...),
    thread_service: IThreadService = Depends(get_thread_service)
) -> ThreadResponse:
    """创建新Thread"""
    try:
        # 创建thread
        if request.config_path:
            thread_id = await thread_service.create_thread_from_config(
                request.config_path,
                request.metadata
            )
        else:
            thread_id = await thread_service.create_thread(
                request.graph_id or "default",
                request.metadata
            )
        
        # 获取thread信息
        thread_info = await thread_service.get_thread_info(thread_id)
        if not thread_info:
            raise HTTPException(status_code=500, detail="创建Thread成功但无法获取信息")
        
        return ThreadResponse(
            thread_id=thread_info.get("thread_id", ""),
            graph_id=thread_info.get("graph_id", ""),
            status=thread_info.get("status", "active"),
            created_at=datetime.fromisoformat(thread_info.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(thread_info.get("updated_at", datetime.now().isoformat())),
            metadata=thread_info.get("metadata", {}),
            branch_name=thread_info.get("metadata", {}).get("branch_name")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建Thread失败: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_thread_statistics(
    thread_service: IThreadService = Depends(get_thread_service)
) -> Dict[str, Any]:
    """获取Thread统计信息"""
    try:
        stats = await thread_service.get_thread_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thread统计失败: {str(e)}")