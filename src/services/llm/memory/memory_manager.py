import gc
import psutil
import asyncio
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from src.interfaces.dependency_injection import get_logger
from datetime import datetime

from ..core.base_factory import BaseFactory

logger = get_logger(__name__)


class MemoryManager(BaseFactory):
    """内存使用管理器"""
    
    def __init__(self, max_memory_mb: int = 512, gc_threshold_mb: float = 0.8):
        """
        初始化内存管理器
        
        Args:
            max_memory_mb: 最大内存使用量（MB）
            gc_threshold_mb: 触发垃圾回收的内存使用阈值（百分比）
        """
        self.max_memory = max_memory_mb
        self.gc_threshold = gc_threshold_mb
        self._current_usage = 0
        self._monitoring_enabled = True
        self._logger = get_logger(__name__)
        self._callbacks: Dict[str, Callable] = {}
        
        # 设置垃圾回收阈值
        gc.set_threshold(700, 10, 10)  # 调整垃圾回收频率
    
    def create(self, max_memory_mb: Optional[int] = None, gc_threshold_mb: Optional[float] = None) -> 'MemoryManager':
        """
        创建内存管理器实例（工厂方法）
        
        Args:
            max_memory_mb: 最大内存使用量（MB）
            gc_threshold_mb: 触发垃圾回收的内存使用阈值（百分比）
            
        Returns:
            MemoryManager: 内存管理器实例
        """
        # 由于这是单例模式，直接返回自身
        if max_memory_mb is not None:
            self.max_memory = max_memory_mb
        if gc_threshold_mb is not None:
            self.gc_threshold = gc_threshold_mb
        
        return self
    
    def track_memory_usage(self, operation: str, size: int) -> None:
        """跟踪内存使用情况"""
        self._current_usage += size
        
        # 检查是否超过阈值
        if self._is_memory_usage_high():
            self._trigger_gc()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取当前内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss,  # 实际物理内存使用
            "vms": memory_info.vms,  # 虚拟内存使用
            "percent": process.memory_percent(),
            "max_allowed_mb": self.max_memory,
            "current_usage_mb": self._current_usage / (1024 * 1024) if isinstance(self._current_usage, (int, float)) else 0
        }
    
    def _is_memory_usage_high(self) -> bool:
        """检查内存使用是否过高"""
        memory_percent = self._get_memory_percent()
        return memory_percent > (self.gc_threshold * 100)
    
    def _get_memory_percent(self) -> float:
        """获取当前内存使用百分比"""
        try:
            process = psutil.Process()
            return process.memory_percent()
        except Exception:
            # 如果无法获取进程内存信息，使用内部跟踪值
            estimated_percent = (self._current_usage / (self.max_memory * 1024 * 1024)) * 100
            return min(estimated_percent, 100.0)
    
    def _trigger_gc(self) -> None:
        """触发垃圾回收"""
        try:
            collected = gc.collect()
            self._logger.info(f"Garbage collection triggered. Collected {collected} objects.")
            
            # 执行回调
            if "gc_triggered" in self._callbacks:
                self._callbacks["gc_triggered"]()
                
        except Exception as e:
            self._logger.error(f"Error during garbage collection: {e}")
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """注册事件回调"""
        self._callbacks[event] = callback
    
    def set_monitoring_enabled(self, enabled: bool) -> None:
        """启用或禁用内存监控"""
        self._monitoring_enabled = enabled
    
    async def monitor_memory_usage(self, interval: int = 30) -> None:
        """异步监控内存使用情况"""
        while self._monitoring_enabled:
            try:
                memory_info = self.get_memory_usage()
                self._logger.debug(f"Memory usage: {memory_info}")
                
                # 如果内存使用过高，触发垃圾回收
                if self._is_memory_usage_high():
                    self._trigger_gc()
                
                await asyncio.sleep(interval)
            except Exception as e:
                self._logger.error(f"Error in memory monitoring: {e}")
                await asyncio.sleep(interval)
    
    def get_detailed_memory_report(self) -> Dict[str, Any]:
        """获取详细的内存使用报告"""
        import sys
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "memory_usage": self.get_memory_usage(),
            "gc_stats": gc.get_stats(),
            "gc_objects": len(gc.get_objects()),
            "tracemalloc_enabled": hasattr(sys, 'gettrace') and sys.gettrace() is not None
        }
        
        # 获取引用最多的对象类型
        objects_by_type = {}
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            objects_by_type[obj_type] = objects_by_type.get(obj_type, 0) + 1
        
        # 获取前10个最常见的对象类型
        sorted_types = sorted(objects_by_type.items(), key=lambda x: x[1], reverse=True)[:10]
        report["top_object_types"] = sorted_types
        
        return report


class MemoryManagerFactory:
    """内存管理器工厂（保持向后兼容）"""
    
    _instance: Optional['MemoryManagerFactory'] = None
    _manager: Optional[MemoryManager] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_manager(self, max_memory_mb: int = 512) -> MemoryManager:
        """获取内存管理器实例"""
        if self._manager is None:
            self._manager = MemoryManager(max_memory_mb)
        return self._manager


# 全局内存管理器工厂实例
memory_manager_factory = MemoryManagerFactory()

# 注册到工厂注册表
BaseFactory.register("memory_manager", MemoryManager)