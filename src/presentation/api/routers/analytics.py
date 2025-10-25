"""分析统计API路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..models.responses import (
    PerformanceMetricsResponse,
    TokenStatisticsResponse,
    CostStatisticsResponse,
    ErrorStatisticsResponse
)
from ..services.analytics_service import AnalyticsService
from ..dependencies import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    session_id: Optional[str] = Query(None, description="会话ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> PerformanceMetricsResponse:
    """获取性能指标"""
    try:
        return await analytics_service.get_performance_metrics(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/tokens/{session_id}", response_model=TokenStatisticsResponse)
async def get_token_statistics(
    session_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> TokenStatisticsResponse:
    """获取Token使用统计"""
    try:
        return await analytics_service.get_token_statistics(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Token统计失败: {str(e)}")


@router.get("/cost/{session_id}", response_model=CostStatisticsResponse)
async def get_cost_statistics(
    session_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> CostStatisticsResponse:
    """获取成本统计"""
    try:
        return await analytics_service.get_cost_statistics(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成本统计失败: {str(e)}")


@router.get("/errors", response_model=ErrorStatisticsResponse)
async def get_error_statistics(
    session_id: Optional[str] = Query(None, description="会话ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> ErrorStatisticsResponse:
    """获取错误统计"""
    try:
        return await analytics_service.get_error_statistics(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误统计失败: {str(e)}")


@router.get("/trends")
async def get_analytics_trends(
    metric: str = Query(..., description="指标类型"),
    time_range: str = Query("7d", description="时间范围"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """获取分析趋势数据"""
    try:
        return await analytics_service.get_trends(
            metric=metric,
            time_range=time_range,
            session_id=session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势数据失败: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_data(
    session_id: Optional[str] = Query(None, description="会话ID"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """获取仪表板数据"""
    try:
        # 获取各种统计数据
        performance = await analytics_service.get_performance_metrics(session_id=session_id)
        
        dashboard_data = {
            "performance": performance.model_dump(),
            "summary": {
                "avg_response_time": performance.avg_response_time,
                "total_requests": performance.total_requests,
                "success_rate": performance.success_rate,
                "error_rate": performance.error_rate
            }
        }
        
        # 如果指定了会话ID，获取更多详细信息
        if session_id:
            token_stats = await analytics_service.get_token_statistics(session_id)
            cost_stats = await analytics_service.get_cost_statistics(session_id)
            error_stats = await analytics_service.get_error_statistics(session_id=session_id)
            
            dashboard_data.update({
                "tokens": token_stats.model_dump(),
                "cost": cost_stats.model_dump(),
                "errors": error_stats.model_dump()
            })
        
        return dashboard_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/health")
async def get_analytics_health(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> dict:
    """获取分析服务健康状态"""
    try:
        # 这里可以添加健康检查逻辑
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "analytics"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")