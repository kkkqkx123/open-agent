"""回放分析器实现"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.domain.replay.interfaces import IReplayAnalyzer, IReplaySource, ReplayAnalysis, ReplayEvent
from src.domain.history.interfaces import IHistoryManager
from src.domain.checkpoint.interfaces import ICheckpointManager
from src.infrastructure.replay.config_service import ReplayConfigService
from src.presentation.api.cache.cache_manager import CacheManager
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ReplayAnalyzer(IReplayAnalyzer):
    """回放分析器实现"""
    
    def __init__(
        self,
        history_manager: IHistoryManager,
        checkpoint_manager: ICheckpointManager,
        config_service: ReplayConfigService,
        cache_manager: Optional[CacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化分析器
        
        Args:
            history_manager: 历史管理器
            checkpoint_manager: 检查点管理器
            config_service: 配置服务
            cache_manager: 缓存管理器
            performance_monitor: 性能监控器
        """
        self.history_manager = history_manager
        self.checkpoint_manager = checkpoint_manager
        self.config_service = config_service
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        
        logger.info("回放分析器初始化完成")
    
    async def analyze_session(self, session_id: str) -> ReplayAnalysis:
        """分析会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            ReplayAnalysis: 分析结果
        """
        operation_id = self.monitor.start_operation("analyze_session")
        
        try:
            # 检查缓存
            if self.cache:
                cache_key = f"session_analysis:{session_id}"
                cached_analysis = await self.cache.get(cache_key)
                if cached_analysis:
                    self.monitor.end_operation(
                        operation_id, "analyze_session", True,
                        {"cache_hit": True, "session_id": session_id}
                    )
                    return self._deserialize_analysis(cached_analysis)
            
            # 获取配置
            analyzer_config = self.config_service.get_analyzer_config()
            cache_ttl = analyzer_config["cache_ttl"]
            
            # 收集基础数据
            basic_stats = await self._collect_basic_statistics(session_id)
            performance_metrics = await self._analyze_performance(session_id)
            cost_analysis = await self._analyze_costs(session_id)
            timeline = await self._build_timeline(session_id)
            
            # 生成建议
            recommendations = await self._generate_recommendations_from_data(
                session_id, basic_stats, performance_metrics, cost_analysis
            )
            
            # 构建分析结果
            analysis = ReplayAnalysis(
                session_id=session_id,
                total_events=basic_stats["total_events"],
                event_types=basic_stats["event_types"],
                duration_seconds=basic_stats["duration_seconds"],
                tool_calls=basic_stats["tool_calls"],
                llm_calls=basic_stats["llm_calls"],
                errors=basic_stats["errors"],
                warnings=basic_stats["warnings"],
                performance_metrics=performance_metrics,
                cost_analysis=cost_analysis,
                recommendations=recommendations,
                timeline=timeline
            )
            
            # 缓存结果
            if self.cache:
                cache_key = f"session_analysis:{session_id}"
                await self.cache.set(cache_key, self._serialize_analysis(analysis), ttl=cache_ttl)
            
            self.monitor.end_operation(
                operation_id, "analyze_session", True,
                {"session_id": session_id, "total_events": analysis.total_events}
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析会话失败: {e}")
            self.monitor.end_operation(
                operation_id, "analyze_session", False,
                {"error": str(e), "session_id": session_id}
            )
            raise
    
    async def analyze_replay(self, replay_id: str) -> ReplayAnalysis:
        """分析回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            ReplayAnalysis: 分析结果
        """
        # 这里可以添加特定的回放分析逻辑
        # 目前复用会话分析逻辑
        # 在实际实现中，可能需要从回放会话中获取原始会话ID
        
        # 暂时返回一个基于回放ID的分析
        return await self._analyze_replay_specific(replay_id)
    
    async def get_analysis_history(self, session_id: str) -> List[ReplayAnalysis]:
        """获取分析历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[ReplayAnalysis]: 分析历史列表
        """
        # 从缓存获取历史分析
        history = []
        
        if self.cache:
            # 获取配置
            analyzer_config = self.config_service.get_analyzer_config()
            max_history = analyzer_config["max_analysis_history"]
            
            # 查找相关的分析缓存
            cache_pattern = f"session_analysis:{session_id}:*"
            # 这里需要实现缓存模式匹配，简化实现
            
            # 模拟历史数据
            for i in range(min(5, max_history)):
                cache_key = f"session_analysis:{session_id}:history_{i}"
                cached_analysis = await self.cache.get(cache_key)
                if cached_analysis:
                    history.append(self._deserialize_analysis(cached_analysis))
        
        return history
    
    async def generate_recommendations(self, analysis: ReplayAnalysis) -> List[str]:
        """生成优化建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 基于错误数量的建议
        if analysis.errors > 0:
            recommendations.append(f"发现 {analysis.errors} 个错误，建议检查错误日志并修复相关问题")
        
        # 基于警告数量的建议
        if analysis.warnings > 5:
            recommendations.append(f"警告数量较多 ({analysis.warnings})，建议优化代码质量")
        
        # 基于工具调用的建议
        if analysis.tool_calls > 50:
            recommendations.append("工具调用次数较多，建议检查是否有重复或可优化的调用")
        
        # 基于LLM调用的建议
        if analysis.llm_calls > 20:
            recommendations.append("LLM调用次数较多，建议考虑缓存结果或优化提示词")
        
        # 基于性能的建议
        avg_response_time = analysis.performance_metrics.get("avg_response_time", 0)
        if avg_response_time > 5.0:
            recommendations.append("平均响应时间较长，建议优化性能瓶颈")
        
        # 基于成本的建议
        total_cost = analysis.cost_analysis.get("total_cost", 0)
        if total_cost > 10.0:
            recommendations.append("成本较高，建议优化提示词长度或使用更经济的模型")
        
        # 基于事件分布的建议
        if analysis.event_types.get("error", 0) > analysis.total_events * 0.1:
            recommendations.append("错误率较高，建议改进错误处理机制")
        
        if not recommendations:
            recommendations.append("会话运行良好，无明显优化建议")
        
        return recommendations
    
    async def _collect_basic_statistics(self, session_id: str) -> Dict[str, Any]:
        """收集基础统计信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 基础统计信息
        """
        # 从历史管理器获取统计信息
        token_stats = self.history_manager.get_token_statistics(session_id)
        cost_stats = self.history_manager.get_cost_statistics(session_id)
        llm_stats = self.history_manager.get_llm_statistics(session_id)
        
        # 查询所有记录以计算详细统计
        from src.domain.history.models import HistoryQuery
        query = HistoryQuery(session_id=session_id)
        result = self.history_manager.query_history(query)
        
        # 统计事件类型
        event_types = {}
        tool_calls = 0
        llm_calls = 0
        errors = 0
        warnings = 0
        
        start_time = None
        end_time = None
        
        for record in result.records:
            record_type = record.record_type
            event_types[record_type] = event_types.get(record_type, 0) + 1
            
            if record_type == "tool_call":
                tool_calls += 1
            elif record_type == "llm_request":
                llm_calls += 1
            elif record_type == "error":
                errors += 1
            elif record_type == "warning":
                warnings += 1
            
            # 记录时间范围
            if start_time is None or record.timestamp < start_time:
                start_time = record.timestamp
            if end_time is None or record.timestamp > end_time:
                end_time = record.timestamp
        
        # 计算持续时间
        duration_seconds = 0
        if start_time and end_time:
            duration_seconds = (end_time - start_time).total_seconds()
        
        return {
            "total_events": len(result.records),
            "event_types": event_types,
            "duration_seconds": duration_seconds,
            "tool_calls": tool_calls,
            "llm_calls": llm_calls,
            "errors": errors,
            "warnings": warnings,
            "token_stats": token_stats,
            "cost_stats": cost_stats,
            "llm_stats": llm_stats
        }
    
    async def _analyze_performance(self, session_id: str) -> Dict[str, Any]:
        """分析性能指标
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 性能指标
        """
        # 获取配置
        analyzer_config = self.config_service.get_analyzer_config()
        
        if not analyzer_config["enable_performance_analysis"]:
            return {}
        
        # 从历史记录中提取性能数据
        performance_metrics = {
            "avg_response_time": 0.0,
            "max_response_time": 0.0,
            "min_response_time": float('inf'),
            "total_response_time": 0.0,
            "response_count": 0,
            "throughput": 0.0  # 事件/秒
        }
        
        try:
            from src.domain.history.models import HistoryQuery
            query = HistoryQuery(session_id=session_id)
            result = self.history_manager.query_history(query)
            
            response_times = []
            
            for record in result.records:
                # 从元数据中提取响应时间
                if hasattr(record, 'metadata') and record.metadata:
                    response_time = record.metadata.get('response_time')
                    if response_time is not None:
                        response_times.append(response_time)
            
            if response_times:
                performance_metrics["avg_response_time"] = sum(response_times) / len(response_times)
                performance_metrics["max_response_time"] = max(response_times)
                performance_metrics["min_response_time"] = min(response_times)
                performance_metrics["total_response_time"] = sum(response_times)
                performance_metrics["response_count"] = len(response_times)
            
            # 计算吞吐量
            if performance_metrics["duration_seconds"] > 0:
                performance_metrics["throughput"] = len(result.records) / performance_metrics["duration_seconds"]
            
            # 修正最小值
            if performance_metrics["min_response_time"] == float('inf'):
                performance_metrics["min_response_time"] = 0.0
                
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
        
        return performance_metrics
    
    async def _analyze_costs(self, session_id: str) -> Dict[str, Any]:
        """分析成本
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 成本分析
        """
        # 获取配置
        analyzer_config = self.config_service.get_analyzer_config()
        
        if not analyzer_config["enable_cost_analysis"]:
            return {}
        
        try:
            cost_stats = self.history_manager.get_cost_statistics(session_id)
            token_stats = self.history_manager.get_token_statistics(session_id)
            
            cost_analysis = {
                "total_cost": cost_stats.get("total_cost", 0.0),
                "prompt_cost": cost_stats.get("prompt_cost", 0.0),
                "completion_cost": cost_stats.get("completion_cost", 0.0),
                "currency": cost_stats.get("currency", "USD"),
                "total_tokens": token_stats.get("total_tokens", 0),
                "prompt_tokens": token_stats.get("prompt_tokens", 0),
                "completion_tokens": token_stats.get("completion_tokens", 0),
                "cost_per_token": 0.0,
                "models_used": cost_stats.get("models_used", [])
            }
            
            # 计算每token成本
            if cost_analysis["total_tokens"] > 0:
                cost_analysis["cost_per_token"] = cost_analysis["total_cost"] / cost_analysis["total_tokens"]
            
            return cost_analysis
            
        except Exception as e:
            logger.error(f"成本分析失败: {e}")
            return {}
    
    async def _build_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """构建时间线
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 时间线
        """
        timeline = []
        
        try:
            from src.domain.history.models import HistoryQuery
            query = HistoryQuery(session_id=session_id, limit=50)  # 限制时间线长度
            result = self.history_manager.query_history(query)
            
            for record in result.records:
                timeline.append({
                    "timestamp": record.timestamp.isoformat(),
                    "type": record.record_type,
                    "summary": self._get_record_summary(record)
                })
            
            # 按时间排序
            timeline.sort(key=lambda x: x["timestamp"])
            
        except Exception as e:
            logger.error(f"构建时间线失败: {e}")
        
        return timeline
    
    def _get_record_summary(self, record) -> str:
        """获取记录摘要
        
        Args:
            record: 历史记录
            
        Returns:
            str: 摘要
        """
        if record.record_type == "message":
            content = getattr(record, 'content', '')
            return f"消息: {content[:50]}..."
        elif record.record_type == "tool_call":
            tool_name = getattr(record, 'tool_name', 'Unknown')
            return f"工具调用: {tool_name}"
        elif record.record_type == "llm_request":
            model = getattr(record, 'model', 'Unknown')
            return f"LLM请求: {model}"
        elif record.record_type == "error":
            error_type = getattr(record, 'error_type', 'Unknown')
            return f"错误: {error_type}"
        else:
            return f"{record.record_type}: {record.record_id}"
    
    async def _generate_recommendations_from_data(
        self,
        session_id: str,
        basic_stats: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        cost_analysis: Dict[str, Any]
    ) -> List[str]:
        """基于数据生成建议
        
        Args:
            session_id: 会话ID
            basic_stats: 基础统计
            performance_metrics: 性能指标
            cost_analysis: 成本分析
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 基于基础统计的建议
        if basic_stats["errors"] > 0:
            recommendations.append(f"发现 {basic_stats['errors']} 个错误，建议检查错误日志")
        
        if basic_stats["warnings"] > 5:
            recommendations.append("警告数量较多，建议优化代码质量")
        
        # 基于性能的建议
        avg_response_time = performance_metrics.get("avg_response_time", 0)
        if avg_response_time > 5.0:
            recommendations.append("平均响应时间较长，建议优化性能")
        
        # 基于成本的建议
        total_cost = cost_analysis.get("total_cost", 0)
        if total_cost > 10.0:
            recommendations.append("成本较高，建议优化提示词或使用更经济的模型")
        
        return recommendations
    
    async def _analyze_replay_specific(self, replay_id: str) -> ReplayAnalysis:
        """分析特定回放
        
        Args:
            replay_id: 回放ID
            
        Returns:
            ReplayAnalysis: 分析结果
        """
        # 这里可以实现特定的回放分析逻辑
        # 目前返回一个模拟的分析结果
        
        return ReplayAnalysis(
            session_id=f"replay_{replay_id}",
            total_events=0,
            event_types={},
            duration_seconds=0.0,
            tool_calls=0,
            llm_calls=0,
            errors=0,
            warnings=0,
            performance_metrics={},
            cost_analysis={},
            recommendations=["回放分析功能待实现"],
            timeline=[]
        )
    
    def _serialize_analysis(self, analysis: ReplayAnalysis) -> Dict[str, Any]:
        """序列化分析结果
        
        Args:
            analysis: 分析结果
            
        Returns:
            Dict[str, Any]: 序列化后的数据
        """
        return {
            "session_id": analysis.session_id,
            "total_events": analysis.total_events,
            "event_types": analysis.event_types,
            "duration_seconds": analysis.duration_seconds,
            "tool_calls": analysis.tool_calls,
            "llm_calls": analysis.llm_calls,
            "errors": analysis.errors,
            "warnings": analysis.warnings,
            "performance_metrics": analysis.performance_metrics,
            "cost_analysis": analysis.cost_analysis,
            "recommendations": analysis.recommendations,
            "timeline": analysis.timeline
        }
    
    def _deserialize_analysis(self, data: Dict[str, Any]) -> ReplayAnalysis:
        """反序列化分析结果
        
        Args:
            data: 序列化的数据
            
        Returns:
            ReplayAnalysis: 分析结果
        """
        return ReplayAnalysis(
            session_id=data["session_id"],
            total_events=data["total_events"],
            event_types=data["event_types"],
            duration_seconds=data["duration_seconds"],
            tool_calls=data["tool_calls"],
            llm_calls=data["llm_calls"],
            errors=data["errors"],
            warnings=data["warnings"],
            performance_metrics=data["performance_metrics"],
            cost_analysis=data["cost_analysis"],
            recommendations=data["recommendations"],
            timeline=data["timeline"]
        )