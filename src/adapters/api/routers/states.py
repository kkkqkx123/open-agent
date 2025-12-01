"""状态管理API路由"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel

from ..models.requests import (
    StateCreateRequest,
    StateUpdateRequest,
    StateValidateRequest,
    StateSnapshotRequest,
    StateRestoreRequest
)
from ..models.responses import (
    ApiResponse,
    StateResponse,
    StateListResponse,
    StateValidationResponse,
    StateSnapshotResponse,
    StateSnapshotListResponse,
    StateHistoryResponse
)
from ..dependencies import get_state_service
from ..services.state_service import StateService


router = APIRouter(prefix="/states", tags=["状态管理"])


@router.get("", response_model=StateListResponse)
async def get_states(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    state_service: StateService = Depends(get_state_service)
) -> StateListResponse:
    """获取状态列表
    
    Returns:
        状态列表响应，包含分页信息
    """
    try:
        result = await state_service.get_states(page, page_size)
        return StateListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态列表失败: {str(e)}")


@router.get("/{state_id}", response_model=StateResponse)
async def get_state(
    state_id: str = Path(..., description="状态ID"),
    state_service: StateService = Depends(get_state_service)
) -> StateResponse:
    """获取状态详情
    
    Args:
        state_id: 状态ID
        
    Returns:
        状态详情
    """
    try:
        state_data = await state_service.get_state(state_id)
        if not state_data:
            raise HTTPException(status_code=404, detail="状态不存在")
        return StateResponse(**state_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("", response_model=StateResponse)
async def create_state(
    request: StateCreateRequest,
    state_service: StateService = Depends(get_state_service)
) -> StateResponse:
    """创建状态
    
    Args:
        request: 创建状态请求
        
    Returns:
        创建的状态
    """
    try:
        state_data = await state_service.create_state(request.state_id, request.initial_state)
        return StateResponse(**state_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"创建状态失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建状态失败: {str(e)}")


@router.put("/{state_id}", response_model=StateResponse)
async def update_state(
    request: StateUpdateRequest,
    state_id: str = Path(..., description="状态ID"),
    state_service: StateService = Depends(get_state_service)
) -> StateResponse:
    """更新状态
    
    Args:
        state_id: 状态ID
        request: 更新状态请求
        
    Returns:
        更新后的状态
    """
    try:
        state_data = await state_service.update_state(
            state_id, request.updates
        )
        return StateResponse(**state_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"更新状态失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")


@router.delete("/{state_id}", response_model=ApiResponse)
async def delete_state(
    state_id: str = Path(..., description="状态ID"),
    state_service: StateService = Depends(get_state_service)
) -> ApiResponse:
    """删除状态
    
    Args:
        state_id: 状态ID
        
    Returns:
        操作结果
    """
    try:
        success = await state_service.delete_state(state_id)
        if not success:
            raise HTTPException(status_code=404, detail="状态不存在")
        return ApiResponse(
            success=True,
            message="状态删除成功",
            data={"state_id": state_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除状态失败: {str(e)}")


@router.post("/{state_id}/validate", response_model=StateValidationResponse)
async def validate_state(
    state_id: str = Path(..., description="状态ID"),
    request: Optional[StateValidateRequest] = None,
    state_service: StateService = Depends(get_state_service)
) -> StateValidationResponse:
    """验证状态
    
    Args:
        state_id: 状态ID
        request: 验证状态请求（可选，如果不提供则验证当前状态）
        
    Returns:
        验证结果
    """
    try:
        if request:
            # 验证请求中的状态
            result = await state_service.validate_state_dict(request.state)
        else:
            # 验证存储的状态
            result = await state_service.validate_state(state_id)
        
        return StateValidationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证状态失败: {str(e)}")


@router.post("/{state_id}/snapshot", response_model=StateSnapshotResponse)
async def create_state_snapshot(
    request: StateSnapshotRequest,
    state_id: str = Path(..., description="状态ID"),
    state_service: StateService = Depends(get_state_service)
) -> StateSnapshotResponse:
    """创建状态快照
    
    Args:
        state_id: 状态ID
        request: 创建快照请求
        
    Returns:
        创建的快照
    """
    try:
        snapshot_data = await state_service.create_snapshot(
            state_id, request.description
        )
        return StateSnapshotResponse(**snapshot_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"创建快照失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建快照失败: {str(e)}")


@router.get("/{state_id}/snapshots", response_model=StateSnapshotListResponse)
async def get_state_snapshots(
    state_id: str = Path(..., description="状态ID"),
    state_service: StateService = Depends(get_state_service)
) -> StateSnapshotListResponse:
    """获取状态快照列表
    
    Args:
        state_id: 状态ID
        
    Returns:
        快照列表
    """
    try:
        snapshots_data = await state_service.get_snapshots(state_id)
        return StateSnapshotListResponse(**snapshots_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取快照列表失败: {str(e)}")


@router.post("/{state_id}/restore", response_model=StateResponse)
async def restore_state_snapshot(
    request: StateRestoreRequest,
    state_id: str = Path(..., description="状态ID"),
    state_service: StateService = Depends(get_state_service)
) -> StateResponse:
    """恢复状态快照
    
    Args:
        state_id: 状态ID
        request: 恢复快照请求
        
    Returns:
        恢复后的状态
    """
    try:
        state_data = await state_service.restore_snapshot(state_id, request.snapshot_id)
        return StateResponse(**state_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"恢复快照失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复快照失败: {str(e)}")


@router.get("/{state_id}/history", response_model=StateHistoryResponse)
async def get_state_history(
    state_id: str = Path(..., description="状态ID"),
    limit: int = Query(100, ge=1, le=1000, description="历史记录数量限制"),
    state_service: StateService = Depends(get_state_service)
) -> StateHistoryResponse:
    """获取状态历史记录
    
    Args:
        state_id: 状态ID
        limit: 历史记录数量限制
        
    Returns:
        状态历史记录
    """
    try:
        history_data = await state_service.get_state_history(state_id, limit)
        return StateHistoryResponse(**history_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")