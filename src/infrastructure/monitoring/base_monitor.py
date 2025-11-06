"""性能监控抽象基类

提供统一的性能监控基类实现。
"""

import time
import threading
import statistics
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from contextlib import contextmanager

from .interfaces import IPerformanceMonitor, MetricType, MetricValue, HistogramData


class BasePerformanceMonitor(IPerformanceMonitor):
    """性能监控抽象基类"""
    
    def __init__(self, max_history_size: int = 1000):
        """初始化性能监控器
        
        Args:
            max_history_size: 最大历史记录大小
        """
        self._max_history_size = max_history_size
        
        # 指标存储
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self._histograms: Dict[str, HistogramData] = defaultdict(HistogramData)
        
        # 历史记录
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 配置
        self._config: Dict[str, Any] = {
            "enabled": True,
            "sampling_rate": 1.0
        }
    
    @contextmanager
    def measure_time(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """测量执行时间的上下文管理器
        
        Args:
            metric_name: 指标名称
            labels: 标签字典
        """
        if not self._should_sample():
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.record_timer(metric_name, execution_time, labels or {})
    
    def increment_counter(self, metric_name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器值
        
        Args:
            metric_name: 指标名称
            value: 增加的值，默认为1.0
            labels: 标签字典
        """
        if not self._should_sample():
            return
            
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            self._counters[full_name] += value
            self._add_to_history(full_name, value)
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表值
        
        Args:
            metric_name: 指标名称
            value: 仪表值
            labels: 标签字典
        """
        if not self._should_sample():
            return
            
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            self._gauges[full_name] = value
            self._add_to_history(full_name, value)
    
    def record_timer(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时器值
        
        Args:
            metric_name: 指标名称
            value: 时间值（秒）
            labels: 标签字典
        """
        if not self._should_sample():
            return
            
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            self._timers[full_name].append(value)
            self._add_to_history(full_name, value)
    
    def observe_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """观察直方图值
        
        Args:
            metric_name: 指标名称
            value: 观察值
            labels: 标签字典
        """
        if not self._should_sample():
            return
            
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            histogram = self._histograms[full_name]
            histogram.count += 1
            histogram.sum += value
            histogram.min = min(histogram.min, value)
            histogram.max = max(histogram.max, value)
            self._add_to_history(full_name, value)
    
    def get_metric(self, metric_name: str, metric_type: MetricType, labels: Optional[Dict[str, str]] = None) -> Any:
        """获取指标值
        
        Args:
            metric_name: 指标名称
            metric_type: 指标类型
            labels: 标签字典
            
        Returns:
            指标值
        """
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            
            if metric_type == MetricType.COUNTER:
                return self._counters.get(full_name, 0.0)
            elif metric_type == MetricType.GAUGE:
                return self._gauges.get(full_name, 0.0)
            elif metric_type == MetricType.TIMER:
                times = list(self._timers.get(full_name, []))
                if times:
                    return {
                        "count": len(times),
                        "average": statistics.mean(times),
                        "min": min(times),
                        "max": max(times),
                        "median": statistics.median(times) if len(times) > 0 else 0
                    }
                return None
            elif metric_type == MetricType.HISTOGRAM:
                return self._histograms.get(full_name, HistogramData())
            else:
                return None
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标
        
        Returns:
            包含所有指标的字典
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timers": {k: self._get_timer_stats(k) for k in self._timers.keys()},
                "histograms": {k: v.to_dict() for k, v in self._histograms.items()}
            }
    
    def reset_metrics(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()
            self._histograms.clear()
            self._history.clear()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告
        
        Returns:
            性能报告字典
        """
        with self._lock:
            return {
                "timestamp": time.time(),
                "metrics": self.get_all_metrics(),
                "summary": {
                    "total_counters": len(self._counters),
                    "total_gauges": len(self._gauges),
                    "total_timers": len(self._timers),
                    "total_histograms": len(self._histograms)
                }
            }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置监控器
        
        Args:
            config: 配置字典
        """
        with self._lock:
            self._config.update(config)
    
    def _should_sample(self) -> bool:
        """判断是否应该采样
        
        Returns:
            是否应该采样
        """
        if not self._config.get("enabled", True):
            return False
            
        import random
        return random.random() <= self._config.get("sampling_rate", 1.0)
    
    def _get_full_metric_name(self, metric_name: str, labels: Optional[Dict[str, str]]) -> str:
        """获取完整的指标名称
        
        Args:
            metric_name: 指标名称
            labels: 标签字典
            
        Returns:
            完整的指标名称
        """
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{metric_name}{{{label_str}}}"
        return metric_name
    
    def _add_to_history(self, metric_name: str, value: float) -> None:
        """添加到历史记录
        
        Args:
            metric_name: 指标名称
            value: 值
        """
        metric_value = MetricValue(value=value)
        self._history[metric_name].append(metric_value)
    
    def _get_timer_stats(self, metric_name: str) -> Dict[str, Any]:
        """获取计时器统计
        
        Args:
            metric_name: 指标名称
            
        Returns:
            计时器统计
        """
        times = list(self._timers.get(metric_name, []))
        if not times:
            return {}
            
        return {
            "count": len(times),
            "average": statistics.mean(times),
            "min": min(times),
            "max": max(times),
            "median": statistics.median(times) if len(times) > 0 else 0
        }