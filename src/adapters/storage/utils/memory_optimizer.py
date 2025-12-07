"""存储内存优化器

提供内存监控和自适应批次大小调整功能，优化流式操作的内存使用。
"""

import gc
import os
import psutil
import threading
import time
from typing import Dict, Any, Optional


class MemoryOptimizer:
    """存储内存优化器
    
    监控内存使用情况，并根据可用内存自适应调整批次大小，
    以优化流式操作的内存使用效率。
    """
    
    def __init__(
        self,
        initial_batch_size: int = 100,
        min_batch_size: int = 10,
        max_batch_size: int = 1000,
        memory_threshold_percent: float = 80.0,
        adjustment_factor: float = 0.8,
        enable_auto_gc: bool = True,
        gc_threshold_percent: float = 85.0
    ) -> None:
        """初始化内存优化器
        
        Args:
            initial_batch_size: 初始批次大小
            min_batch_size: 最小批次大小
            max_batch_size: 最大批次大小
            memory_threshold_percent: 内存使用阈值百分比
            adjustment_factor: 批次大小调整因子
            enable_auto_gc: 是否启用自动垃圾回收
            gc_threshold_percent: 垃圾回收阈值百分比
        """
        self.initial_batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.memory_threshold_percent = memory_threshold_percent
        self.adjustment_factor = adjustment_factor
        self.enable_auto_gc = enable_auto_gc
        self.gc_threshold_percent = gc_threshold_percent
        
        # 当前批次大小
        self.current_batch_size = initial_batch_size
        
        # 内存监控
        self.process = psutil.Process(os.getpid())
        self.memory_stats: Dict[str, Any] = {}
        self.last_check_time = 0
        self.check_interval = 5  # 秒
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 调整历史
        self.adjustment_history: list = []
        self.max_history_size = 100
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取当前内存使用情况
        
        Returns:
            内存使用统计信息
        """
        try:
            # 进程内存信息
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 系统内存信息
            system_memory = psutil.virtual_memory()
            
            # 计算内存使用率
            process_memory_mb = memory_info.rss / (1024 * 1024)
            system_memory_mb = system_memory.used / (1024 * 1024)
            system_memory_total_mb = system_memory.total / (1024 * 1024)
            
            stats = {
                "process_memory_mb": round(process_memory_mb, 2),
                "process_memory_percent": round(memory_percent, 2),
                "system_memory_mb": round(system_memory_mb, 2),
                "system_memory_total_mb": round(system_memory_total_mb, 2),
                "system_memory_percent": system_memory.percent,
                "available_memory_mb": round(system_memory.available / (1024 * 1024), 2),
                "timestamp": time.time()
            }
            
            with self._lock:
                self.memory_stats = stats
            
            return stats
            
        except Exception as e:
            return {"error": str(e), "timestamp": time.time()}
    
    def should_adjust_batch_size(self) -> bool:
        """检查是否应该调整批次大小
        
        Returns:
            是否应该调整批次大小
        """
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return False
        
        self.last_check_time = current_time
        memory_stats = self.get_memory_usage()
        
        # 检查内存使用率
        memory_percent = memory_stats.get("process_memory_percent", 0)
        system_memory_percent = memory_stats.get("system_memory_percent", 0)
        
        # 如果进程或系统内存使用率超过阈值，需要调整
        return (memory_percent > self.memory_threshold_percent or 
                system_memory_percent > self.memory_threshold_percent)
    
    def adjust_batch_size(self) -> int:
        """调整批次大小
        
        Returns:
            调整后的批次大小
        """
        with self._lock:
            memory_stats = self.get_memory_usage()
            memory_percent = memory_stats.get("process_memory_percent", 0)
            system_memory_percent = memory_stats.get("system_memory_percent", 0)
            
            old_batch_size = self.current_batch_size
            
            # 根据内存使用率调整批次大小
            if (memory_percent > self.gc_threshold_percent or 
                system_memory_percent > self.gc_threshold_percent):
                # 内存使用率过高，减小批次大小
                new_batch_size = max(
                    self.min_batch_size,
                    int(self.current_batch_size * self.adjustment_factor)
                )
                
                # 触发垃圾回收
                if self.enable_auto_gc:
                    gc.collect()
                
                adjustment_type = "decrease"
            elif (memory_percent < self.memory_threshold_percent * 0.6 and 
                  system_memory_percent < self.memory_threshold_percent * 0.6):
                # 内存使用率较低，可以增加批次大小
                new_batch_size = min(
                    self.max_batch_size,
                    int(self.current_batch_size / self.adjustment_factor)
                )
                adjustment_type = "increase"
            else:
                # 内存使用率适中，不调整
                new_batch_size = self.current_batch_size
                adjustment_type = "no_change"
            
            # 记录调整历史
            if new_batch_size != old_batch_size:
                self.adjustment_history.append({
                    "timestamp": time.time(),
                    "old_batch_size": old_batch_size,
                    "new_batch_size": new_batch_size,
                    "adjustment_type": adjustment_type,
                    "memory_percent": memory_percent,
                    "system_memory_percent": system_memory_percent
                })
                
                # 限制历史记录大小
                if len(self.adjustment_history) > self.max_history_size:
                    self.adjustment_history.pop(0)
            
            self.current_batch_size = new_batch_size
            return new_batch_size
    
    def get_optimal_batch_size(self, data_size_hint: Optional[int] = None) -> int:
        """获取最优批次大小
        
        Args:
            data_size_hint: 数据大小提示（字节）
            
        Returns:
            最优批次大小
        """
        # 检查是否需要调整批次大小
        if self.should_adjust_batch_size():
            self.adjust_batch_size()
        
        # 如果有数据大小提示，可以进一步优化
        if data_size_hint:
            memory_stats = self.get_memory_usage()
            available_memory_mb = memory_stats.get("available_memory_mb", 100)
            
            # 估算每个记录的大小
            estimated_record_size_kb = data_size_hint / 1024
            
            # 计算基于可用内存的批次大小
            memory_based_batch_size = int(
                (available_memory_mb * 1024 * 0.3) / estimated_record_size_kb
            )
            
            # 取当前批次大小和基于内存的批次大小的较小值
            optimal_batch_size = min(self.current_batch_size, memory_based_batch_size)
            
            # 确保在最小和最大范围内
            optimal_batch_size = max(self.min_batch_size, optimal_batch_size)
            optimal_batch_size = min(self.max_batch_size, optimal_batch_size)
            
            return optimal_batch_size
        
        return self.current_batch_size
    
    def get_stats(self) -> Dict[str, Any]:
        """获取优化器统计信息
        
        Returns:
            优化器统计信息
        """
        with self._lock:
            memory_stats = self.get_memory_usage()
            
            # 计算调整统计
            total_adjustments = len(self.adjustment_history)
            recent_adjustments = [
                adj for adj in self.adjustment_history
                if time.time() - adj["timestamp"] < 3600  # 最近1小时
            ]
            
            return {
                "current_batch_size": self.current_batch_size,
                "initial_batch_size": self.initial_batch_size,
                "min_batch_size": self.min_batch_size,
                "max_batch_size": self.max_batch_size,
                "total_adjustments": total_adjustments,
                "recent_adjustments": len(recent_adjustments),
                "memory_threshold_percent": self.memory_threshold_percent,
                "adjustment_factor": self.adjustment_factor,
                "memory_stats": memory_stats,
                "last_adjustment": self.adjustment_history[-1] if self.adjustment_history else None
            }
    
    def reset(self) -> None:
        """重置优化器状态"""
        with self._lock:
            self.current_batch_size = self.initial_batch_size
            self.adjustment_history.clear()
            self.memory_stats.clear()
            self.last_check_time = 0
    
    def configure(
        self,
        batch_size: Optional[int] = None,
        memory_threshold: Optional[float] = None,
        adjustment_factor: Optional[float] = None
    ) -> None:
        """配置优化器参数
        
        Args:
            batch_size: 批次大小
            memory_threshold: 内存阈值百分比
            adjustment_factor: 调整因子
        """
        with self._lock:
            if batch_size is not None:
                self.current_batch_size = max(self.min_batch_size, min(batch_size, self.max_batch_size))
            
            if memory_threshold is not None:
                self.memory_threshold_percent = max(10.0, min(memory_threshold, 95.0))
            
            if adjustment_factor is not None:
                self.adjustment_factor = max(0.1, min(adjustment_factor, 0.9))


# 全局内存优化器实例
_global_optimizer: Optional[MemoryOptimizer] = None
_optimizer_lock = threading.Lock()


def get_global_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器实例
    
    Returns:
        全局内存优化器实例
    """
    global _global_optimizer
    
    if _global_optimizer is None:
        with _optimizer_lock:
            if _global_optimizer is None:
                _global_optimizer = MemoryOptimizer()
    
    return _global_optimizer


def configure_global_optimizer(**kwargs) -> None:
    """配置全局内存优化器
    
    Args:
        **kwargs: 配置参数
    """
    optimizer = get_global_optimizer()
    optimizer.configure(**kwargs)


def reset_global_optimizer() -> None:
    """重置全局内存优化器"""
    global _global_optimizer
    
    with _optimizer_lock:
        if _global_optimizer is not None:
            _global_optimizer.reset()
            _global_optimizer = None