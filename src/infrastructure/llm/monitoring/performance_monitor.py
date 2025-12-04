"""性能监控器基础设施模块

提供统一的性能监控和指标收集功能。
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from .stats_collector import StatsCollector, MetricType, TimerContext, AsyncTimerContext


@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    
    # 请求统计
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # 响应时间统计
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    # 错误统计
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    rate_limit_rate: float = 0.0
    
    # 吞吐量统计
    requests_per_second: float = 0.0
    
    # 资源使用统计
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    # 时间戳
    last_updated: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0,
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "p50_response_time": self.p50_response_time,
            "p95_response_time": self.p95_response_time,
            "p99_response_time": self.p99_response_time,
            "error_rate": self.error_rate,
            "timeout_rate": self.timeout_rate,
            "rate_limit_rate": self.rate_limit_rate,
            "requests_per_second": self.requests_per_second,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "last_updated": self.last_updated,
        }


class PerformanceMonitor:
    """性能监控器
    
    提供统一的性能监控和指标收集功能。
    """
    
    def __init__(self, stats_collector: Optional[StatsCollector] = None):
        """
        初始化性能监控器
        
        Args:
            stats_collector: 统计收集器
        """
        self.stats = stats_collector or StatsCollector()
        self._response_times: List[float] = []
        self._request_timestamps: List[float] = []
        self._lock = threading.RLock()
        self._max_samples = 10000
        
        # 创建默认的直方图桶
        self.stats.create_histogram("response_time_histogram", [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0])
    
    def record_request_start(self, request_id: Optional[str] = None) -> str:
        """
        记录请求开始
        
        Args:
            request_id: 请求ID（可选）
            
        Returns:
            请求ID
        """
        import uuid
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        with self._lock:
            self._request_timestamps.append(time.time())
            self.stats.increment("total_requests")
        
        return request_id
    
    def record_request_success(
        self, 
        request_id: str, 
        response_time: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录请求成功
        
        Args:
            request_id: 请求ID
            response_time: 响应时间（秒）
            labels: 标签
        """
        with self._lock:
            self.stats.increment("successful_requests", labels=labels)
            self.stats.timing("response_time", response_time, labels)
            self.stats.observe_histogram("response_time_histogram", response_time)
            
            # 记录响应时间用于计算百分位数
            self._response_times.append(response_time)
            if len(self._response_times) > self._max_samples:
                self._response_times = self._response_times[-self._max_samples:]
    
    def record_request_error(
        self, 
        request_id: str, 
        error: Exception,
        response_time: Optional[float] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录请求错误
        
        Args:
            request_id: 请求ID
            error: 错误对象
            response_time: 响应时间（秒）
            labels: 标签
        """
        error_type = type(error).__name__
        error_labels = {**(labels or {}), "error_type": error_type}
        
        with self._lock:
            self.stats.increment("failed_requests", labels=error_labels)
            self.stats.increment(f"error_{error_type.lower()}", labels=labels)
            
            if response_time is not None:
                self.stats.timing("error_response_time", response_time, labels=error_labels)
            
            # 特殊错误类型统计
            if "timeout" in str(error).lower():
                self.stats.increment("timeout_errors", labels=labels)
            elif "rate limit" in str(error).lower():
                self.stats.increment("rate_limit_errors", labels=labels)
    
    def record_request_timeout(
        self, 
        request_id: str, 
        timeout_duration: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录请求超时
        
        Args:
            request_id: 请求ID
            timeout_duration: 超时时长（秒）
            labels: 标签
        """
        timeout_labels = {**(labels or {}), "timeout_type": "request_timeout"}
        
        with self._lock:
            self.stats.increment("timeout_errors", labels=timeout_labels)
            self.stats.timing("timeout_duration", timeout_duration, labels=timeout_labels)
    
    def record_rate_limit(
        self, 
        request_id: str,
        retry_after: Optional[float] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录速率限制
        
        Args:
            request_id: 请求ID
            retry_after: 重试等待时间（秒）
            labels: 标签
        """
        rate_limit_labels = {**(labels or {}), "limit_type": "rate_limit"}
        
        with self._lock:
            self.stats.increment("rate_limit_errors", labels=rate_limit_labels)
            if retry_after is not None:
                self.stats.timing("retry_after", retry_after, labels=rate_limit_labels)
    
    def get_performance_metrics(self, window_seconds: int = 60) -> PerformanceMetrics:
        """
        获取性能指标
        
        Args:
            window_seconds: 时间窗口（秒）
            
        Returns:
            性能指标对象
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - window_seconds
            
            # 过滤时间窗口内的请求
            recent_requests = [
                timestamp for timestamp in self._request_timestamps
                if timestamp >= cutoff_time
            ]
            
            # 基础统计
            total_requests = self.stats.get_counter("total_requests")
            successful_requests = self.stats.get_counter("successful_requests")
            failed_requests = self.stats.get_counter("failed_requests")
            
            # 响应时间统计
            response_time_stats = self.stats.get_timer_stats("response_time")
            avg_response_time = response_time_stats["mean"]
            min_response_time = response_time_stats["min"]
            max_response_time = response_time_stats["max"]
            
            # 计算百分位数
            p50, p95, p99 = self._calculate_percentiles()
            
            # 错误率
            error_rate = failed_requests / total_requests if total_requests > 0 else 0.0
            timeout_errors = self.stats.get_counter("timeout_errors")
            rate_limit_errors = self.stats.get_counter("rate_limit_errors")
            timeout_rate = timeout_errors / total_requests if total_requests > 0 else 0.0
            rate_limit_rate = rate_limit_errors / total_requests if total_requests > 0 else 0.0
            
            # 吞吐量
            requests_per_second = len(recent_requests) / window_seconds if window_seconds > 0 else 0.0
            
            # 资源使用情况
            memory_usage, cpu_usage = self._get_resource_usage()
            
            return PerformanceMetrics(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time=avg_response_time,
                min_response_time=min_response_time,
                max_response_time=max_response_time,
                p50_response_time=p50,
                p95_response_time=p95,
                p99_response_time=p99,
                error_rate=error_rate,
                timeout_rate=timeout_rate,
                rate_limit_rate=rate_limit_rate,
                requests_per_second=requests_per_second,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                last_updated=current_time,
            )
    
    def get_error_summary(self, limit: int = 10) -> Dict[str, int]:
        """
        获取错误摘要
        
        Args:
            limit: 返回的错误类型数量限制
            
        Returns:
            错误类型统计字典
        """
        all_metrics = self.stats.get_all_metrics()
        error_metrics = {}
        
        for metric_name, value in all_metrics["counters"].items():
            if metric_name.startswith("error_"):
                error_type = metric_name.replace("error_", "")
                error_metrics[error_type] = value
        
        # 按数量排序
        sorted_errors = sorted(error_metrics.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_errors[:limit])
    
    def reset_metrics(self) -> None:
        """重置所有指标"""
        with self._lock:
            self.stats.reset_all_metrics()
            self._response_times.clear()
            self._request_timestamps.clear()
    
    def create_timer_context(self, metric: str, labels: Optional[Dict[str, str]] = None) -> TimerContext:
        """
        创建计时器上下文管理器
        
        Args:
            metric: 指标名称
            labels: 标签
            
        Returns:
            计时器上下文管理器
        """
        return TimerContext(self.stats, metric, labels)
    
    def create_async_timer_context(self, metric: str, labels: Optional[Dict[str, str]] = None) -> AsyncTimerContext:
        """
        创建异步计时器上下文管理器
        
        Args:
            metric: 指标名称
            labels: 标签
            
        Returns:
            异步计时器上下文管理器
        """
        return AsyncTimerContext(self.stats, metric, labels)
    
    # === 内部方法 ===
    
    def _calculate_percentiles(self) -> tuple[float, float, float]:
        """计算响应时间百分位数"""
        if not self._response_times:
            return 0.0, 0.0, 0.0
        
        sorted_times = sorted(self._response_times)
        length = len(sorted_times)
        
        def percentile(p: float) -> float:
            index = int(p * length)
            if index >= length:
                index = length - 1
            return sorted_times[index]
        
        return percentile(0.5), percentile(0.95), percentile(0.99)
    
    def _get_resource_usage(self) -> tuple[float, float]:
        """获取资源使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent()
            return memory_usage, cpu_usage
        except ImportError:
            # 如果没有psutil，返回默认值
            return 0.0, 0.0


class PerformanceMonitorFactory:
    """性能监控器工厂"""
    
    @staticmethod
    def create_default() -> PerformanceMonitor:
        """创建默认性能监控器"""
        return PerformanceMonitor()
    
    @staticmethod
    def create_with_stats_collector(stats_collector: StatsCollector) -> PerformanceMonitor:
        """使用指定统计收集器创建性能监控器"""
        return PerformanceMonitor(stats_collector)


# === 装饰器 ===

def monitor_performance(monitor: PerformanceMonitor, metric_prefix: str = ""):
    """性能监控装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            request_id = monitor.record_request_start()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                monitor.record_request_success(request_id, response_time)
                return result
            except Exception as e:
                response_time = time.time() - start_time
                monitor.record_request_error(request_id, e, response_time)
                raise
        
        return wrapper
    return decorator


def async_monitor_performance(monitor: PerformanceMonitor, metric_prefix: str = ""):
    """异步性能监控装饰器"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            request_id = monitor.record_request_start()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                response_time = time.time() - start_time
                monitor.record_request_success(request_id, response_time)
                return result
            except Exception as e:
                response_time = time.time() - start_time
                monitor.record_request_error(request_id, e, response_time)
                raise
        
        return wrapper
    return decorator