"""指标收集器"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from threading import Lock

from .log_level import LogLevel


class IMetricsCollector(ABC):
    """指标收集器接口"""
    
    @abstractmethod
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器
        
        Args:
            name: 指标名称
            value: 增加的值
            labels: 标签
        """
        pass
    
    @abstractmethod
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表盘值
        
        Args:
            name: 指标名称
            value: 值
            labels: 标签
        """
        pass
    
    @abstractmethod
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """观察直方图
        
        Args:
            name: 指标名称
            value: 值
            labels: 标签
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标
        
        Returns:
            指标字典
        """
        pass


class MetricsCollector(IMetricsCollector):
    """指标收集器实现"""
    
    def __init__(self) -> None:
        """初始化指标收集器"""
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器"""
        key = self._create_key(name, labels)
        
        with self._lock:
            if key in self._counters:
                self._counters[key] += value
            else:
                self._counters[key] = value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表盘值"""
        key = self._create_key(name, labels)
        
        with self._lock:
            self._gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """观察直方图"""
        key = self._create_key(name, labels)
        
        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": dict(self._histograms),
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """创建指标键
        
        Args:
            name: 指标名称
            labels: 标签
            
        Returns:
            指标键
        """
        if not labels:
            return name
        
        # 将标签按字母顺序排序以确保一致性
        sorted_labels = sorted(labels.items())
        labels_str = ",".join([f"{k}={v}" for k, v in sorted_labels])
        return f"{name}{{{labels_str}}}"
    
    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# 全局指标收集器实例
_global_metrics_collector: Optional[MetricsCollector] = None


def get_global_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器
    
    Returns:
        全局指标收集器实例
    """
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector