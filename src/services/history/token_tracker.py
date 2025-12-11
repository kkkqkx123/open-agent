"""Token追踪服务实现

提供基于LLM模块的精确Token追踪功能，支持工作流和模型维度统计。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import asdict

from src.core.history.interfaces import ITokenTracker
from src.interfaces.repository.history import IHistoryRepository
from src.core.history.entities import (
    TokenUsageRecord, WorkflowTokenStatistics, WorkflowTokenSummary,
    TokenSource
)
from src.core.history.base import BaseTokenTracker
from src.services.llm.token_calculation_service import TokenCalculationService
from src.interfaces.history.exceptions import StatisticsError
from src.interfaces.container.exceptions import ValidationError


logger = get_logger(__name__)


class WorkflowTokenTracker(BaseTokenTracker):
    """工作流Token追踪器
    
    基于LLM模块的精确Token计算，支持工作流和模型维度统计。
    """
    
    def __init__(
        self,
        storage: IHistoryRepository,
        token_calculation_service: TokenCalculationService,
        cache_ttl: int = 300  # 缓存5分钟
    ):
        """
        初始化Token追踪器
        
        Args:
            storage: 历史存储
            token_calculation_service: Token计算服务
            cache_ttl: 缓存生存时间（秒）
        """
        super().__init__(storage)
        self._token_service = token_calculation_service
        self._cache_ttl = cache_ttl
        self._workflow_stats_cache: Dict[str, Dict[str, WorkflowTokenStatistics]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._logger = get_logger(self.__class__.__name__)
    
    async def track_workflow_token_usage(
        self,
        workflow_id: str,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        source: TokenSource = TokenSource.API,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        追踪工作流Token使用
        
        Args:
            workflow_id: 工作流ID
            model: 模型名称
            provider: 提供商名称
            prompt_tokens: Prompt token数量
            completion_tokens: Completion token数量
            source: Token来源
            confidence: 置信度
            metadata: 额外元数据
        """
        try:
            # 验证输入参数
            self._validate_token_usage_params(
                workflow_id, model, provider, prompt_tokens, completion_tokens, confidence
            )
            
            # 调用基类方法
            await super().track_workflow_token_usage(
                workflow_id, model, provider, prompt_tokens, completion_tokens,
                source, confidence, metadata
            )
            
            # 清除相关缓存
            self._invalidate_cache(workflow_id, model)
            
        except Exception as e:
            if isinstance(e, (ValidationError, StatisticsError)):
                raise
            self._logger.error(f"追踪工作流Token使用失败: {e}")
            raise StatisticsError(f"追踪工作流Token使用失败: {e}", workflow_id=workflow_id)
    
    async def track_llm_request_with_precise_tokens(
        self,
        workflow_id: str,
        session_id: str,
        model: str,
        provider: str,
        messages: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        使用精确Token计算追踪LLM请求
        
        Args:
            workflow_id: 工作流ID
            session_id: 会话ID
            model: 模型名称
            provider: 提供商名称
            messages: 消息列表
            parameters: 请求参数
            metadata: 额外元数据
            
        Returns:
            str: 请求记录ID
        """
        try:
            # 使用LLM模块的精确Token计算
            from src.infrastructure.messages.base import BaseMessage
            
            # 转换消息格式
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # 计算精确的Token数量
            estimated_tokens = self._token_service.calculate_messages_tokens(
                lc_messages, provider, model
            )
            
            # 追踪请求
            request_id = await self.track_llm_request(
                workflow_id=workflow_id,
                session_id=session_id,
                model=model,
                provider=provider,
                messages=messages,
                parameters=parameters,
                estimated_tokens=estimated_tokens,
                metadata={
                    **(metadata or {}),
                    "token_calculation_method": "precise",
                    "calculation_timestamp": datetime.now().isoformat()
                }
            )
            
            self._logger.debug(f"精确Token计算: 模型={model}, Token={estimated_tokens}")
            
            return request_id
            
        except Exception as e:
            self._logger.error(f"精确Token计算追踪失败: {e}")
            raise StatisticsError(f"精确Token计算追踪失败: {e}")
    
    async def get_workflow_statistics(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> WorkflowTokenStatistics:
        """
        获取工作流统计
        
        Args:
            workflow_id: 工作流ID
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            WorkflowTokenStatistics: 统计信息
        """
        try:
            # 检查缓存
            cache_key = f"{workflow_id}:{model or 'all'}"
            if self._is_cache_valid(cache_key):
                cached_stats = self._workflow_stats_cache.get(cache_key)
                if cached_stats and model:
                    return cached_stats[model]
                elif cached_stats and not model:
                    # 如果没有指定模型，返回第一个统计
                    return list(cached_stats.values())[0] if cached_stats else WorkflowTokenStatistics(workflow_id=workflow_id, model="unknown")
            
            # 从存储获取统计
            stats_list = await self._storage.get_workflow_token_stats(
                workflow_id, model, start_time, end_time
            )
            
            if stats_list:
                stats = stats_list[0]
                
                # 如果有多个统计记录（不同时间范围），合并它们
                if len(stats_list) > 1:
                    stats = self._merge_statistics(stats_list)
                
                # 更新缓存
                self._update_cache(cache_key, stats)
                
                return stats
            
            # 返回空统计
            empty_stats = WorkflowTokenStatistics(
                workflow_id=workflow_id,
                model=model or "unknown"
            )
            
            # 缓存空统计
            self._update_cache(cache_key, empty_stats)
            
            return empty_stats
            
        except Exception as e:
            self._logger.error(f"获取工作流统计失败: {e}")
            raise StatisticsError(f"获取工作流统计失败: {e}", workflow_id=workflow_id)
    
    async def get_multi_model_statistics(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, WorkflowTokenStatistics]:
        """
        获取工作流多模型统计
        
        Args:
            workflow_id: 工作流ID
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            Dict[str, WorkflowTokenStatistics]: 模型名称到统计信息的映射
        """
        try:
            # 检查缓存
            cache_key = f"{workflow_id}:multi_model"
            if self._is_cache_valid(cache_key):
                cached_stats = self._workflow_stats_cache.get(cache_key)
                if cached_stats:
                    return cached_stats
            
            # 从存储获取所有模型统计
            stats_list = await self._storage.get_workflow_token_stats(
                workflow_id, None, start_time, end_time
            )
            
            # 按模型分组
            model_stats = {}
            for stats in stats_list:
                model_stats[stats.model] = stats
            
            # 更新缓存
            self._update_cache(cache_key, model_stats)
            
            return model_stats
            
        except Exception as e:
            self._logger.error(f"获取多模型统计失败: {e}")
            raise StatisticsError(f"获取多模型统计失败: {e}", workflow_id=workflow_id)
    
    async def get_cross_workflow_statistics(
        self,
        workflow_ids: List[str],
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, WorkflowTokenStatistics]:
        """
        获取跨工作流统计
        
        Args:
            workflow_ids: 工作流ID列表
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            Dict[str, WorkflowTokenStatistics]: 工作流ID到统计信息的映射
        """
        try:
            cross_stats = {}
            
            for workflow_id in workflow_ids:
                try:
                    stats = await self.get_workflow_statistics(
                        workflow_id, model, start_time, end_time
                    )
                    cross_stats[workflow_id] = stats
                except Exception as e:
                    self._logger.warning(f"获取工作流 {workflow_id} 统计失败: {e}")
                    # 继续处理其他工作流
                    continue
            
            return cross_stats
            
        except Exception as e:
            self._logger.error(f"获取跨工作流统计失败: {e}")
            raise StatisticsError(f"获取跨工作流统计失败: {e}")
    
    async def get_workflow_summary(
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
            # 获取所有模型统计
            model_stats = await self.get_multi_model_statistics(
                workflow_id, start_time, end_time
            )
            
            # 创建汇总统计
            summary = WorkflowTokenSummary(workflow_id=workflow_id)
            
            # 添加各模型统计
            for stats in model_stats.values():
                summary.add_model_stats(stats)
            
            return summary
            
        except Exception as e:
            self._logger.error(f"获取工作流汇总统计失败: {e}")
            raise StatisticsError(f"获取工作流汇总统计失败: {e}", workflow_id=workflow_id)
    
    async def get_model_usage_trends(
        self,
        workflow_id: str,
        days: int = 7
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取模型使用趋势
        
        Args:
            workflow_id: 工作流ID
            days: 分析天数
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: 按日期分组的趋势数据
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 按天分组获取统计
            daily_stats = {}
            current_date = start_time.date()
            
            while current_date <= end_time.date():
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                day_summary = await self.get_workflow_summary(
                    workflow_id, day_start, day_end
                )
                
                daily_stats[current_date.isoformat()] = {
                    "total_tokens": day_summary.total_tokens,
                    "total_cost": day_summary.total_cost,
                    "total_requests": day_summary.total_requests,
                    "model_breakdown": {
                        model: {
                            "tokens": stats.total_tokens,
                            "cost": stats.total_cost,
                            "requests": stats.request_count,
                            "avg_tokens_per_request": stats.avg_tokens_per_request,
                            "avg_cost_per_request": stats.avg_cost_per_request
                        }
                        for model, stats in day_summary.model_breakdown.items()
                    }
                }
                
                current_date += timedelta(days=1)
            
            return daily_stats  # type: ignore
            
        except Exception as e:
            self._logger.error(f"获取模型使用趋势失败: {e}")
            raise StatisticsError(f"获取模型使用趋势失败: {e}", workflow_id=workflow_id)
    
    def _validate_token_usage_params(
        self,
        workflow_id: str,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        confidence: float
    ) -> None:
        """验证Token使用参数"""
        if not workflow_id:
            raise ValidationError("工作流ID不能为空")
        
        if not model:
            raise ValidationError("模型名称不能为空")
        
        if not provider:
            raise ValidationError("提供商不能为空")
        
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValidationError("Token数量不能为负数")
        
        if not 0.0 <= confidence <= 1.0:
            raise ValidationError("置信度必须在0.0到1.0之间")
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """转换为LangChain消息格式"""
        try:
            from src.infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage
            
            lc_messages = []
            for msg in messages:
                msg_type = msg.get("type", "human").lower()
                content = msg.get("content", "")
                
                if msg_type == "human" or msg_type == "user":
                    lc_messages.append(HumanMessage(content=content))  # type: ignore
                elif msg_type == "ai" or msg_type == "assistant":
                    lc_messages.append(AIMessage(content=content))  # type: ignore
                elif msg_type == "system":
                    lc_messages.append(SystemMessage(content=content))
                else:
                    # 默认为HumanMessage
                    lc_messages.append(HumanMessage(content=content))
            
            return lc_messages
            
        except Exception as e:
            self._logger.warning(f"转换消息格式失败: {e}")
            # 返回空列表，避免中断流程
            return []
    
    def _merge_statistics(self, stats_list: List[WorkflowTokenStatistics]) -> WorkflowTokenStatistics:
        """合并多个统计记录"""
        if not stats_list:
            raise ValidationError("统计列表不能为空")
        
        if len(stats_list) == 1:
            return stats_list[0]
        
        # 以第一个统计为基础
        merged = WorkflowTokenStatistics(
            workflow_id=stats_list[0].workflow_id,
            model=stats_list[0].model
        )
        
        # 合并所有统计
        for stats in stats_list:
            merged.total_prompt_tokens += stats.total_prompt_tokens
            merged.total_completion_tokens += stats.total_completion_tokens
            merged.total_tokens += stats.total_tokens
            merged.total_cost += stats.total_cost
            merged.request_count += stats.request_count
            
            # 更新时间范围
            if stats.period_start and (merged.period_start is None or stats.period_start < merged.period_start):
                merged.period_start = stats.period_start
            
            if stats.period_end and (merged.period_end is None or stats.period_end > merged.period_end):
                merged.period_end = stats.period_end
            
            if stats.last_updated > merged.last_updated:
                merged.last_updated = stats.last_updated
        
        return merged
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        return (datetime.now() - cache_time).total_seconds() < self._cache_ttl
    
    def _update_cache(self, cache_key: str, data: Any) -> None:
        """更新缓存"""
        self._workflow_stats_cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
    
    def _invalidate_cache(self, workflow_id: str, model: Optional[str] = None) -> None:
        """清除相关缓存"""
        keys_to_remove = []
        
        for cache_key in self._cache_timestamps.keys():
            if workflow_id in cache_key:
                if model is None or model in cache_key:
                    keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            self._workflow_stats_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
    
    def clear_all_cache(self) -> None:
        """清除所有缓存"""
        self._workflow_stats_cache.clear()
        self._cache_timestamps.clear()
        self._logger.info("清除了所有Token统计缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cache_size": len(self._workflow_stats_cache),
            "cache_ttl": self._cache_ttl,
            "cached_keys": list(self._cache_timestamps.keys()),
            "oldest_cache": min(self._cache_timestamps.values()).isoformat() if self._cache_timestamps else None,
            "newest_cache": max(self._cache_timestamps.values()).isoformat() if self._cache_timestamps else None
        }