"""检查点性能监控器

专门用于监控检查点操作的性能指标，使用零内存存储。
"""

from typing import Optional, Dict, Any

from ..lightweight_monitor import LightweightPerformanceMonitor
from ..logger_writer import PerformanceMetricsLogger


class CheckpointPerformanceMonitor(LightweightPerformanceMonitor):
    """检查点性能监控器 - 零内存存储版本"""
    
    def __init__(self, logger: Optional[PerformanceMetricsLogger] = None):
        """初始化检查点性能监控器
        
        Args:
            logger: 性能指标日志写入器，如果为None则创建默认实例
        """
        super().__init__(logger or PerformanceMetricsLogger("checkpoint_metrics"))
    
    def record_checkpoint_save(self, duration: float, size: int, success: bool = True) -> None:
        """记录检查点保存操作
        
        Args:
            duration: 保存耗时（秒）
            size: 检查点大小（字节）
            success: 是否成功
        """
        self.logger.log_checkpoint_save(duration, size, success)
    
    def record_checkpoint_load(self, duration: float, size: int, success: bool = True) -> None:
        """记录检查点加载操作
        
        Args:
            duration: 加载耗时（秒）
            size: 检查点大小（字节）
            success: 是否成功
        """
        self.logger.log_checkpoint_load(duration, size, success)
    
    def record_checkpoint_list(self, duration: float, count: int) -> None:
        """记录检查点列表操作
        
        Args:
            duration: 列表操作耗时（秒）
            count: 检查点数量
        """
        self.logger.log_checkpoint_list(duration, count)