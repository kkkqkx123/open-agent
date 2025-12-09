"""存储指标收集器

提供统一的存储操作指标收集和报告功能。
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading


@dataclass
class OperationMetrics:
    """操作指标数据类"""
    operation: str
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    last_error: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count
    
    @property
    def failure_rate(self) -> float:
        """失败率"""
        if self.total_count == 0:
            return 0.0
        return self.failure_count / self.total_count


@dataclass
class TimeSeriesPoint:
    """时间序列数据点"""
    timestamp: float
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class StorageMetrics:
    """存储指标收集器
    
    收集、存储和报告存储操作的性能指标。
    """
    
    def __init__(
        self,
        max_history_size: int = 1000,
        time_series_window: int = 3600  # 1小时窗口
    ) -> None:
        """初始化指标收集器
        
        Args:
            max_history_size: 最大历史记录数量
            time_series_window: 时间序列窗口大小（秒）
        """
        self.max_history_size = max_history_size
        self.time_series_window = time_series_window
        
        # 操作指标
        self._operation_metrics: Dict[str, OperationMetrics] = {}
        
        # 时间序列数据
        self._time_series: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        
        # 实时统计
        self._realtime_stats: Dict[str, Any] = {
            "active_operations": 0,
            "total_operations": 0,
            "start_time": time.time(),
        }
        
        # 线程安全
        self._lock = threading.RLock()
    
    def start_operation(self, operation: str) -> str:
        """开始操作计时
        
        Args:
            operation: 操作名称
            
        Returns:
            操作ID
        """
        operation_id = f"{operation}_{int(time.time() * 1000000)}"
        
        with self._lock:
            self._realtime_stats["active_operations"] += 1
            self._realtime_stats["total_operations"] += 1
        
        return operation_id
    
    def record_operation(
        self,
        operation: str,
        success: bool,
        duration: float,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作指标
        
        Args:
            operation: 操作名称
            success: 是否成功
            duration: 操作持续时间（秒）
            error: 错误信息（如果有）
            metadata: 额外的元数据
        """
        current_time = time.time()
        
        with self._lock:
            # 更新操作指标
            if operation not in self._operation_metrics:
                self._operation_metrics[operation] = OperationMetrics(operation=operation)
            
            metrics = self._operation_metrics[operation]
            metrics.total_count += 1
            metrics.total_duration += duration
            
            if success:
                metrics.success_count += 1
                metrics.last_success_time = current_time
            else:
                metrics.failure_count += 1
                metrics.last_failure_time = current_time
                metrics.last_error = error
            
            # 更新持续时间统计
            metrics.min_duration = min(metrics.min_duration, duration)
            metrics.max_duration = max(metrics.max_duration, duration)
            metrics.avg_duration = metrics.total_duration / metrics.total_count
            
            # 添加时间序列点
            point = TimeSeriesPoint(
                timestamp=current_time,
                value=duration,
                metadata=metadata or {}
            )
            self._time_series[f"{operation}_duration"].append(point)
            
            # 添加成功率时间序列
            success_point = TimeSeriesPoint(
                timestamp=current_time,
                value=1.0 if success else 0.0,
                metadata={"operation": operation}
            )
            self._time_series[f"{operation}_success"].append(success_point)
            
            # 更新实时统计
            self._realtime_stats["active_operations"] = max(
                0, self._realtime_stats["active_operations"] - 1
            )
    
    def get_operation_metrics(self, operation: str) -> Optional[OperationMetrics]:
        """获取操作指标
        
        Args:
            operation: 操作名称
            
        Returns:
            操作指标，如果不存在则返回None
        """
        with self._lock:
            return self._operation_metrics.get(operation)
    
    def get_all_metrics(self) -> Dict[str, OperationMetrics]:
        """获取所有操作指标
        
        Returns:
            所有操作指标字典
        """
        with self._lock:
            return self._operation_metrics.copy()
    
    def get_time_series(
        self,
        metric_name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[TimeSeriesPoint]:
        """获取时间序列数据
        
        Args:
            metric_name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            时间序列数据点列表
        """
        current_time = time.time()
        start_time = start_time or (current_time - self.time_series_window)
        end_time = end_time or current_time
        
        with self._lock:
            points = list(self._time_series.get(metric_name, []))
            
            # 过滤时间范围
            filtered_points = [
                point for point in points
                if start_time <= point.timestamp <= end_time
            ]
            
            return filtered_points
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """获取实时统计信息
        
        Returns:
            实时统计信息字典
        """
        with self._lock:
            stats = self._realtime_stats.copy()
            stats["uptime"] = time.time() - stats["start_time"]
            return stats
    
    def get_summary_report(self) -> Dict[str, Any]:
        """获取汇总报告
        
        Returns:
            汇总报告字典
        """
        with self._lock:
            report = {
                "generated_at": time.time(),
                "realtime_stats": self.get_realtime_stats(),
                "operation_summary": {},
                "performance_summary": {
                    "total_operations": 0,
                    "overall_success_rate": 0.0,
                    "avg_duration": 0.0,
                }
            }
            
            total_ops = 0
            total_success = 0
            total_duration = 0.0
            
            for operation, metrics in self._operation_metrics.items():
                total_ops += metrics.total_count
                total_success += metrics.success_count
                total_duration += metrics.total_duration
                
                report["operation_summary"][operation] = {
                    "total_count": metrics.total_count,
                    "success_rate": metrics.success_rate,
                    "avg_duration": metrics.avg_duration,
                    "min_duration": metrics.min_duration,
                    "max_duration": metrics.max_duration,
                    "last_error": metrics.last_error,
                }
            
            if total_ops > 0:
                report["performance_summary"]["total_operations"] = total_ops
                report["performance_summary"]["overall_success_rate"] = total_success / total_ops
                report["performance_summary"]["avg_duration"] = total_duration / total_ops
            
            return report
    
    def reset_metrics(self, operation: Optional[str] = None) -> None:
        """重置指标
        
        Args:
            operation: 操作名称，None表示重置所有指标
        """
        with self._lock:
            if operation:
                self._operation_metrics.pop(operation, None)
                # 清理相关时间序列
                keys_to_remove = [
                    key for key in self._time_series.keys()
                    if key.startswith(f"{operation}_")
                ]
                for key in keys_to_remove:
                    self._time_series.pop(key, None)
            else:
                self._operation_metrics.clear()
                self._time_series.clear()
                self._realtime_stats = {
                    "active_operations": 0,
                    "total_operations": 0,
                    "start_time": time.time(),
                }
    
    def get_performance_percentiles(
        self,
        operation: str,
        percentiles: Optional[List[float]] = None
    ) -> Dict[float, float]:
        """获取性能百分位数
        
        Args:
            operation: 操作名称
            percentiles: 百分位数列表，默认为[50, 90, 95, 99]
            
        Returns:
            百分位数字典
        """
        if percentiles is None:
            percentiles = [50, 90, 95, 99]
        
        points = self.get_time_series(f"{operation}_duration")
        if not points:
            return {p: 0.0 for p in percentiles}
        
        # 提取持续时间值
        durations = [point.value for point in points]
        durations.sort()
        
        # 计算百分位数
        result = {}
        count = len(durations)
        
        for percentile in percentiles:
            index = int((percentile / 100) * count)
            if index >= count:
                index = count - 1
            result[percentile] = durations[index]
        
        return result


class MetricsCollector:
    """指标收集器上下文管理器
    
    用于自动收集操作指标的上下文管理器。
    """
    
    def __init__(
        self,
        metrics: StorageMetrics,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化指标收集器
        
        Args:
            metrics: 存储指标收集器
            operation: 操作名称
            metadata: 额外的元数据
        """
        self.metrics = metrics
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
        self.operation_id = None
    
    def __enter__(self) -> 'MetricsCollector':
        """进入上下文"""
        self.operation_id = self.metrics.start_operation(self.operation)
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文"""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            success = exc_type is None
            error = str(exc_val) if exc_val else None
            
            self.metrics.record_operation(
                operation=self.operation,
                success=success,
                duration=duration,
                error=error,
                metadata=self.metadata
            )