"""检查点模块

提供检查点相关的功能实现。
"""

from .performance import (
    PerformanceMonitor,
    monitor_performance,
    get_performance_metrics,
    reset_performance_metrics
)

# 如果新的性能监控系统可用，也导出适配器
try:
    from .performance_adapter import (
        CheckpointPerformanceAdapter,
        monitor_performance as new_monitor_performance,
        get_performance_metrics as new_get_performance_metrics,
        reset_performance_metrics as new_reset_performance_metrics
    )
    __all__ = [
        "PerformanceMonitor",
        "monitor_performance",
        "get_performance_metrics",
        "reset_performance_metrics",
        "CheckpointPerformanceAdapter",
        "new_monitor_performance",
        "new_get_performance_metrics",
        "new_reset_performance_metrics"
    ]
except ImportError:
    __all__ = [
        "PerformanceMonitor",
        "monitor_performance",
        "get_performance_metrics",
        "reset_performance_metrics"
    ]