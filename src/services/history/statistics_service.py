"""历史统计服务

提供丰富的历史数据查询和分析功能。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import asdict

from src.interfaces.repository.history import IHistoryRepository
from src.interfaces.logger import ILogger
from src.core.history.entities import (
    WorkflowTokenStatistics, WorkflowTokenSummary, TokenUsageRecord,
    CostRecord, RecordType
)
from src.interfaces.history.exceptions import StatisticsError
from src.interfaces.container.exceptions import ValidationError


class HistoryStatisticsService:
    """历史统计服务
    
    提供历史数据的查询、分析和报告功能。
    """
    
    def __init__(self, storage: IHistoryRepository, logger: Optional[ILogger] = None):
        """
        初始化统计服务
        
        Args:
            storage: 历史存储
            logger: 日志记录器
        """
        self._storage = storage
        self._logger = logger
    
    async def get_workflow_token_summary(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> WorkflowTokenSummary:
        """
        获取工作流Token汇总统计
        
        Args:
            workflow_id: 工作流ID
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            WorkflowTokenSummary: 汇总统计
        """
        try:
            if not workflow_id:
                raise ValidationError("工作流ID不能为空")
            
            # 获取指定时间范围内的所有模型统计
            model_stats = await self._storage.get_workflow_token_stats(
                workflow_id, None, start_time, end_time
            )
            
            # 创建汇总统计
            summary = WorkflowTokenSummary(workflow_id=workflow_id)
            
            # 添加各模型统计
            for stats in model_stats:
                summary.add_model_stats(stats)
            
            # 更新时间范围
            if start_time:
                summary.period_start = start_time
            if end_time:
                summary.period_end = end_time
            
            if self._logger:
                self._logger.debug(f"获取工作流汇总统计: {workflow_id}, "
                                 f"总Token: {summary.total_tokens}, "
                                 f"总成本: {summary.total_cost:.6f}")
            
            return summary
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            if self._logger:
                self._logger.error(f"获取工作流汇总统计失败: {e}")
            raise StatisticsError(f"获取工作流汇总统计失败: {e}", workflow_id=workflow_id)
    
    async def get_cross_workflow_comparison(
        self,
        workflow_ids: List[str],
        metric: str = "total_tokens",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取跨工作流对比统计
        
        Args:
            workflow_ids: 工作流ID列表
            metric: 对比指标 ("total_tokens", "total_cost", "total_requests")
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            Dict[str, Any]: 对比结果
        """
        try:
            if not workflow_ids:
                raise ValidationError("工作流ID列表不能为空")
            
            if metric not in ["total_tokens", "total_cost", "total_requests"]:
                raise ValidationError(f"不支持的对比指标: {metric}")
            
            comparison: Dict[str, Any] = {
                "metric": metric,
                "workflow_ids": workflow_ids,
                "period": {
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                },
                "data": {},
                "ranking": [],
                "summary": {}
            }
            
            # 获取各工作流的统计数据
            for workflow_id in workflow_ids:
                try:
                    summary = await self.get_workflow_token_summary(
                        workflow_id, start_time, end_time
                    )
                    
                    value: Union[int, float] = 0
                    if metric == "total_tokens":
                        value = summary.total_tokens
                    elif metric == "total_cost":
                        value = summary.total_cost
                    elif metric == "total_requests":
                        value = summary.total_requests
                    
                    comparison["data"][workflow_id] = {
                        "value": value,
                        "models_used": summary.models_used,
                        "most_used_model": summary.most_used_model,
                        "most_expensive_model": summary.most_expensive_model
                    }
                    
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"获取工作流 {workflow_id} 统计失败: {e}")
                    comparison["data"][workflow_id] = {
                        "value": 0,
                        "error": str(e)
                    }
            
            # 生成排名
            sorted_workflows = sorted(
                comparison["data"].items(),
                key=lambda x: x[1].get("value", 0),
                reverse=True
            )
            comparison["ranking"] = [
                {"workflow_id": wf_id, **data} for wf_id, data in sorted_workflows
            ]
            
            # 生成汇总
            values = [data.get("value", 0) for data in comparison["data"].values()]
            comparison["summary"] = {
                "total_workflows": len(workflow_ids),
                "successful_workflows": len([v for v in values if v > 0]),
                "total_value": sum(values),
                "average_value": sum(values) / len(values) if values else 0,
                "max_value": max(values) if values else 0,
                "min_value": min(values) if values else 0
            }
            
            return comparison
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            if self._logger:
                self._logger.error(f"获取跨工作流对比统计失败: {e}")
            raise StatisticsError(f"获取跨工作流对比统计失败: {e}")
    
    async def get_model_usage_trends(
        self,
        workflow_id: str,
        days: int = 7,
        group_by: str = "day"
    ) -> Dict[str, Any]:
        """
        获取模型使用趋势
        
        Args:
            workflow_id: 工作流ID
            days: 分析天数
            group_by: 分组方式 ("day", "hour", "model")
            
        Returns:
            Dict[str, Any]: 趋势数据
        """
        try:
            if not workflow_id:
                raise ValidationError("工作流ID不能为空")
            
            if days <= 0:
                raise ValidationError("天数必须大于0")
            
            if group_by not in ["day", "hour", "model"]:
                raise ValidationError(f"不支持的分组方式: {group_by}")
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            trends = {
                "workflow_id": workflow_id,
                "period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "days": days
                },
                "group_by": group_by,
                "data": {}
            }
            
            if group_by == "day":
                trends["data"] = await self._get_daily_trends(workflow_id, start_time, end_time)
            elif group_by == "hour":
                trends["data"] = await self._get_hourly_trends(workflow_id, start_time, end_time)
            elif group_by == "model":
                trends["data"] = await self._get_model_trends(workflow_id, start_time, end_time)
            
            # 生成趋势分析
            trends["analysis"] = self._analyze_trends(trends["data"])  # type: ignore
            
            return trends
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            if self._logger:
                self._logger.error(f"获取模型使用趋势失败: {e}")
            raise StatisticsError(f"获取模型使用趋势失败: {e}", workflow_id=workflow_id)
    
    async def get_cost_analysis(
        self,
        workflow_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取成本分析
        
        Args:
            workflow_id: 工作流ID过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            Dict[str, Any]: 成本分析结果
        """
        try:
            # 获取成本记录
            cost_records = await self._storage.get_records(
                workflow_id=workflow_id,
                record_type=RecordType.COST,
                start_time=start_time,
                end_time=end_time,
                limit=10000  # 获取足够多的记录进行分析
            )
            
            if not cost_records:
                return {
                    "total_cost": 0.0,
                    "total_requests": 0,
                    "avg_cost_per_request": 0.0,
                    "model_breakdown": {},
                    "provider_breakdown": {},
                    "time_distribution": {}
                }
            
            # 按模型和提供商分组
            model_costs: Dict[str, Dict[str, Any]] = {}
            provider_costs: Dict[str, Dict[str, Any]] = {}
            time_costs: Dict[str, Dict[str, Any]] = {}
            total_cost = 0.0
            total_requests = len(cost_records)
            
            for record in cost_records:
                if not isinstance(record, CostRecord):
                    continue
                
                total_cost += record.total_cost
                
                # 按模型分组
                if record.model not in model_costs:
                    model_costs[record.model] = {
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "request_count": 0,
                        "avg_cost_per_token": 0.0
                    }
                
                model_costs[record.model]["total_cost"] += record.total_cost
                model_costs[record.model]["total_tokens"] += record.total_tokens
                model_costs[record.model]["request_count"] += 1
                model_costs[record.model]["avg_cost_per_token"] = (
                    model_costs[record.model]["total_cost"] / 
                    model_costs[record.model]["total_tokens"]
                    if model_costs[record.model]["total_tokens"] > 0 else 0.0
                )
                
                # 按提供商分组
                if record.provider not in provider_costs:
                    provider_costs[record.provider] = {
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "request_count": 0,
                        "models": set()
                    }
                
                provider_costs[record.provider]["total_cost"] += record.total_cost
                provider_costs[record.provider]["total_tokens"] += record.total_tokens
                provider_costs[record.provider]["request_count"] += 1
                provider_costs[record.provider]["models"].add(record.model)
                
                # 按时间分组（按天）
                date_key = record.timestamp.date().isoformat()
                if date_key not in time_costs:
                    time_costs[date_key] = {
                        "total_cost": 0.0,
                        "request_count": 0
                    }
                
                time_costs[date_key]["total_cost"] += record.total_cost
                time_costs[date_key]["request_count"] += 1
            
            # 转换set为list以便序列化
            for provider_data in provider_costs.values():
                provider_data["models"] = list(provider_data["models"])
            
            return {
                "total_cost": total_cost,
                "total_requests": total_requests,
                "avg_cost_per_request": total_cost / total_requests if total_requests > 0 else 0.0,
                "model_breakdown": model_costs,
                "provider_breakdown": provider_costs,
                "time_distribution": time_costs,
                "period": {
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                }
            }
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取成本分析失败: {e}")
            raise StatisticsError(f"获取成本分析失败: {e}")
    
    async def get_efficiency_metrics(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取效率指标
        
        Args:
            workflow_id: 工作流ID
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            Dict[str, Any]: 效率指标
        """
        try:
            # 获取Token使用记录
            token_records = await self._storage.get_records(
                workflow_id=workflow_id,
                record_type=RecordType.TOKEN_USAGE,
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )
            
            if not token_records:
                return {
                    "total_requests": 0,
                    "avg_tokens_per_request": 0.0,
                    "token_efficiency": {},
                    "model_efficiency": {}
                }
            
            # 计算基本指标
            total_requests = len(token_records)
            total_tokens = sum(r.total_tokens for r in token_records if isinstance(r, TokenUsageRecord))
            avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0.0
            
            # 按模型分析效率
            model_stats: Dict[str, Dict[str, Any]] = {}
            for record in token_records:
                if not isinstance(record, TokenUsageRecord):
                    continue
                
                if record.model not in model_stats:
                    model_stats[record.model] = {
                        "total_tokens": 0,
                        "total_requests": 0,
                        "avg_tokens_per_request": 0.0,
                        "cost_efficiency": 0.0  # tokens per cost unit
                    }
                
                model_stats[record.model]["total_tokens"] += record.total_tokens
                model_stats[record.model]["total_requests"] += 1
                model_stats[record.model]["avg_tokens_per_request"] = (
                    model_stats[record.model]["total_tokens"] / 
                    model_stats[record.model]["total_requests"]
                )
            
            # 获取成本信息以计算成本效率
            try:
                cost_analysis = await self.get_cost_analysis(workflow_id, start_time, end_time)
                
                for model, cost_data in cost_analysis["model_breakdown"].items():
                    if model in model_stats and cost_data["total_cost"] > 0:
                        model_stats[model]["cost_efficiency"] = (
                            cost_data["total_tokens"] / cost_data["total_cost"]
                        )
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"获取成本分析失败，跳过成本效率计算: {e}")
            
            # 计算整体效率指标
            efficiency_metrics = {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "avg_tokens_per_request": avg_tokens_per_request,
                "model_efficiency": model_stats,
                "token_efficiency": {
                    "best_model": max(model_stats.items(), key=lambda x: x[1]["avg_tokens_per_request"])[0] if model_stats else None,
                    "worst_model": min(model_stats.items(), key=lambda x: x[1]["avg_tokens_per_request"])[0] if model_stats else None,
                    "most_cost_efficient": max(model_stats.items(), key=lambda x: x[1]["cost_efficiency"])[0] if model_stats else None
                }
            }
            
            return efficiency_metrics
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取效率指标失败: {e}")
            raise StatisticsError(f"获取效率指标失败: {e}", workflow_id=workflow_id)
    
    async def _get_daily_trends(
        self,
        workflow_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """获取每日趋势"""
        daily_stats = {}
        current_date = start_time.date()
        
        while current_date <= end_time.date():
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            
            day_summary = await self.get_workflow_token_summary(
                workflow_id, day_start, day_end
            )
            
            daily_stats[current_date.isoformat()] = {
                "total_tokens": day_summary.total_tokens,
                "total_cost": day_summary.total_cost,
                "total_requests": day_summary.total_requests,
                "models_used": day_summary.models_used,
                "model_breakdown": {
                    model: {
                        "tokens": stats.total_tokens,
                        "cost": stats.total_cost,
                        "requests": stats.request_count
                    }
                    for model, stats in day_summary.model_breakdown.items()
                }
            }
            
            current_date += timedelta(days=1)
        
        return daily_stats
    
    async def _get_hourly_trends(
        self,
        workflow_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """获取每小时趋势"""
        hourly_stats = {}
        current_time = start_time.replace(minute=0, second=0, microsecond=0)
        
        while current_time <= end_time:
            hour_end = current_time + timedelta(hours=1) - timedelta(microseconds=1)
            
            hour_summary = await self.get_workflow_token_summary(
                workflow_id, current_time, hour_end
            )
            
            hourly_stats[current_time.isoformat()] = {
                "total_tokens": hour_summary.total_tokens,
                "total_cost": hour_summary.total_cost,
                "total_requests": hour_summary.total_requests,
                "models_used": hour_summary.models_used
            }
            
            current_time += timedelta(hours=1)
        
        return hourly_stats
    
    async def _get_model_trends(
        self,
        workflow_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """获取按模型分组的趋势"""
        summary = await self.get_workflow_token_summary(workflow_id, start_time, end_time)
        
        model_trends = {}
        for model, stats in summary.model_breakdown.items():
            model_trends[model] = {
                "total_tokens": stats.total_tokens,
                "total_cost": stats.total_cost,
                "total_requests": stats.request_count,
                "avg_tokens_per_request": stats.avg_tokens_per_request,
                "avg_cost_per_request": stats.avg_cost_per_request,
                "usage_percentage": (stats.total_tokens / summary.total_tokens * 100) if summary.total_tokens > 0 else 0
            }
        
        return model_trends
    
    def _analyze_trends(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析趋势数据"""
        if not trend_data:
            return {}
        
        analysis = {
            "data_points": len(trend_data),
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_requests": 0,
            "peak_usage": None,
            "lowest_usage": None,
            "growth_rate": 0.0
        }
        
        # 计算汇总数据
        tokens_data = []
        cost_data = []
        requests_data = []
        
        for key, data in trend_data.items():
            tokens_data.append(data.get("total_tokens", 0))
            cost_data.append(data.get("total_cost", 0.0))
            requests_data.append(data.get("total_requests", 0))
            
            analysis["total_tokens"] += data.get("total_tokens", 0)
            analysis["total_cost"] += data.get("total_cost", 0.0)
            analysis["total_requests"] += data.get("total_requests", 0)
        
        if tokens_data:
            max_tokens = max(tokens_data)
            min_tokens = min(tokens_data)
            
            # 找到峰值和最低值的时间点
            for key, data in trend_data.items():
                if data.get("total_tokens", 0) == max_tokens:
                    analysis["peak_usage"] = {  # type: ignore
                        "time": key,
                        "tokens": max_tokens,
                        "cost": data.get("total_cost", 0.0),
                        "requests": data.get("total_requests", 0)
                    }
                
                if data.get("total_tokens", 0) == min_tokens:
                    analysis["lowest_usage"] = {  # type: ignore
                        "time": key,
                        "tokens": min_tokens,
                        "cost": data.get("total_cost", 0.0),
                        "requests": data.get("total_requests", 0)
                    }
            
            # 计算增长率（简单线性趋势）
            if len(tokens_data) > 1:
                first_half = tokens_data[:len(tokens_data)//2]
                second_half = tokens_data[len(tokens_data)//2:]
                
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                
                analysis["growth_rate"] = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0.0
        
        return analysis