"""存储指标收集器

提供专门的存储操作指标收集功能。
"""

import threading
import time
from collections import defaultdict
from typing import Dict, Any, List


class StorageMetrics:
    """专门的存储指标收集器
    
    收集和管理存储操作的性能指标。
    """
    
    def __init__(self):
        """初始化指标收集器"""
        self._operation_counts = defaultdict(int)
        self._operation_times = defaultdict(list)
        self._error_counts = defaultdict(int)
        self._lock = threading.Lock()
        self._start_time = time.time()
    
    def record_operation(self, operation: str, duration: float, success: bool) -> None:
        """记录操作指标
        
        Args:
            operation: 操作名称
            duration: 操作耗时（秒）
            success: 是否成功
        """
        with self._lock:
            self._operation_counts[operation] += 1
            self._operation_times[operation].append(duration)
            if not success:
                self._error_counts[operation] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据
        
        Returns:
            指标数据字典
        """
        with self._lock:
            current_time = time.time()
            uptime = current_time - self._start_time
            
            return {
                "uptime_seconds": uptime,
                "operation_counts": dict(self._operation_counts),
                "average_times": {
                    op: sum(times) / len(times) if times else 0
                    for op, times in self._operation_times.items()
                },
                "min_times": {
                    op: min(times) if times else 0
                    for op, times in self._operation_times.items()
                },
                "max_times": {
                    op: max(times) if times else 0
                    for op, times in self._operation_times.items()
                },
                "error_rates": {
                    op: self._error_counts[op] / self._operation_counts[op] if self._operation_counts[op] > 0 else 0
                    for op in self._operation_counts.keys()
                },
                "total_operations": sum(self._operation_counts.values()),
                "total_errors": sum(self._error_counts.values())
            }
    
    def get_operation_metrics(self, operation: str) -> Dict[str, Any]:
        """获取特定操作的指标
        
        Args:
            operation: 操作名称
            
        Returns:
            操作指标数据
        """
        with self._lock:
            count = self._operation_counts[operation]
            times = self._operation_times[operation]
            errors = self._error_counts[operation]
            
            return {
                "operation": operation,
                "count": count,
                "errors": errors,
                "success_rate": (count - errors) / count if count > 0 else 0,
                "average_time": sum(times) / len(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "recent_times": times[-10:] if times else []  # 最近10次操作时间
            }
    
    def reset_metrics(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._operation_counts.clear()
            self._operation_times.clear()
            self._error_counts.clear()
            self._start_time = time.time()
    
    def reset_operation_metrics(self, operation: str) -> None:
        """重置特定操作的指标
        
        Args:
            operation: 操作名称
        """
        with self._lock:
            if operation in self._operation_counts:
                del self._operation_counts[operation]
            if operation in self._operation_times:
                del self._operation_times[operation]
            if operation in self._error_counts:
                del self._error_counts[operation]


class MetricsContext:
    """指标上下文管理器
    
    用于自动记录操作指标。
    """
    
    def __init__(self, metrics: StorageMetrics, operation: str):
        """初始化指标上下文
        
        Args:
            metrics: 指标收集器
            operation: 操作名称
        """
        self._metrics = metrics
        self._operation = operation
        self._start_time = None
        self._success = False
    
    def __enter__(self):
        """进入上下文"""
        self._start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self._start_time is not None:
            duration = time.time() - self._start_time
            self._success = exc_type is None
            self._metrics.record_operation(self._operation, duration, self._success)
    
    def mark_success(self) -> None:
        """标记操作成功"""
        self._success = True
    
    def mark_failure(self) -> None:
        """标记操作失败"""
        self._success = False