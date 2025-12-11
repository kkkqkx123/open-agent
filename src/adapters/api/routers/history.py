"""历史数据API路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime
import io
from src.interfaces.dependency_injection import get_logger

from ..models.requests import BookmarkCreateRequest
from ..models.responses import HistoryResponse, SearchResponse, BookmarkResponse, ApiResponse
from ..services.history_service import HistoryService
from ..dependencies import get_history_service

logger = get_logger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/sessions/{session_id}/messages", response_model=HistoryResponse)
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=500, description="记录数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    message_types: Optional[List[str]] = Query(None, description="消息类型过滤"),
    history_service: HistoryService = Depends(get_history_service)
) -> HistoryResponse:
    """获取会话消息历史"""
    try:
        return await history_service.get_session_messages(
            session_id=session_id,
            limit=limit,
            offset=offset,
            start_time=start_time,
            end_time=end_time,
            message_types=message_types
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话消息失败: {str(e)}")


@router.get("/sessions/{session_id}/search", response_model=SearchResponse)
async def search_session_messages(
    session_id: str,
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    history_service: HistoryService = Depends(get_history_service)
) -> SearchResponse:
    """搜索会话消息"""
    try:
        return await history_service.search_session_messages(
            session_id=session_id,
            query=query,
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索会话消息失败: {str(e)}")


@router.get("/sessions/{session_id}/export")
async def export_session_data(
    session_id: str,
    format: str = Query("json", description="导出格式: json, csv"),
    history_service: HistoryService = Depends(get_history_service)
):
    """导出会话数据"""
    try:
        export_data = await history_service.export_session_data(session_id, format)
        
        if format == "json":
            return export_data
        elif format == "csv":
            # 返回CSV文件下载
            csv_content = export_data if isinstance(export_data, str) else str(export_data)
            return StreamingResponse(
                io.BytesIO(csv_content.encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=session_{session_id}.csv"}
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出会话数据失败: {str(e)}")


@router.post("/sessions/{session_id}/bookmarks", response_model=BookmarkResponse)
async def bookmark_message(
    session_id: str,
    request: BookmarkCreateRequest,
    history_service: HistoryService = Depends(get_history_service)
) -> BookmarkResponse:
    """添加消息书签"""
    try:
        return await history_service.bookmark_message(
            session_id=session_id,
            message_id=request.message_id,
            note=request.note
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加书签失败: {str(e)}")


@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def get_bookmarks(
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    history_service: HistoryService = Depends(get_history_service)
) -> List[BookmarkResponse]:
    """获取书签列表"""
    try:
        return await history_service.get_bookmarks(session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取书签列表失败: {str(e)}")


@router.delete("/bookmarks/{bookmark_id}", response_model=ApiResponse)
async def delete_bookmark(
    bookmark_id: str,
    history_service: HistoryService = Depends(get_history_service)
) -> ApiResponse:
    """删除书签"""
    try:
        success = await history_service.delete_bookmark(bookmark_id)
        if not success:
            raise HTTPException(status_code=404, detail="书签不存在")
        return ApiResponse(success=True, message="书签已删除", data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除书签失败: {str(e)}")


@router.get("/sessions/{session_id}/statistics")
async def get_session_statistics(
    session_id: str,
    history_service: HistoryService = Depends(get_history_service)
) -> dict:
    """获取会话统计信息"""
    try:
        return await history_service.get_session_statistics(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话统计失败: {str(e)}")


@router.get("/activity")
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200, description="活动数量限制"),
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    history_service: HistoryService = Depends(get_history_service)
) -> List[dict]:
    """获取最近活动"""
    try:
        return await history_service.get_recent_activity(
            limit=limit,
            session_id=session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近活动失败: {str(e)}")


@router.post("/cleanup", response_model=ApiResponse)
async def cleanup_old_records(
    days_to_keep: int = Query(30, ge=1, le=365, description="保留天数"),
    history_service: HistoryService = Depends(get_history_service)
) -> ApiResponse:
    """清理旧记录"""
    try:
        result = await history_service.cleanup_old_records(days_to_keep=days_to_keep)
        return ApiResponse(
            success=True,
            message="清理完成",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理旧记录失败: {str(e)}")


@router.get("/sessions/{session_id}/aggregate")
async def aggregate_session_data(
    session_id: str,
    aggregation_type: str = Query("daily", description="聚合类型"),
    history_service: HistoryService = Depends(get_history_service)
) -> dict:
    """聚合会话数据"""
    try:
        return await history_service.aggregate_session_data(
            session_id=session_id,
            aggregation_type=aggregation_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聚合会话数据失败: {str(e)}")


@router.get("/sessions")
async def get_all_sessions(
    limit: int = Query(100, ge=1, le=1000, description="返回会话数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    history_service: HistoryService = Depends(get_history_service)
) -> dict:
    """
    获取所有会话列表
    
    返回所有会话的基本信息，包括会话ID、消息数量、最后活动时间等。
    支持分页查询，可按需获取不同范围的会话列表。
    """
    try:
        logger.info(f"获取会话列表: limit={limit}, offset={offset}")
        sessions = await history_service.get_all_sessions(limit=limit, offset=offset)
        
        return {
            "success": True,
            "data": {
                "sessions": sessions,
                "total": len(sessions),
                "limit": limit,
                "offset": offset
            },
            "message": "会话列表获取成功"
        }
        
    except ValueError as e:
        logger.warning(f"获取会话列表参数验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")