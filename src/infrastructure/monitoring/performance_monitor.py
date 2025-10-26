"""性能监控系统

提供全面的性能监控和分析功能。
"""

import time
import threading
import statistics
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager
from enum import Enum
import json


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"      # 仪表值
    HISTOGRAM = "histogram"  # 直方图
    TIMER = "timer"      # 计时器


@dataclass
class MetricValue:
    """指标值"""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels
        }


@dataclass
class Histogram:
    """直方图数据"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    buckets: Dict[str, int] = field(default_factory=dict)
    
    def observe(self, value: float) -> None:
        """观察一个值"""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        
        # 更新桶计数
        for bucket_label, bucket_value in self.buckets.items():
            if value <= float(bucket_label):
                self.buckets[bucket_label] += 1
    
    def get_average(self) -> float:
        """获取平均值"""
        return self.sum / self.count if self.count > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "count": self.count,
            "sum": self.sum,
            "min": self.min if self.min != float('inf') else 0,
            "max": self.max if self.max != float('-inf') else 0,
            "average": self.get_average(),
            "buckets": self.buckets.copy()
        }


class PerformanceMonitor:
    """性能监控器
    
    提供以下功能：
    1. 多种指标类型
    2. 实时监控
    3. 性能分析
    4. 报告生成
    """
    
    def __init__(
        self,
        max_history_size: int = 1000,
        enable_real_time_monitoring: bool = True,
        sampling_rate: float = 1.0
    ):
        """初始化性能监控器
        
        Args:
            max_history_size: 最大历史记录大小
            enable_real_time_monitoring: 是否启用实时监控
            sampling_rate: 采样率（0.0-1.0）
        """
        self._max_history_size = max_history_size
        self._enable_real_time_monitoring = enable_real_time_monitoring
        self._sampling_rate = sampling_rate
        
        # 指标存储
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, Histogram] = defaultdict(Histogram)
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        
        # 历史记录
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 监控配置
        self._monitoring_config = {
            "enabled_metrics": set(),
            "alert_thresholds": {},
            "sampling_rules": {}
        }
        
        # 性能统计
        self._monitor_stats = {
            "total_metrics": 0,
            "total_samples": 0,
            "monitoring_overhead": 0.0
        }
    
    @contextmanager
    def measure_time(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """测量执行时间的上下文管理器
        
        Args:
            metric_name: 指标名称
            labels: 标签
        """
        if not self._should_sample(metric_name):
            yield
            return
        
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.record_timer(metric_name, execution_time, labels or {})
    
    def increment_counter(self, metric_name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器
        
        Args:
            metric_name: 指标名称
            value: 增加值
            labels: 标签
        """
        if not self._should_sample(metric_name):
            return
        
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            self._counters[full_name] += value
            self._add_to_history(full_name, self._counters[full_name])
            self._monitor_stats["total_metrics"] += 1
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表值
        
        Args:
            metric_name: 指标名称
            value: 值
            labels: 标签
        """
        if not self._should_sample(metric_name):
            return
        
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            self._gauges[full_name] = value
            self._add_to_history(full_name, value)
            self._monitor_stats["total_metrics"] += 1
    
    def observe_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """观察直方图值
        
        Args:
            metric_name: 指标名称
            value: 值
            labels: 标签
        """
        if not self._should_sample(metric_name):
            return
        
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            self._histograms[full_name].observe(value)
            self._add_to_history(full_name, value)
            self._monitor_stats["total_metrics"] += 1
    
    def record_timer(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时器值
        
        Args:
            metric_name: 指标名称
            value: 时间值
            labels: 标签
        """
        if not self._should_sample(metric_name):
            return
        
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            self._timers[full_name].append(value)
            self._add_to_history(full_name, value)
            self._monitor_stats["total_metrics"] += 1
    
    def get_metric(self, metric_name: str, metric_type: MetricType, labels: Optional[Dict[str, str]] = None) -> Any:
        """获取指标值
        
        Args:
            metric_name: 指标名称
            metric_type: 指标类型
            labels: 标签
            
        Returns:
            指标值
        """
        with self._lock:
            full_name = self._get_full_metric_name(metric_name, labels)
            
            if metric_type == MetricType.COUNTER:
                return self._counters.get(full_name, 0.0)
            elif metric_type == MetricType.GAUGE:
                return self._gauges.get(full_name, 0.0)
            elif metric_type == MetricType.HISTOGRAM:
                return self._histograms.get(full_name, Histogram())
            elif metric_type == MetricType.TIMER:
                times = list(self._timers.get(full_name, []))
                if times:
                    return {
                        "count": len(times),
                        "average": statistics.mean(times),
                        "min": min(times),
                        "max": max(times),
                        "median": statistics.median(times),
                        "p95": self._percentile(times, 0.95),
                        "p99": self._percentile(times, 0.99)
                    }
                return None
            else:
                return None
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标
        
        Returns:
            所有指标的字典
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: v.to_dict() for k, v in self._histograms.items()},
                "timers": {k: self._get_timer_stats(k) for k in self._timers.keys()},
                "monitor_stats": self._monitor_stats.copy()
            }
    
    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[MetricValue]:
        """获取指标历史
        
        Args:
            metric_name: 指标名称
            limit: 返回的最大记录数
            
        Returns:
            历史记录列表
        """
        with self._lock:
            history = list(self._history.get(metric_name, []))
            return history[-limit:] if history else []
    
    def generate_report(self, time_range: Optional[float] = None) -> Dict[str, Any]:
        """生成性能报告
        
        Args:
            time_range: 时间范围（秒），None表示全部
            
        Returns:
            性能报告
        """
        current_time = time.time()
        cutoff_time = current_time - time_range if time_range else 0
        
        with self._lock:
            report = {
                "timestamp": current_time,
                "time_range": time_range,
                "summary": self._generate_summary(cutoff_time),
                "metrics": {
                    "counters": self._filter_metrics_by_time(self._counters, cutoff_time),
                    "gauges": self._filter_metrics_by_time(self._gauges, cutoff_time),
                    "histograms": {
                        k: v.to_dict() for k, v in self._histograms.items()
                    },
                    "timers": {
                        k: self._get_timer_stats(k) for k in self._timers.keys()
                    }
                },
                "monitoring_stats": self._monitor_stats.copy()
            }
            
            return report
    
    def export_metrics(self, format: str = "json") -> str:
        """导出指标数据
        
        Args:
            format: 导出格式（json, prometheus）
            
        Returns:
            导出的数据
        """
        metrics = self.get_all_metrics()
        
        if format == "json":
            return json.dumps(metrics, indent=2, default=str)
        elif format == "prometheus":
            return self._export_prometheus_format(metrics)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def reset_metrics(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._history.clear()
            self._monitor_stats = {
                "total_metrics": 0,
                "total_samples": 0,
                "monitoring_overhead": 0.0
            }
    
    def configure_monitoring(self, config: Dict[str, Any]) -> None:
        """配置监控
        
        Args:
            config: 配置字典
        """
        with self._lock:
            if "enabled_metrics" in config:
                self._monitoring_config["enabled_metrics"] = set(config["enabled_metrics"])
            
            if "alert_thresholds" in config:
                self._monitoring_config["alert_thresholds"] = config["alert_thresholds"]
            
            if "sampling_rules" in config:
                self._monitoring_config["sampling_rules"] = config["sampling_rules"]
    
    def _should_sample(self, metric_name: str) -> bool:
        """判断是否应该采样
        
        Args:
            metric_name: 指标名称
            
        Returns:
            是否应该采样
        """
        # 检查采样率
        import random
        if random.random() > self._sampling_rate:
            return False
        
        # 检查启用的指标
        if self._monitoring_config["enabled_metrics"]:
            return metric_name in self._monitoring_config["enabled_metrics"]
        
        return True
    
    def _get_full_metric_name(self, metric_name: str, labels: Optional[Dict[str, str]]) -> str:
        """获取完整的指标名称
        
        Args:
            metric_name: 指标名称
            labels: 标签
            
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
        metric_value = MetricValue(
            value=value,
            timestamp=time.time()
        )
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
            "median": statistics.median(times),
            "p95": self._percentile(times, 0.95),
            "p99": self._percentile(times, 0.99),
            "recent_average": statistics.mean(times[-10:]) if len(times) >= 10 else statistics.mean(times)
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """计算百分位数
        
        Args:
            values: 值列表
            percentile: 百分位数（0-1）
            
        Returns:
            百分位数值
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _filter_metrics_by_time(self, metrics: Dict[str, Any], cutoff_time: float) -> Dict[str, Any]:
        """按时间过滤指标
        
        Args:
            metrics: 指标字典
            cutoff_time: 截止时间
            
        Returns:
            过滤后的指标
        """
        # 简化实现，返回所有指标
        return dict(metrics)
    
    def _generate_summary(self, cutoff_time: float) -> Dict[str, Any]:
        """生成摘要
        
        Args:
            cutoff_time: 截止时间
            
        Returns:
            摘要信息
        """
        return {
            "total_metrics": self._monitor_stats["total_metrics"],
            "active_counters": len(self._counters),
            "active_gauges": len(self._gauges),
            "active_histograms": len(self._histograms),
            "active_timers": len(self._timers),
            "monitoring_overhead": self._monitor_stats["monitoring_overhead"]
        }
    
    def _export_prometheus_format(self, metrics: Dict[str, Any]) -> str:
        """导出Prometheus格式
        
        Args:
            metrics: 指标数据
            
        Returns:
            Prometheus格式字符串
        """
        lines = []
        
        # 导出计数器
        for name, value in metrics["counters"].items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # 导出仪表值
        for name, value in metrics["gauges"].items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # 导出直方图
        for name, histogram in metrics["histograms"].items():
            lines.append(f"# TYPE {name} histogram")
            lines.append(f"{name}_count {histogram['count']}")
            lines.append(f"{name}_sum {histogram['sum']}")
        
        return "\n".join(lines)


def create_performance_monitor(
    max_history_size: int = 1000,
    enable_real_time_monitoring: bool = True,
    sampling_rate: float = 1.0
) -> PerformanceMonitor:
    """创建性能监控器
    
    Args:
        max_history_size: 最大历史记录大小
        enable_real_time_monitoring: 是否启用实时监控
        sampling_rate: 采样率
        
    Returns:
        性能监控器实例
    """
    return PerformanceMonitor(
        max_history_size=max_history_size,
        enable_real_time_monitoring=enable_real_time_monitoring,
        sampling_rate=sampling_rate
    )


# 全局性能监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器
    
    Returns:
        全局性能监控器实例
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = create_performance_monitor()
    return _global_monitor