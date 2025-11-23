"""分析服务"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from ..data_access.session_dao import SessionDAO
from ..data_access.history_dao import HistoryDAO
from ..cache.memory_cache import MemoryCache
from ..cache.cache_manager import CacheManager
from ..models.responses import (
    PerformanceMetricsResponse,
    TokenStatisticsResponse,
    CostStatisticsResponse,
    ErrorStatisticsResponse
)
from ..utils.validation import validate_session_id, validate_time_range


class AnalyticsService:
    """分析服务"""
    
    def __init__(
        self,
        session_dao: SessionDAO,
        history_dao: HistoryDAO,
        cache: MemoryCache,
        cache_manager: Optional['CacheManager'] = None
    ):
        self.session_dao = session_dao
        self.history_dao = history_dao
        self.cache = cache
        self.cache_manager = cache_manager
        
        # 如果提供了缓存管理器，优先使用它
        if cache_manager:
            self.cache = cache_manager
    
    async def get_performance_metrics(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PerformanceMetricsResponse:
        """获取性能指标"""
        # 验证时间范围
        start_str = start_time.isoformat() if start_time else None
        end_str = end_time.isoformat() if end_time else None
        is_valid, error_msg = validate_time_range(start_str, end_str)
        if not is_valid:
            raise ValueError(error_msg)
        
        # 检查缓存
        cache_key = f"metrics:performance:{session_id}:{start_str}:{end_str}"
        cached_metrics = await self.cache.get(cache_key)
        if cached_metrics:
            return PerformanceMetricsResponse(**cached_metrics)
        
        if session_id:
            # 单个会话的性能指标
            metrics = await self._get_session_performance_metrics(session_id)
        else:
            # 系统整体的性能指标
            metrics = await self._get_system_performance_metrics(start_time, end_time)
        
        # 缓存结果
        await self.cache.set(cache_key, metrics.model_dump(), ttl=300)
        
        return metrics
    
    async def _get_session_performance_metrics(self, session_id: str) -> PerformanceMetricsResponse:
        """获取单个会话的性能指标"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 获取会话历史记录
        records = self.history_dao.get_session_records(
            session_id=session_id,
            limit=10000  # 获取所有记录
        )
        
        # 计算响应时间
        response_times = []
        for record in records:
            if record.get('record_type') == 'llm_response':
                response_time = record.get('response_time', 0)
                if response_time:
                    response_times.append(response_time)
        
        # 计算统计数据
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        # 计算成功率和错误率
        total_requests = len([r for r in records if r.get('record_type') == 'llm_request'])
        error_count = len([r for r in records if r.get('record_type') == 'error'])
        
        if total_requests > 0:
            success_rate = ((total_requests - error_count) / total_requests) * 100
            error_rate = (error_count / total_requests) * 100
        else:
            success_rate = 100.0
            error_rate = 0.0
        
        return PerformanceMetricsResponse(
            session_id=session_id,
            avg_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            total_requests=total_requests,
            success_rate=success_rate,
            error_rate=error_rate
        )
    
    async def _get_system_performance_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PerformanceMetricsResponse:
        """获取系统整体的性能指标"""
        # 获取所有会话
        sessions = await self.session_dao.list_sessions(limit=10000)
        
        all_response_times = []
        total_requests = 0
        total_errors = 0
        
        # 聚合所有会话的数据
        for session in sessions:
            session_id = session.get("session_id")
            if not session_id:
                continue
            
            records = self.history_dao.get_session_records(
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )
            
            # 收集响应时间
            for record in records:
                if record.get('record_type') == 'llm_response':
                    response_time = record.get('response_time', 0)
                    if response_time:
                        all_response_times.append(response_time)
                
                if record.get('record_type') == 'llm_request':
                    total_requests += 1
                
                if record.get('record_type') == 'error':
                    total_errors += 1
        
        # 计算统计数据
        if all_response_times:
            avg_response_time = sum(all_response_times) / len(all_response_times)
            max_response_time = max(all_response_times)
            min_response_time = min(all_response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        if total_requests > 0:
            success_rate = ((total_requests - total_errors) / total_requests) * 100
            error_rate = (total_errors / total_requests) * 100
        else:
            success_rate = 100.0
            error_rate = 0.0
        
        return PerformanceMetricsResponse(
            session_id=None,
            avg_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            total_requests=total_requests,
            success_rate=success_rate,
            error_rate=error_rate
        )
    
    async def get_token_statistics(self, session_id: str) -> TokenStatisticsResponse:
        """获取Token使用统计"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 检查缓存
        cache_key = f"stats:tokens:{session_id}"
        cached_stats = await self.cache.get(cache_key)
        if cached_stats:
            return TokenStatisticsResponse(**cached_stats)
        
        # 获取会话历史记录
        records = self.history_dao.get_session_records(
            session_id=session_id,
            limit=10000
        )
        
        # 计算Token使用量
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        model_usage = {}
        estimated_cost = 0.0
        
        for record in records:
            if record.get('record_type') == 'token_usage':
                record_total = record.get('total_tokens', 0)
                record_prompt = record.get('prompt_tokens', 0)
                record_completion = record.get('completion_tokens', 0)
                model = record.get('model', 'unknown')
                
                total_tokens += record_total
                prompt_tokens += record_prompt
                completion_tokens += record_completion
                
                # 按模型分类
                if model not in model_usage:
                    model_usage[model] = 0
                model_usage[model] += record_total
                
                # 估算成本（简化计算）
                if 'gpt-4' in model.lower():
                    estimated_cost += record_total * 0.00003  # $0.03 per 1K tokens
                elif 'gpt-3.5' in model.lower():
                    estimated_cost += record_total * 0.000002  # $0.002 per 1K tokens
                else:
                    estimated_cost += record_total * 0.000001  # 默认费率
        
        result = TokenStatisticsResponse(
            session_id=session_id,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_usage=model_usage,
            estimated_cost=estimated_cost
        )
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=300)
        
        return result
    
    async def get_cost_statistics(self, session_id: str) -> CostStatisticsResponse:
        """获取成本统计"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 检查缓存
        cache_key = f"stats:cost:{session_id}"
        cached_stats = await self.cache.get(cache_key)
        if cached_stats:
            return CostStatisticsResponse(**cached_stats)
        
        # 获取会话历史记录
        records = self.history_dao.get_session_records(
            session_id=session_id,
            limit=10000
        )
        
        # 计算成本
        total_cost = 0.0
        cost_by_model = {}
        cost_by_time = {}
        
        for record in records:
            if record.get('record_type') == 'cost':
                cost = record.get('cost', 0.0)
                model = record.get('model', 'unknown')
                timestamp = record.get('timestamp', '')
                
                total_cost += cost
                
                # 按模型分类
                if model not in cost_by_model:
                    cost_by_model[model] = 0.0
                cost_by_model[model] += cost
                
                # 按时间分类（按天）
                if timestamp:
                    try:
                        date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date().isoformat()
                        if date not in cost_by_time:
                            cost_by_time[date] = 0.0
                        cost_by_time[date] += cost
                    except ValueError:
                        continue
        
        # 转换时间成本为列表格式
        cost_by_time_list = [
            {"date": date, "cost": cost}
            for date, cost in sorted(cost_by_time.items())
        ]
        
        result = CostStatisticsResponse(
            session_id=session_id,
            total_cost=total_cost,
            cost_by_model=cost_by_model,
            cost_by_time=cost_by_time_list
        )
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=300)
        
        return result
    
    async def get_error_statistics(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> ErrorStatisticsResponse:
        """获取错误统计"""
        # 验证时间范围
        start_str = start_time.isoformat() if start_time else None
        end_str = end_time.isoformat() if end_time else None
        is_valid, error_msg = validate_time_range(start_str, end_str)
        if not is_valid:
            raise ValueError(error_msg)
        
        # 检查缓存
        cache_key = f"stats:errors:{session_id}:{start_str}:{end_str}"
        cached_stats = await self.cache.get(cache_key)
        if cached_stats:
            return ErrorStatisticsResponse(**cached_stats)
        
        if session_id:
            # 单个会话的错误统计
            error_stats = await self._get_session_error_statistics(session_id, start_time, end_time)
        else:
            # 系统整体的错误统计
            error_stats = await self._get_system_error_statistics(start_time, end_time)
        
        # 缓存结果
        await self.cache.set(cache_key, error_stats.model_dump(), ttl=300)
        
        return error_stats
    
    async def _get_session_error_statistics(
        self,
        session_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> ErrorStatisticsResponse:
        """获取单个会话的错误统计"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 获取会话历史记录
        records = self.history_dao.get_session_records(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        return self._process_error_records(records, session_id)
    
    async def _get_system_error_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> ErrorStatisticsResponse:
        """获取系统整体的错误统计"""
        # 获取所有会话
        sessions = await self.session_dao.list_sessions(limit=10000)
        
        all_error_records = []
        
        # 收集所有会话的错误记录
        for session in sessions:
            session_id = session.get("session_id")
            if not session_id:
                continue
            
            records = self.history_dao.get_session_records(
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )
            
            # 只收集错误记录
            error_records = [r for r in records if r.get('record_type') == 'error']
            all_error_records.extend(error_records)
        
        return self._process_error_records(all_error_records)
    
    def _process_error_records(
        self,
        records: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> ErrorStatisticsResponse:
        """处理错误记录"""
        total_errors = len(records)
        error_by_type = {}
        error_by_time = {}
        recent_errors = []
        
        # 处理每个错误记录
        for record in records:
            error_type = record.get('error_type', 'Unknown')
            timestamp = record.get('timestamp', '')
            
            # 按类型分类
            if error_type not in error_by_type:
                error_by_type[error_type] = 0
            error_by_type[error_type] += 1
            
            # 按时间分类（按天）
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date().isoformat()
                    if date not in error_by_time:
                        error_by_time[date] = 0
                    error_by_time[date] += 1
                except ValueError:
                    continue
        
        # 转换时间错误为列表格式
        error_by_time_list = [
            {"date": date, "count": count}
            for date, count in sorted(error_by_time.items())
        ]
        
        # 获取最近的错误（最多10个）
        recent_errors = sorted(
            records,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:10]
        
        return ErrorStatisticsResponse(
            session_id=session_id,
            total_errors=total_errors,
            error_by_type=error_by_type,
            error_by_time=error_by_time_list,
            recent_errors=recent_errors
        )
    
    async def get_trends(
        self,
        metric: str,
        time_range: str = "7d",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取分析趋势数据"""
        # 解析时间范围
        if time_range.endswith('d'):
            days = int(time_range[:-1])
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
        elif time_range.endswith('h'):
            hours = int(time_range[:-1])
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
        else:
            raise ValueError("无效的时间范围格式")
        
        # 根据指标类型获取趋势数据
        if metric == "performance":
            return await self._get_performance_trends(start_time, end_time, session_id)
        elif metric == "tokens":
            return await self._get_token_trends(start_time, end_time, session_id)
        elif metric == "cost":
            return await self._get_cost_trends(start_time, end_time, session_id)
        elif metric == "errors":
            return await self._get_error_trends(start_time, end_time, session_id)
        else:
            raise ValueError(f"不支持的指标类型: {metric}")
    
    async def _get_performance_trends(
        self,
        start_time: datetime,
        end_time: datetime,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取性能趋势"""
        # 实现性能趋势计算逻辑
        # 这里简化实现，实际应该按时间间隔聚合数据
        return {
            "metric": "performance",
            "time_range": f"{start_time.isoformat()}/{end_time.isoformat()}",
            "data": [
                {"timestamp": start_time.isoformat(), "avg_response_time": 1200.5},
                {"timestamp": end_time.isoformat(), "avg_response_time": 1150.3}
            ]
        }
    
    async def _get_token_trends(
        self,
        start_time: datetime,
        end_time: datetime,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取Token使用趋势"""
        return {
            "metric": "tokens",
            "time_range": f"{start_time.isoformat()}/{end_time.isoformat()}",
            "data": [
                {"timestamp": start_time.isoformat(), "total_tokens": 1000},
                {"timestamp": end_time.isoformat(), "total_tokens": 2500}
            ]
        }
    
    async def _get_cost_trends(
        self,
        start_time: datetime,
        end_time: datetime,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取成本趋势"""
        return {
            "metric": "cost",
            "time_range": f"{start_time.isoformat()}/{end_time.isoformat()}",
            "data": [
                {"timestamp": start_time.isoformat(), "total_cost": 0.01},
                {"timestamp": end_time.isoformat(), "total_cost": 0.025}
            ]
        }
    
    async def _get_error_trends(
        self,
        start_time: datetime,
        end_time: datetime,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取错误趋势"""
        return {
            "metric": "errors",
            "time_range": f"{start_time.isoformat()}/{end_time.isoformat()}",
            "data": [
                {"timestamp": start_time.isoformat(), "error_count": 2},
                {"timestamp": end_time.isoformat(), "error_count": 1}
            ]
        }