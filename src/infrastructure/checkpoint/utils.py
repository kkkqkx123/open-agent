"""检查点模块便利工具

提供检查点性能监控的便利函数和装饰器。
"""

import time
import logging
from functools import wraps
from typing import Any, Callable, cast

from . import CheckpointPerformanceMonitor, PerformanceMonitorFactory

logger = logging.getLogger(__name__)


def get_checkpoint_monitor() -> CheckpointPerformanceMonitor:
    """获取检查点性能监控器实例
    
    Returns:
        CheckpointPerformanceMonitor: 检查点性能监控器实例
    """
    factory = PerformanceMonitorFactory.get_instance()
    monitor = factory.get_monitor("checkpoint")
    
    if monitor is None:
        monitor = factory.create_monitor("checkpoint")
    
    return cast(CheckpointPerformanceMonitor, monitor)


def monitor_checkpoint_performance(operation_name: str | None = None):
    """检查点性能监控装饰器
    
    Args:
        operation_name: 操作名称，如果为None则使用函数名
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
                _record_operation_by_name(op_name, execution_time)
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
                _record_operation_by_name(op_name, execution_time)
                logger.debug(f"{op_name} 执行时间: {execution_time:.4f}秒")
        
        # 根据函数是否是协程函数选择包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _record_operation_by_name(operation: str, execution_time: float) -> None:
    """根据操作名称记录性能指标
    
    Args:
        operation: 操作名称
        execution_time: 执行时间（秒）
    """
    try:
        monitor = get_checkpoint_monitor()
        
        # 根据操作类型记录不同的指标
        if "save" in operation.lower():
            monitor.record_checkpoint_save(execution_time, 0, True)  # 大小暂时设为0
        elif "load" in operation.lower():
            monitor.record_checkpoint_load(execution_time, 0, True)  # 大小暂时设为0
        elif "list" in operation.lower():
            monitor.record_checkpoint_list(execution_time, 0)  # 数量暂时设为0
        else:
            # 对于其他操作，使用通用的计时器
            monitor.record_timer(f"checkpoint.{operation}", execution_time)
    except Exception as e:
        logger.warning(f"记录检查点操作失败: {e}")