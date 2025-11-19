"""性能监控器"""

import threading
import time
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class OperationMetric:
    """操作指标"""
    name: str
    duration: float
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """性能统计"""
    total_operations: int = 0
    total_duration: float = 0.0
    successful_operations: int = 0
    failed_operations: int = 0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations
    
    @property
    def failure_rate(self) -> float:
        """失败率"""
        return 1.0 - self.success_rate


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        """初始化性能监控器
        
        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._stats: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self._start_times: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str) -> str:
        """开始操作计时
        
        Args:
            operation_name: 操作名称
            
        Returns:
            操作ID
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        with self._lock:
            self._start_times[operation_id] = time.time()
        return operation_id
    
    def end_operation(
        self,
        operation_id: str,
        operation_name: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """结束操作计时
        
        Args:
            operation_id: 操作ID
            operation_name: 操作名称
            success: 是否成功
            metadata: 元数据
            
        Returns:
            操作持续时间（秒）
        """
        start_time = self._start_times.pop(operation_id, None)
        if start_time is None:
            return 0.0
        
        duration = time.time() - start_time
        
        # 记录指标
        metric = OperationMetric(
            name=operation_name,
            duration=duration,
            timestamp=datetime.now(),
            success=success,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics[operation_name].append(metric)
            self._update_stats(operation_name, metric)
        
        return duration
    
    def record_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """直接记录操作指标
        
        Args:
            operation_name: 操作名称
            duration: 持续时间
            success: 是否成功
            metadata: 元数据
        """
        metric = OperationMetric(
            name=operation_name,
            duration=duration,
            timestamp=datetime.now(),
            success=success,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics[operation_name].append(metric)
            self._update_stats(operation_name, metric)
    
    def _update_stats(self, operation_name: str, metric: OperationMetric) -> None:
        """更新统计信息"""
        stats = self._stats[operation_name]
        stats.total_operations += 1
        stats.total_duration += metric.duration
        
        if metric.success:
            stats.successful_operations += 1
        else:
            stats.failed_operations += 1
        
        stats.min_duration = min(stats.min_duration, metric.duration)
        stats.max_duration = max(stats.max_duration, metric.duration)
        stats.avg_duration = stats.total_duration / stats.total_operations
    
    def get_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计
        
        Args:
            operation_name: 操作名称，如果为None则返回所有统计
            
        Returns:
            性能统计信息
        """
        with self._lock:
            if operation_name:
                stats = self._stats.get(operation_name)
                if not stats:
                    return {}
                
                return {
                    "operation": operation_name,
                    "total_operations": stats.total_operations,
                    "successful_operations": stats.successful_operations,
                    "failed_operations": stats.failed_operations,
                    "success_rate": stats.success_rate,
                    "failure_rate": stats.failure_rate,
                    "min_duration": stats.min_duration,
                    "max_duration": stats.max_duration,
                    "avg_duration": stats.avg_duration,
                    "total_duration": stats.total_duration
                }
            else:
                return {
                    name: self.get_stats(name)
                    for name in self._stats.keys()
                }
    
    def get_recent_metrics(
        self,
        operation_name: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[OperationMetric]:
        """获取最近的指标
        
        Args:
            operation_name: 操作名称
            limit: 限制数量
            since: 起始时间
            
        Returns:
            指标列表
        """
        with self._lock:
            metrics = list(self._metrics.get(operation_name, []))
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return metrics[-limit:] if limit else metrics
    
    def reset_stats(self, operation_name: Optional[str] = None) -> None:
        """重置统计信息
        
        Args:
            operation_name: 操作名称，如果为None则重置所有统计
        """
        with self._lock:
            if operation_name:
                self._metrics[operation_name].clear()
                self._stats[operation_name] = PerformanceStats()
            else:
                self._metrics.clear()
                self._stats.clear()
    
    def get_slow_operations(
        self,
        threshold: float = 1.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取慢操作
        
        Args:
            threshold: 时间阈值（秒）
            limit: 限制数量
            
        Returns:
            慢操作列表
        """
        slow_operations = []
        
        with self._lock:
            for operation_name, metrics in self._metrics.items():
                for metric in metrics:
                    if metric.duration >= threshold:
                        slow_operations.append({
                            "operation": operation_name,
                            "duration": metric.duration,
                            "timestamp": metric.timestamp.isoformat(),
                            "success": metric.success,
                            "metadata": metric.metadata
                        })
        
        # 按持续时间排序
        slow_operations.sort(key=lambda x: x["duration"], reverse=True)
        return slow_operations[:limit]
    
    def get_error_rate_trend(
        self,
        operation_name: str,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """获取错误率趋势
        
        Args:
            operation_name: 操作名称
            window_minutes: 时间窗口（分钟）
            
        Returns:
            错误率趋势信息
        """
        since = datetime.now() - timedelta(minutes=window_minutes)
        metrics = self.get_recent_metrics(operation_name, since=since)
        
        if not metrics:
            return {"error_rate": 0.0, "total_operations": 0}
        
        total = len(metrics)
        errors = sum(1 for m in metrics if not m.success)
        
        return {
            "error_rate": errors / total,
            "total_operations": total,
            "error_operations": errors,
            "window_minutes": window_minutes
        }