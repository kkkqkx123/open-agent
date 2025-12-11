"""工作流管理API路由"""
from src.interfaces.dependency_injection import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import asyncio

from ..models.requests import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowRunRequest
from ..models.responses import WorkflowResponse, WorkflowListResponse, WorkflowExecutionResponse, ApiResponse
from ..services.workflow_service import WorkflowService
from ..dependencies import get_workflow_service

# 配置日志
logger = get_logger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("loaded_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowListResponse:
    """获取工作流列表"""
    try:
        return await workflow_service.list_workflows(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流列表失败: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowResponse:
    """获取特定工作流详情"""
    try:
        workflow = await workflow_service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流失败: {str(e)}")


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowResponse:
    """创建新工作流"""
    try:
        return await workflow_service.create_workflow(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工作流失败: {str(e)}")


@router.post("/load", response_model=ApiResponse)
async def load_workflow(
    config_path: str = Query(..., description="配置文件路径"),
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> ApiResponse:
    """加载工作流配置"""
    try:
        workflow_id = await workflow_service.load_workflow(config_path)
        return ApiResponse(
            success=True,
            message="工作流加载成功",
            data={"workflow_id": workflow_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载工作流失败: {str(e)}")


@router.post("/{workflow_id}/run", response_model=WorkflowExecutionResponse)
async def run_workflow(
    workflow_id: str,
    request: Optional[WorkflowRunRequest] = None,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowExecutionResponse:
    """运行工作流"""
    try:
        return await workflow_service.run_workflow(workflow_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"运行工作流失败: {str(e)}")


@router.post("/{workflow_id}/stream")
async def stream_workflow(
    workflow_id: str,
    request: Optional[WorkflowRunRequest] = None,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """流式运行工作流"""
    try:
        async def generate():
            async for chunk in workflow_service.stream_workflow(workflow_id, request):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用nginx缓冲
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式运行工作流失败: {str(e)}")


@router.get("/{workflow_id}/visualization")
async def get_workflow_visualization(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> dict:
    """获取工作流可视化数据"""
    try:
        visualization = await workflow_service.get_workflow_visualization(workflow_id)
        if not visualization:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return visualization
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流可视化失败: {str(e)}")


@router.delete("/{workflow_id}", response_model=ApiResponse)
async def unload_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> ApiResponse:
    """卸载工作流"""
    try:
        success = await workflow_service.unload_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return ApiResponse(success=True, message="工作流已卸载", data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卸载工作流失败: {str(e)}")


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> WorkflowResponse:
    """更新工作流"""
    try:
        updated_workflow = await workflow_service.update_workflow(workflow_id, request)
        if not updated_workflow:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return updated_workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新工作流失败: {str(e)}")


@router.get("/search/{query}", response_model=List[WorkflowResponse])
async def search_workflows(
    query: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
) -> List[WorkflowResponse]:
    """搜索工作流"""
    try:
        return await workflow_service.search_workflows(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索工作流失败: {str(e)}")