"""Checkpoint性能监控工具

提供性能监控和度量功能。
"""

import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._metrics: Dict[str, Dict[str, float]] = {}
    
    def record_execution_time(self, operation: str, execution_time: float) -> None:
        """记录执行时间
        
        Args:
            operation: 操作名称
            execution_time: 执行时间（秒）
        """
        if operation not in self._metrics:
            self._metrics[operation] = {
                'total_time': 0.0,
                'count': 0,
                'min_time': float('inf'),
                'max_time': 0.0
            }
        
        metrics = self._metrics[operation]
        metrics['total_time'] += execution_time
        metrics['count'] += 1
        metrics['min_time'] = min(metrics['min_time'], execution_time)
        metrics['max_time'] = max(metrics['max_time'], execution_time)
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标
        
        Args:
            operation: 可选的操作名称，如果为None则返回所有操作的指标
            
        Returns:
            性能指标字典
        """
        if operation:
            if operation not in self._metrics:
                return {}
            
            metrics = self._metrics[operation]
            return {
                'operation': operation,
                'total_time': metrics['total_time'],
                'count': metrics['count'],
                'average_time': metrics['total_time'] / metrics['count'],
                'min_time': metrics['min_time'],
                'max_time': metrics['max_time']
            }
        
        return {
            op: self.get_metrics(op) 
            for op in self._metrics
        }
    
    def reset_metrics(self, operation: Optional[str] = None) -> None:
        """重置性能指标
        
        Args:
            operation: 可选的操作名称，如果为None则重置所有操作的指标
        """
        if operation:
            self._metrics.pop(operation, None)
        else:
            self._metrics.clear()


# 全局性能监控器实例
_performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: Optional[str] = None):
    """性能监控装饰器
    
    Args:
        operation_name: 可选的操作名称，如果为None则使用函数名
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                _performance_monitor.record_execution_time(op_name, execution_time)
                logger.debug(f"{op_name} 执行时间: {execution_time:.4f}秒")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                _performance_monitor.record_execution_time(op_name, execution_time)
                logger.debug(f"{op_name} 执行时间: {execution_time:.4f}秒")
        
        # 根据函数是否是协程函数选择包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_performance_metrics(operation: Optional[str] = None) -> Dict[str, Any]:
    """获取性能指标
    
    Args:
        operation: 可选的操作名称
        
    Returns:
        性能指标字典
    """
    return _performance_monitor.get_metrics(operation)


def reset_performance_metrics(operation: Optional[str] = None) -> None:
    """重置性能指标
    
    Args:
        operation: 可选的操作名称
    """
    _performance_monitor.reset_metrics(operation)