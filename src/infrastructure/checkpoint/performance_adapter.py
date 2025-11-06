"""检查点性能监控适配器

将新的统一性能监控系统与现有的检查点性能监控代码集成。
"""

import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

from ..monitoring import PerformanceMonitorFactory

logger = logging.getLogger(__name__)


class CheckpointPerformanceAdapter:
    """检查点性能监控适配器"""
    
    def __init__(self):
        """初始化适配器"""
        # 获取检查点性能监控器实例
        factory = PerformanceMonitorFactory.get_instance()
        self._monitor = factory.get_monitor("checkpoint")
        
        # 如果没有创建过检查点监控器，则创建一个
        if self._monitor is None:
            self._monitor = factory.create_monitor("checkpoint")
    
    def record_execution_time(self, operation: str, execution_time: float) -> None:
        """记录执行时间（适配旧接口）
        
        Args:
            operation: 操作名称
            execution_time: 执行时间（秒）
        """
        # 使用新的监控器记录执行时间
        if self._monitor:
            # 将操作名称映射为新的指标名称
            if operation.startswith("checkpoint_save"):
                self._monitor.record_checkpoint_save(execution_time, 0)  # 大小暂时设为0
            elif operation.startswith("checkpoint_load"):
                self._monitor.record_checkpoint_load(execution_time, 0)  # 大小暂时设为0
            else:
                # 对于其他操作，使用通用的计时器
                self._monitor.record_timer(f"checkpoint.{operation}", execution_time)
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标（适配旧接口）
        
        Args:
            operation: 可选的操作名称
            
        Returns:
            性能指标字典
        """
        if self._monitor:
            # 获取所有指标并转换为旧格式
            all_metrics = self._monitor.get_all_metrics()
            
            # 简化的转换逻辑
            result = {}
            if operation:
                # 返回特定操作的指标（简化实现）
                result['operation'] = operation
                result['total_time'] = 0.0
                result['count'] = 0
                result['average_time'] = 0.0
                result['min_time'] = 0.0
                result['max_time'] = 0.0
            else:
                # 返回所有操作的指标（简化实现）
                for key, value in all_metrics.items():
                    result[key] = value
                    
            return result
        
        return {}
    
    def reset_metrics(self, operation: Optional[str] = None) -> None:
        """重置性能指标（适配旧接口）
        
        Args:
            operation: 可选的操作名称
        """
        if self._monitor:
            self._monitor.reset_metrics()


# 全局适配器实例
_checkpoint_performance_adapter = CheckpointPerformanceAdapter()


def monitor_performance(operation_name: Optional[str] = None):
    """性能监控装饰器（适配旧接口）
    
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
                _checkpoint_performance_adapter.record_execution_time(op_name, execution_time)
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
                _checkpoint_performance_adapter.record_execution_time(op_name, execution_time)
                logger.debug(f"{op_name} 执行时间: {execution_time:.4f}秒")
        
        # 根据函数是否是协程函数选择包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_performance_metrics(operation: Optional[str] = None) -> Dict[str, Any]:
    """获取性能指标（适配旧接口）
    
    Args:
        operation: 可选的操作名称
        
    Returns:
        性能指标字典
    """
    return _checkpoint_performance_adapter.get_metrics(operation)


def reset_performance_metrics(operation: Optional[str] = None) -> None:
    """重置性能指标（适配旧接口）
    
    Args:
        operation: 可选的操作名称
    """
    _checkpoint_performance_adapter.reset_metrics(operation)