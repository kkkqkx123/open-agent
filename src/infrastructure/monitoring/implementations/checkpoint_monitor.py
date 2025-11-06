"""检查点性能监控器

专门用于监控检查点操作的性能指标。
"""

from typing import Optional, Dict, Any

from ..base_monitor import BasePerformanceMonitor


class CheckpointPerformanceMonitor(BasePerformanceMonitor):
    """检查点性能监控器"""
    
    def __init__(self, max_history_size: int = 1000):
        """初始化检查点性能监控器
        
        Args:
            max_history_size: 最大历史记录大小
        """
        super().__init__(max_history_size)
        self._config.update({
            "module": "checkpoint",
            "description": "检查点性能监控"
        })
    
    def record_checkpoint_save(self, duration: float, size: int, success: bool = True) -> None:
        """记录检查点保存操作
        
        Args:
            duration: 保存耗时（秒）
            size: 检查点大小（字节）
            success: 是否成功
        """
        labels = {"operation": "save"}
        
        # 记录保存时间
        self.record_timer("checkpoint.save.duration", duration, labels)
        
        # 记录检查点大小
        self.set_gauge("checkpoint.save.size", size, labels)
        
        # 记录成功/失败计数
        if success:
            self.increment_counter("checkpoint.save.success", 1, labels)
        else:
            self.increment_counter("checkpoint.save.failure", 1, labels)
    
    def record_checkpoint_load(self, duration: float, size: int, success: bool = True) -> None:
        """记录检查点加载操作
        
        Args:
            duration: 加载耗时（秒）
            size: 检查点大小（字节）
            success: 是否成功
        """
        labels = {"operation": "load"}
        
        # 记录加载时间
        self.record_timer("checkpoint.load.duration", duration, labels)
        
        # 记录检查点大小
        self.set_gauge("checkpoint.load.size", size, labels)
        
        # 记录成功/失败计数
        if success:
            self.increment_counter("checkpoint.load.success", 1, labels)
        else:
            self.increment_counter("checkpoint.load.failure", 1, labels)
    
    def record_checkpoint_list(self, duration: float, count: int) -> None:
        """记录检查点列表操作
        
        Args:
            duration: 列表操作耗时（秒）
            count: 检查点数量
        """
        labels = {"operation": "list"}
        
        # 记录列表时间
        self.record_timer("checkpoint.list.duration", duration, labels)
        
        # 记录检查点数量
        self.set_gauge("checkpoint.list.count", count, labels)