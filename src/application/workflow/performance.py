"""工作流性能优化模块

提供工作流加载和执行的性能优化功能。
"""

import time
import functools
import threading
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import pickle
import json
from pathlib import Path

F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}

    def finish(self, success: bool = True, error: Optional[str] = None) -> None:
        """完成性能测量"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.success = success
        self.error = error


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history: int = 1000) -> None:
        """初始化性能监控器

        Args:
            max_history: 最大历史记录数
        """
        self._metrics: Dict[str, list[PerformanceMetrics]] = {}
        self._max_history = max_history
        self._lock = threading.RLock()

    def start_measurement(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetrics:
        """开始性能测量

        Args:
            operation: 操作名称
            metadata: 元数据

        Returns:
            PerformanceMetrics: 性能指标对象
        """
        with self._lock:
            if operation not in self._metrics:
                self._metrics[operation] = []
            
            metric = PerformanceMetrics(
                operation=operation,
                start_time=datetime.now(),
                metadata=metadata or {}
            )
            
            self._metrics[operation].append(metric)
            
            # 限制历史记录数量
            if len(self._metrics[operation]) > self._max_history:
                self._metrics[operation] = self._metrics[operation][-self._max_history:]
            
            return metric

    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, list[PerformanceMetrics]]:
        """获取性能指标

        Args:
            operation: 操作名称，如果为None则返回所有操作

        Returns:
            Dict[str, list[PerformanceMetrics]]: 性能指标
        """
        with self._lock:
            if operation:
                return {operation: self._metrics.get(operation, [])}
            return self._metrics.copy()

    def get_statistics(self, operation: str) -> Dict[str, Any]:
        """获取操作统计信息

        Args:
            operation: 操作名称

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            metrics = self._metrics.get(operation, [])
            if not metrics:
                return {}

            successful_metrics = [m for m in metrics if m.success and m.duration_ms is not None]
            failed_metrics = [m for m in metrics if not m.success]

            if successful_metrics:
               durations = [m.duration_ms for m in successful_metrics if m.duration_ms is not None]
               if durations:  # 确保durations列表不为空
                   stats = {
                       "total_calls": len(metrics),
                       "successful_calls": len(successful_metrics),
                       "failed_calls": len(failed_metrics),
                       "success_rate": len(successful_metrics) / len(metrics),
                       "avg_duration_ms": sum(durations) / len(durations),
                       "min_duration_ms": min(durations),
                       "max_duration_ms": max(durations),
                       "median_duration_ms": sorted(durations)[len(durations) // 2],
                       "p95_duration_ms": sorted(durations)[min(int(len(durations) * 0.95), len(durations) - 1)],
                       "p99_duration_ms": sorted(durations)[min(int(len(durations) * 0.99), len(durations) - 1)]
                   }
               else:
                   stats = {
                       "total_calls": len(metrics),
                       "successful_calls": len(successful_metrics),
                       "failed_calls": len(failed_metrics),
                       "success_rate": len(successful_metrics) / len(metrics) if len(metrics) > 0 else 0.0
                   }
            else:
                stats = {
                    "total_calls": len(metrics),
                    "successful_calls": 0,
                    "failed_calls": len(failed_metrics),
                    "success_rate": 0.0
                }

            return stats

    def clear_metrics(self, operation: Optional[str] = None) -> None:
        """清除性能指标

        Args:
            operation: 操作名称，如果为None则清除所有
        """
        with self._lock:
            if operation:
                self._metrics.pop(operation, None)
            else:
                self._metrics.clear()


def performance_monitor(monitor: PerformanceMonitor, operation: str) -> Callable[[F], F]:
    """性能监控装饰器

    Args:
        monitor: 性能监控器
        operation: 操作名称
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            metric = monitor.start_measurement(operation)
            try:
                result = func(*args, **kwargs)
                metric.finish(success=True)
                return result
            except Exception as e:
                metric.finish(success=False, error=str(e))
                raise
        return wrapper  # type: ignore
    return decorator  # type: ignore


class WorkflowCache:
    """工作流缓存"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600) -> None:
        """初始化工作流缓存

        Args:
            max_size: 最大缓存大小
            ttl_seconds: 生存时间（秒）
        """
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._access_times: Dict[str, datetime] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = threading.RLock()

    def _generate_key(self, *args: Any, **kwargs: Any) -> str:
        """生成缓存键

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            str: 缓存键
        """
        # 创建可序列化的键
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """获取缓存值

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期则返回None
        """
        key = self._generate_key(*args, **kwargs)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            # 检查是否过期
            if self._is_expired(key):
                self._remove_key(key)
                return None
            
            # 更新访问时间
            self._access_times[key] = datetime.now()
            return self._cache[key]

    def set(self, value: Any, *args: Any, **kwargs: Any) -> None:
        """设置缓存值

        Args:
            value: 缓存值
            *args: 位置参数
            **kwargs: 关键字参数
        """
        key = self._generate_key(*args, **kwargs)
        
        with self._lock:
            # 如果缓存已满，移除最少使用的项
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_lru()
            
            now = datetime.now()
            self._cache[key] = value
            self._timestamps[key] = now
            self._access_times[key] = now

    def clear(self) -> None:
        """清除所有缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_times.clear()

    def _is_expired(self, key: str) -> bool:
        """检查缓存项是否过期

        Args:
            key: 缓存键

        Returns:
            bool: 是否过期
        """
        timestamp = self._timestamps.get(key)
        if timestamp is None:
            return True
        
        return (datetime.now() - timestamp).total_seconds() > self._ttl_seconds

    def _remove_key(self, key: str) -> None:
        """移除缓存项

        Args:
            key: 缓存键
        """
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_times.pop(key, None)

    def _evict_lru(self) -> None:
        """移除最少使用的缓存项"""
        if not self._access_times:
            return
        
        # 找到最少使用的项
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self._remove_key(lru_key)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total_items = len(self._cache)
            expired_items = sum(1 for key in self._cache if self._is_expired(key))
            
            return {
                "total_items": total_items,
                "expired_items": expired_items,
                "max_size": self._max_size,
                "ttl_seconds": self._ttl_seconds,
                "utilization": total_items / self._max_size if self._max_size > 0 else 0
            }


def cached(cache: WorkflowCache) -> Callable[[F], F]:
    """缓存装饰器

    Args:
        cache: 缓存实例
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 尝试从缓存获取
            cached_result = cache.get(*args, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(result, *args, **kwargs)
            return result
        return wrapper  # type: ignore
    return decorator  # type: ignore


class ParallelExecutor:
    """并行执行器"""

    def __init__(self, max_workers: int = 4) -> None:
        """初始化并行执行器

        Args:
            max_workers: 最大工作线程数
        """
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute_parallel(
        self,
        tasks: list[Callable[[], Any]],
        timeout: Optional[float] = None
    ) -> list[Any]:
        """并行执行任务

        Args:
            tasks: 任务列表
            timeout: 超时时间

        Returns:
            list[Any]: 结果列表
        """
        futures = [self._executor.submit(task) for task in tasks]
        results = []
        
        try:
            for future in as_completed(futures, timeout=timeout):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # 记录错误但继续处理其他任务
                    results.append({"error": str(e)})
        except TimeoutError:
            # 处理超时
            for future in futures:
                future.cancel()
            raise TimeoutError(f"并行执行超时（{timeout}秒）")
        
        return results

    def shutdown(self) -> None:
        """关闭执行器"""
        self._executor.shutdown(wait=True)


class WorkflowOptimizer:
    """工作流优化器"""

    def __init__(self) -> None:
        """初始化工作流优化器"""
        self._monitor = PerformanceMonitor()
        self._config_cache = WorkflowCache(max_size=50, ttl_seconds=1800)  # 30分钟
        self._executor = ParallelExecutor(max_workers=4)

    def optimize_config_loading(self, config_path: str) -> Dict[str, Any]:
        """优化配置加载

        Args:
            config_path: 配置文件路径

        Returns:
            Dict[str, Any]: 配置数据
        """
        metric = self._monitor.start_measurement("config_loading", {"path": config_path})
        
        try:
            # 尝试从缓存获取
            cached_config = self._config_cache.get(config_path)
            if cached_config is not None:
                metric.metadata["cache_hit"] = True  # type: ignore
                metric.finish(success=True)
                return cached_config  # type: ignore
            
            # 从文件加载配置
            with open(config_path, 'r', encoding='utf-8') as f:
                import yaml
                config_data = yaml.safe_load(f)
            
            # 缓存配置
            self._config_cache.set(config_data, config_path)
            
            metric.metadata["cache_hit"] = False # type: ignore
            metric.finish(success=True)
            return config_data  # type: ignore
            
        except Exception as e:
            metric.finish(success=False, error=str(e))
            raise

    def optimize_node_execution(
        self,
        nodes: list[Callable[[], Any]],
        parallel: bool = False
    ) -> list[Any]:
        """优化节点执行

        Args:
            nodes: 节点列表
            parallel: 是否并行执行

        Returns:
            list[Any]: 执行结果
        """
        metric = self._monitor.start_measurement("node_execution", {
            "node_count": len(nodes),
            "parallel": parallel
        })
        
        try:
            if parallel and len(nodes) > 1:
                results = self._executor.execute_parallel(nodes)
            else:
                results = [node() for node in nodes]
            
            metric.finish(success=True)
            return results
            
        except Exception as e:
            metric.finish(success=False, error=str(e))
            raise

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告

        Returns:
            Dict[str, Any]: 性能报告
        """
        report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "operations": {}
        }
        
        for operation in self._monitor._metrics.keys():
            report["operations"][operation] = self._monitor.get_statistics(operation)
        
        # 添加缓存统计
        report["cache_stats"] = self._config_cache.get_stats()
        
        return report  # type: ignore

    def cleanup(self) -> None:
        """清理资源"""
        self._executor.shutdown()
        self._config_cache.clear()
        self._monitor.clear_metrics()


# 全局优化器实例
_global_optimizer: Optional[WorkflowOptimizer] = None


def get_global_optimizer() -> WorkflowOptimizer:
    """获取全局优化器

    Returns:
        WorkflowOptimizer: 全局优化器实例
    """
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = WorkflowOptimizer()
    return _global_optimizer


def optimize_workflow_loading(func: F) -> F:
    """工作流加载优化装饰器

    Args:
        func: 要优化的函数

    Returns:
        F: 优化后的函数
    """
    optimizer = get_global_optimizer()
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取配置路径
        config_path = None
        if "config_path" in kwargs:
            config_path = kwargs["config_path"]
        elif args:
            config_path = args[0]
        
        # 如果有配置路径，尝试优化加载
        if config_path:
            try:
                # 使用优化的配置加载
                config_data = optimizer.optimize_config_loading(config_path)
                # 如果返回的是配置数据，需要转换为WorkflowConfig
                if isinstance(config_data, dict):
                    from src.application.workflow.config import WorkflowConfig
                    return WorkflowConfig.from_dict(config_data)
                # 如果返回的已经是WorkflowConfig，直接返回
                return config_data
            except Exception:
                # 如果优化失败，回退到原始函数
                pass
        
        # 回退到原始函数
        return func(*args, **kwargs)
    
    return wrapper  # type: ignore