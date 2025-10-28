"""容器性能监控适配器"""

import time
from typing import Type, Dict, Any

from ..monitoring.performance_monitor import PerformanceMonitor, MetricType
from ..container_interfaces import IPerformanceMonitor


class ContainerPerformanceMonitor(IPerformanceMonitor):
    """容器性能监控实现"""
    
    def __init__(self, monitor: PerformanceMonitor):
        """初始化容器性能监控
        
        Args:
            monitor: 性能监控器实例
        """
        self._monitor = monitor
    
    def record_resolution(self, service_type: Type, start_time: float, end_time: float) -> None:
        """记录服务解析
        
        Args:
            service_type: 服务类型
            start_time: 开始时间
            end_time: 结束时间
        """
        resolution_time = end_time - start_time
        self._monitor.record_timer(
            "container.service_resolution",
            resolution_time,
            {"service": service_type.__name__}
        )
    
    def record_cache_hit(self, service_type: Type) -> None:
        """记录缓存命中
        
        Args:
            service_type: 服务类型
        """
        self._monitor.increment_counter(
            "container.cache_hits",
            1.0,
            {"service": service_type.__name__}
        )
    
    def record_cache_miss(self, service_type: Type) -> None:
        """记录缓存未命中
        
        Args:
            service_type: 服务类型
        """
        self._monitor.increment_counter(
            "container.cache_misses",
            1.0,
            {"service": service_type.__name__}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        return self._monitor.get_all_metrics()