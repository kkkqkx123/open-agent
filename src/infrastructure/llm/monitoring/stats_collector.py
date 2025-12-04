"""统计收集器基础设施模块

提供统一的指标收集和管理功能。
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from collections import defaultdict, deque
import threading


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """指标数据结构"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp,
            "labels": self.labels,
            "unit": self.unit,
            "description": self.description,
        }


@dataclass
class HistogramBucket:
    """直方图桶"""
    upper_bound: float
    count: int = 0
    
    def observe(self, value: float) -> None:
        """观察值"""
        if value <= self.upper_bound:
            self.count += 1


@dataclass
class Histogram:
    """直方图指标"""
    name: str
    buckets: List[HistogramBucket]
    count: int = 0
    sum: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def observe(self, value: float) -> None:
        """观察值"""
        self.count += 1
        self.sum += value
        for bucket in self.buckets:
            bucket.observe(value)
    
    def get_buckets(self) -> List[Dict[str, Any]]:
        """获取桶数据"""
        return [
            {"upper_bound": bucket.upper_bound, "count": bucket.count}
            for bucket in self.buckets
        ]


class StatsCollector:
    """统计收集器
    
    提供统一的指标收集和管理功能。
    """
    
    def __init__(self, max_history: int = 1000):
        """
        初始化统计收集器
        
        Args:
            max_history: 最大历史记录数量
        """
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, Histogram] = {}
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._metrics_history: deque = deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._max_history = max_history
    
    # === 计数器方法 ===
    
    def increment(self, metric: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        增加计数器
        
        Args:
            metric: 指标名称
            value: 增加值
            labels: 标签
        """
        with self._lock:
            self._counters[metric] += value
            self._record_metric(metric, value, MetricType.COUNTER, labels)
    
    def decrement(self, metric: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        减少计数器
        
        Args:
            metric: 指标名称
            value: 减少值
            labels: 标签
        """
        with self._lock:
            self._counters[metric] -= value
            self._record_metric(metric, -value, MetricType.COUNTER, labels)
    
    def get_counter(self, metric: str) -> int:
        """
        获取计数器值
        
        Args:
            metric: 指标名称
            
        Returns:
            计数器值
        """
        with self._lock:
            return self._counters[metric]
    
    # === 仪表盘方法 ===
    
    def set_gauge(self, metric: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        设置仪表盘值
        
        Args:
            metric: 指标名称
            value: 值
            labels: 标签
        """
        with self._lock:
            self._gauges[metric] = value
            self._record_metric(metric, value, MetricType.GAUGE, labels)
    
    def get_gauge(self, metric: str) -> float:
        """
        获取仪表盘值
        
        Args:
            metric: 指标名称
            
        Returns:
            仪表盘值
        """
        with self._lock:
            return self._gauges[metric]
    
    # === 直方图方法 ===
    
    def create_histogram(self, metric: str, buckets: List[float], labels: Optional[Dict[str, str]] = None) -> None:
        """
        创建直方图
        
        Args:
            metric: 指标名称
            buckets: 桶边界
            labels: 标签
        """
        with self._lock:
            histogram_buckets = [HistogramBucket(upper_bound) for upper_bound in buckets]
            self._histograms[metric] = Histogram(
                name=metric,
                buckets=histogram_buckets,
                labels=labels or {}
            )
    
    def observe_histogram(self, metric: str, value: float) -> None:
        """
        观察直方图值
        
        Args:
            metric: 指标名称
            value: 观察值
        """
        with self._lock:
            if metric not in self._histograms:
                # 创建默认桶
                self.create_histogram(metric, [0.1, 0.5, 1.0, 2.5, 5.0, 10.0])
            
            self._histograms[metric].observe(value)
            self._record_metric(metric, value, MetricType.HISTOGRAM)
    
    def get_histogram(self, metric: str) -> Optional[Histogram]:
        """
        获取直方图
        
        Args:
            metric: 指标名称
            
        Returns:
            直方图对象
        """
        with self._lock:
            return self._histograms.get(metric)
    
    # === 计时器方法 ===
    
    def timing(self, metric: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        记录计时
        
        Args:
            metric: 指标名称
            value: 时间值（秒）
            labels: 标签
        """
        with self._lock:
            self._timers[metric].append(value)
            self._record_metric(metric, value, MetricType.TIMER, labels)
    
    def get_timer_stats(self, metric: str) -> Dict[str, float]:
        """
        获取计时器统计
        
        Args:
            metric: 指标名称
            
        Returns:
            统计信息字典
        """
        with self._lock:
            values = list(self._timers[metric])
            if not values:
                return {
                    "count": 0,
                    "min": 0.0,
                    "max": 0.0,
                    "mean": 0.0,
                    "sum": 0.0,
                }
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "sum": sum(values),
            }
    
    # === 通用方法 ===
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标
        
        Returns:
            所有指标的字典
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: {
                        "count": hist.count,
                        "sum": hist.sum,
                        "buckets": hist.get_buckets(),
                    }
                    for name, hist in self._histograms.items()
                },
                "timers": {
                    name: self.get_timer_stats(name)
                    for name in self._timers.keys()
                },
            }
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[Metric]:
        """
        获取指标历史
        
        Args:
            limit: 限制返回数量
            
        Returns:
            指标历史列表
        """
        with self._lock:
            history = list(self._metrics_history)
            if limit:
                history = history[-limit:]
            return history
    
    def reset_metric(self, metric: str) -> None:
        """
        重置指标
        
        Args:
            metric: 指标名称
        """
        with self._lock:
            if metric in self._counters:
                self._counters[metric] = 0
            if metric in self._gauges:
                self._gauges[metric] = 0.0
            if metric in self._histograms:
                # 重置直方图
                hist = self._histograms[metric]
                hist.count = 0
                hist.sum = 0.0
                for bucket in hist.buckets:
                    bucket.count = 0
            if metric in self._timers:
                self._timers[metric].clear()
    
    def reset_all_metrics(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._metrics_history.clear()
    
    # === 内部方法 ===
    
    def _record_metric(
        self, 
        name: str, 
        value: Union[int, float], 
        metric_type: MetricType,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录指标到历史"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=time.time(),
            labels=labels or {}
        )
        self._metrics_history.append(metric)


class StatsCollectorFactory:
    """统计收集器工厂"""
    
    @staticmethod
    def create_default() -> StatsCollector:
        """创建默认统计收集器"""
        return StatsCollector()
    
    @staticmethod
    def create_with_max_history(max_history: int) -> StatsCollector:
        """创建指定最大历史记录的统计收集器"""
        return StatsCollector(max_history)


# === 上下文管理器 ===

class TimerContext:
    """计时器上下文管理器"""
    
    def __init__(self, collector: StatsCollector, metric: str, labels: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.metric = metric
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.timing(self.metric, duration, self.labels)
        return False


class AsyncTimerContext:
    """异步计时器上下文管理器"""
    
    def __init__(self, collector: StatsCollector, metric: str, labels: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.metric = metric
        self.labels = labels
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.timing(self.metric, duration, self.labels)
        return False


def timer(collector: StatsCollector, metric: str, labels: Optional[Dict[str, str]] = None):
    """计时器装饰器工厂"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TimerContext(collector, metric, labels):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def async_timer(collector: StatsCollector, metric: str, labels: Optional[Dict[str, str]] = None):
    """异步计时器装饰器工厂"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with AsyncTimerContext(collector, metric, labels):
                return await func(*args, **kwargs)
        return wrapper
    return decorator