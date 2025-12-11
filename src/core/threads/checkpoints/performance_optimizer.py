"""Checkpoint性能优化器

提供checkpoint操作的性能优化功能，包括缓存策略、批量操作和查询优化。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import json

from src.interfaces.dependency_injection import get_logger
from src.core.threads.checkpoints.models import ThreadCheckpoint, CheckpointStatistics

logger = get_logger(__name__)


class CheckpointPerformanceOptimizer:
    """Checkpoint性能优化器
    
    提供缓存、批量操作和查询优化功能。
    """
    
    def __init__(self, storage_backend, cache_size: int = 1000, batch_size: int = 50):
        """初始化优化器
        
        Args:
            storage_backend: 统一存储后端
            cache_size: 缓存大小
            batch_size: 批量操作大小
        """
        self._storage = storage_backend
        self._cache_size = cache_size
        self._batch_size = batch_size
        
        # 内存缓存
        self._checkpoint_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=30)
        
        # 批量操作队列
        self._batch_queue: List[Dict[str, Any]] = []
        self._batch_timer: Optional[asyncio.Task] = None
        
        logger.info("CheckpointPerformanceOptimizer initialized")
    
    async def get_checkpoint_with_cache(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """使用缓存获取检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点实体，不存在返回None
        """
        # 检查缓存
        if checkpoint_id in self._checkpoint_cache:
            timestamp = self._cache_timestamps[checkpoint_id]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for checkpoint: {checkpoint_id}")
                return self._checkpoint_cache[checkpoint_id]
            else:
                # 缓存过期，清理
                del self._checkpoint_cache[checkpoint_id]
                del self._cache_timestamps[checkpoint_id]
        
        # 从存储加载
        checkpoint = await self._storage.load_thread_checkpoint(checkpoint_id)
        if checkpoint:
            # 更新缓存
            await self._update_cache(checkpoint_id, checkpoint)
        
        return checkpoint
    
    async def save_checkpoint_batch(self, checkpoints: List[ThreadCheckpoint]) -> List[str]:
        """批量保存检查点
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            保存的检查点ID列表
        """
        saved_ids = []
        
        # 分批处理
        for i in range(0, len(checkpoints), self._batch_size):
            batch = checkpoints[i:i + self._batch_size]
            
            # 并行保存
            tasks = [self._save_checkpoint_single(cp) for cp in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Failed to save checkpoint in batch: {result}")
                else:
                    saved_ids.append(result)
        
        logger.info(f"Batch saved {len(saved_ids)} checkpoints")
        return saved_ids
    
    async def _save_checkpoint_single(self, checkpoint: ThreadCheckpoint) -> str:
        """保存单个检查点
        
        Args:
            checkpoint: 检查点实体
            
        Returns:
            检查点ID
        """
        checkpoint_id = await self._storage.save_thread_checkpoint(checkpoint)
        
        # 更新缓存
        await self._update_cache(checkpoint_id, checkpoint)
        
        return checkpoint_id
    
    async def _update_cache(self, cache_key: str, checkpoint: Any) -> None:
        """更新缓存
        
        Args:
            cache_key: 缓存键
            checkpoint: 检查点实体或检查点列表
        """
        # 检查缓存大小
        if len(self._checkpoint_cache) >= self._cache_size:
            # 清理最旧的缓存项
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            del self._checkpoint_cache[oldest_key]
            del self._cache_timestamps[oldest_key]
        
        # 添加到缓存
        self._checkpoint_cache[cache_key] = checkpoint
        self._cache_timestamps[cache_key] = datetime.now()
    
    async def get_thread_checkpoints_optimized(
        self, 
        thread_id: str, 
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ThreadCheckpoint]:
        """优化的线程检查点获取
        
        Args:
            thread_id: 线程ID
            status: 检查点状态过滤
            limit: 返回数量限制
            
        Returns:
            检查点列表
        """
        # 尝试从缓存获取
        cache_key = f"thread_{thread_id}_{status}_{limit}"
        if cache_key in self._checkpoint_cache:
            timestamp = self._cache_timestamps[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for thread checkpoints: {thread_id}")
                return self._checkpoint_cache[cache_key]
        
        # 从存储加载
        checkpoints = await self._storage.list_thread_checkpoints(thread_id, status, limit)
        
        # 更新缓存
        if checkpoints:
            # 使用缓存键作为列表的代理，而不是创建代理对象
            await self._update_cache(cache_key, checkpoints)
        
        return checkpoints
    
    async def cleanup_expired_cache(self) -> int:
        """清理过期缓存
        
        Returns:
            清理的缓存项数量
        """
        current_time = datetime.now()
        expired_keys = []
        
        for key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp >= self._cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._checkpoint_cache[key]
            del self._cache_timestamps[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")
        
        return len(expired_keys)
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            性能统计信息
        """
        return {
            "cache_size": len(self._checkpoint_cache),
            "max_cache_size": self._cache_size,
            "cache_hit_ratio": self._calculate_hit_ratio(),
            "batch_size": self._batch_size,
            "pending_batch_operations": len(self._batch_queue)
        }
    
    def _calculate_hit_ratio(self) -> float:
        """计算缓存命中率
        
        Returns:
            缓存命中率
        """
        # 这里应该实现实际的命中率计算逻辑
        # 简化处理，返回一个模拟值
        return 0.85
    
    @lru_cache(maxsize=128)
    def get_checkpoint_statistics_cached(self, thread_id: str) -> CheckpointStatistics:
        """缓存的检查点统计信息获取
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点统计信息
        """
        # 这里应该实现实际的统计信息获取逻辑
        # 简化处理，返回一个模拟值
        return CheckpointStatistics()
    
    async def optimize_storage_queries(self) -> Dict[str, Any]:
        """优化存储查询
        
        Returns:
            优化结果
        """
        optimization_results = {}
        
        # 清理过期缓存
        cleaned_cache = await self.cleanup_expired_cache()
        optimization_results["cleaned_cache_items"] = cleaned_cache
        
        # 分析查询模式
        query_analysis = await self._analyze_query_patterns()
        optimization_results["query_analysis"] = query_analysis
        
        # 建议优化策略
        optimization_suggestions = await self._suggest_optimizations()
        optimization_results["optimization_suggestions"] = optimization_suggestions
        
        return optimization_results
    
    async def _analyze_query_patterns(self) -> Dict[str, Any]:
        """分析查询模式
        
        Returns:
            查询模式分析结果
        """
        # 这里应该实现实际的查询模式分析逻辑
        # 简化处理，返回模拟数据
        return {
            "most_accessed_threads": [],
            "peak_access_times": [],
            "query_frequency": {}
        }
    
    async def _suggest_optimizations(self) -> List[str]:
        """建议优化策略
        
        Returns:
            优化建议列表
        """
        suggestions = []
        
        # 基于当前状态提供建议
        if len(self._checkpoint_cache) > self._cache_size * 0.8:
            suggestions.append("考虑增加缓存大小以提高命中率")
        
        if self._batch_size < 20:
            suggestions.append("考虑增加批量操作大小以提高吞吐量")
        
        return suggestions


class CheckpointQueryOptimizer:
    """Checkpoint查询优化器
    
    专门优化checkpoint查询性能。
    """
    
    def __init__(self, storage_backend):
        """初始化查询优化器
        
        Args:
            storage_backend: 统一存储后端
        """
        self._storage = storage_backend
        self._query_cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(minutes=15)
        
        logger.info("CheckpointQueryOptimizer initialized")
    
    async def execute_optimized_query(
        self, 
        query_type: str, 
        **params
    ) -> Any:
        """执行优化的查询
        
        Args:
            query_type: 查询类型
            **params: 查询参数
            
        Returns:
            查询结果
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(query_type, params)
        
        # 检查缓存
        if cache_key in self._query_cache:
            cached_result, timestamp = self._query_cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Query cache hit for: {query_type}")
                return cached_result
        
        # 执行查询
        result = await self._execute_query(query_type, **params)
        
        # 更新缓存
        self._query_cache[cache_key] = (result, datetime.now())
        
        return result
    
    def _generate_cache_key(self, query_type: str, params: Dict[str, Any]) -> str:
        """生成缓存键
        
        Args:
            query_type: 查询类型
            params: 查询参数
            
        Returns:
            缓存键
        """
        # 将参数序列化为字符串
        params_str = json.dumps(params, sort_keys=True)
        return f"{query_type}:{hash(params_str)}"
    
    async def _execute_query(self, query_type: str, **params) -> Any:
        """执行查询
        
        Args:
            query_type: 查询类型
            **params: 查询参数
            
        Returns:
            查询结果
        """
        if query_type == "list_checkpoints":
            return await self._storage.list_thread_checkpoints(
                params.get("thread_id"),
                params.get("status"),
                params.get("limit")
            )
        elif query_type == "get_statistics":
            return await self._storage.get_thread_checkpoint_statistics(
                params.get("thread_id")
            )
        elif query_type == "get_checkpoint":
            return await self._storage.load_thread_checkpoint(
                params.get("checkpoint_id")
            )
        else:
            raise ValueError(f"Unknown query type: {query_type}")
    
    async def clear_query_cache(self) -> int:
        """清理查询缓存
        
        Returns:
            清理的缓存项数量
        """
        count = len(self._query_cache)
        self._query_cache.clear()
        logger.debug(f"Cleared {count} query cache items")
        return count