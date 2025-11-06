"""性能监控接口定义

定义统一的性能监控接口和数据模型。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, field
import time


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"      # 计数器
    GAUGE = "gauge"          # 仪表值
    TIMER = "timer"          # 计时器
    HISTOGRAM = "histogram"  # 直方图


@dataclass
class MetricValue:
    """指标值数据类"""
    value: Union[float, int]
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels
        }


@dataclass
class HistogramData:
    """直方图数据"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    buckets: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "count": self.count,
            "sum": self.sum,
            "min": self.min if self.min != float('inf') else 0,
            "max": self.max if self.max != float('-inf') else 0,
            "buckets": self.buckets.copy()
        }


class IPerformanceMonitor(ABC):
    """性能监控接口"""
    
    @abstractmethod
    def increment_counter(self, metric_name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器值
        
        Args:
            metric_name: 指标名称
            value: 增加的值，默认为1.0
            labels: 标签字典，用于区分不同的指标维度
        """
        pass
    
    @abstractmethod
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表值
        
        Args:
            metric_name: 指标名称
            value: 仪表值
            labels: 标签字典
        """
        pass
    
    @abstractmethod
    def record_timer(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时器值
        
        Args:
            metric_name: 指标名称
            value: 时间值（秒）
            labels: 标签字典
        """
        pass
    
    @abstractmethod
    def observe_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """观察直方图值
        
        Args:
            metric_name: 指标名称
            value: 观察值
            labels: 标签字典
        """
        pass
    
    @abstractmethod
    def get_metric(self, metric_name: str, metric_type: MetricType, labels: Optional[Dict[str, str]] = None) -> Any:
        """获取指标值
        
        Args:
            metric_name: 指标名称
            metric_type: 指标类型
            labels: 标签字典
            
        Returns:
            指标值
        """
        pass
    
    @abstractmethod
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标
        
        Returns:
            包含所有指标的字典
        """
        pass
    
    @abstractmethod
    def reset_metrics(self) -> None:
        """重置所有指标"""
        pass
    
    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告
        
        Returns:
            性能报告字典
        """
        pass