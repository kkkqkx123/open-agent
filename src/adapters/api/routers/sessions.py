"""会话管理API路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from ..models.requests import SessionCreateRequest, SessionUpdateRequest
from ..models.responses import SessionResponse, SessionListResponse, SessionHistoryResponse, ApiResponse
from ..services.session_service import SessionService
from ..dependencies import get_session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[str] = Query(None, description="会话状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    session_service: SessionService = Depends(get_session_service)
) -> SessionListResponse:
    """获取会话列表"""
    try:
        return await session_service.list_sessions(
            page=page,
            page_size=page_size,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
) -> SessionResponse:
    """获取特定会话详情"""
    try:
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@router.post("/", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    session_service: SessionService = Depends(get_session_service)
) -> SessionResponse:
    """创建新会话"""
    try:
        return await session_service.create_session(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    session_service: SessionService = Depends(get_session_service)
) -> SessionResponse:
    """更新会话"""
    try:
        session = await session_service.update_session(session_id, request)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")


@router.delete("/{session_id}", response_model=ApiResponse)
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
) -> ApiResponse:
    """删除会话"""
    try:
        success = await session_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return ApiResponse(success=True, message="会话已删除", data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=500, description="记录数量限制"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    record_types: Optional[List[str]] = Query(None, description="记录类型过滤"),
    session_service: SessionService = Depends(get_session_service)
) -> SessionHistoryResponse:
    """获取会话历史"""
    try:
        return await session_service.get_session_history(
            session_id=session_id,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            record_types=record_types
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话历史失败: {str(e)}")


@router.post("/{session_id}/save", response_model=ApiResponse)
async def save_session_state(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
) -> ApiResponse:
    """保存会话状态"""
    try:
        success = await session_service.save_session_state(session_id, {})
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return ApiResponse(success=True, message="会话状态已保存", data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存会话状态失败: {str(e)}")


@router.post("/{session_id}/restore", response_model=SessionResponse)
async def restore_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
) -> SessionResponse:
    """恢复会话"""
    try:
        session = await session_service.restore_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或无法恢复")
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复会话失败: {str(e)}")


@router.get("/{session_id}/statistics")
async def get_session_statistics(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
) -> dict:
    """获取会话统计信息"""
    try:
        return await session_service.get_session_statistics(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话统计失败: {str(e)}")