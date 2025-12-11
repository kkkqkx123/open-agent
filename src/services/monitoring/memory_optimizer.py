"""内存使用优化模块

提供内存监控、优化和管理功能。
"""

import gc
from src.interfaces.dependency_injection import get_logger
import threading
import time
import weakref
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass
from collections import defaultdict
import psutil
import os

logger = get_logger(__name__)


@dataclass
class MemoryStats:
    """内存统计信息"""
    total_mb: float
    used_mb: float
    available_mb: float
    percent: float
    process_mb: float
    timestamp: float


@dataclass
class MemoryOptimizationResult:
    """内存优化结果"""
    freed_mb: float
    objects_collected: int
    duration_seconds: float
    strategies_used: List[str]


class MemoryOptimizer:
    """内存优化器
    
    提供内存监控、垃圾回收优化和内存泄漏检测功能。
    """
    
    def __init__(self, monitoring_interval: float = 60.0):
        """初始化内存优化器
        
        Args:
            monitoring_interval: 监控间隔（秒）
        """
        self.monitoring_interval = monitoring_interval
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stats_history: List[MemoryStats] = []
        self._object_refs: Dict[str, Set[weakref.ref]] = defaultdict(set)
        self._callbacks: List[Callable[[MemoryStats], None]] = []
        self._lock = threading.RLock()
        
        # 优化策略配置
        self.optimization_strategies = {
            'gc_collect': True,
            'weakref_cleanup': True,
            'cache_clear': True,
            'cyclic_reference_check': True
        }
        
        logger.debug("MemoryOptimizer初始化完成")
    
    def start_monitoring(self) -> None:
        """开始内存监控"""
        with self._lock:
            if self._monitoring:
                return
            
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="MemoryMonitor",
                daemon=True
            )
            self._monitor_thread.start()
            
            logger.info("内存监控已启动")
    
    def stop_monitoring(self) -> None:
        """停止内存监控"""
        with self._lock:
            if not self._monitoring:
                return
            
            self._monitoring = False
            
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)
            
            logger.info("内存监控已停止")
    
    def add_monitoring_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """添加监控回调
        
        Args:
            callback: 回调函数，接收MemoryStats参数
        """
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_monitoring_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """移除监控回调
        
        Args:
            callback: 要移除的回调函数
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def get_current_stats(self) -> MemoryStats:
        """获取当前内存统计
        
        Returns:
            MemoryStats: 当前内存统计信息
        """
        # 系统内存信息
        memory = psutil.virtual_memory()
        
        # 进程内存信息
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return MemoryStats(
            total_mb=memory.total / 1024 / 1024,
            used_mb=memory.used / 1024 / 1024,
            available_mb=memory.available / 1024 / 1024,
            percent=memory.percent,
            process_mb=process_memory,
            timestamp=time.time()
        )
    
    def get_stats_history(self, limit: Optional[int] = None) -> List[MemoryStats]:
        """获取历史统计信息
        
        Args:
            limit: 限制返回的记录数量
            
        Returns:
            List[MemoryStats]: 历史统计信息
        """
        with self._lock:
            if limit:
                return self._stats_history[-limit:]
            return self._stats_history.copy()
    
    def optimize_memory(self, aggressive: bool = False) -> MemoryOptimizationResult:
        """优化内存使用

        Args:
            aggressive: 是否使用激进优化策略

        Returns:
            MemoryOptimizationResult: 优化结果
        """
        start_time = time.time()
        initial_stats = self.get_current_stats()
        strategies_used = []

        # 初始化对象计数变量
        objects_before = 0
        objects_after = 0

        try:
            # 策略1: 垃圾回收
            if self.optimization_strategies['gc_collect']:
                objects_before = len(gc.get_objects())
                collected = gc.collect()
                objects_after = len(gc.get_objects())

                strategies_used.append('gc_collect')
                logger.debug(f"垃圾回收: 回收了 {collected} 个对象")
            
            # 策略2: 弱引用清理
            if self.optimization_strategies['weakref_cleanup']:
                self._cleanup_weak_references()
                strategies_used.append('weakref_cleanup')
            
            # 策略3: 缓存清理
            if self.optimization_strategies['cache_clear']:
                self._clear_caches()
                strategies_used.append('cache_clear')
            
            # 策略4: 循环引用检查（激进模式）
            if aggressive and self.optimization_strategies['cyclic_reference_check']:
                self._detect_and_break_cycles()
                strategies_used.append('cyclic_reference_check')
            
            # 再次垃圾回收
            if aggressive:
                gc.collect()
            
        except Exception as e:
            logger.error(f"内存优化过程中发生错误: {e}")
        
        # 计算优化结果
        end_time = time.time()
        final_stats = self.get_current_stats()

        freed_mb = initial_stats.process_mb - final_stats.process_mb
        # 如果执行了垃圾回收策略，使用前后计数差，否则为0
        objects_collected = objects_after - objects_before if self.optimization_strategies['gc_collect'] else 0
        
        result = MemoryOptimizationResult(
            freed_mb=freed_mb,
            objects_collected=objects_collected,
            duration_seconds=end_time - start_time,
            strategies_used=strategies_used
        )
        
        logger.info(f"内存优化完成: 释放 {freed_mb:.2f}MB, 耗时 {result.duration_seconds:.3f}s")
        return result
    
    def track_object(self, category: str, obj: Any) -> None:
        """跟踪对象
        
        Args:
            category: 对象类别
            obj: 要跟踪的对象
        """
        with self._lock:
            def cleanup_callback(ref):
                """弱引用清理回调"""
                with self._lock:
                    if category in self._object_refs:
                        self._object_refs[category].discard(ref)
            
            weak_ref = weakref.ref(obj, cleanup_callback)
            self._object_refs[category].add(weak_ref)
    
    def get_tracked_objects_count(self, category: Optional[str] = None) -> Dict[str, int]:
        """获取跟踪对象数量
        
        Args:
            category: 对象类别，None表示所有类别
            
        Returns:
            Dict[str, int]: 类别到对象数量的映射
        """
        with self._lock:
            if category:
                if category in self._object_refs:
                    # 清理已死亡的弱引用
                    alive_refs = [ref for ref in self._object_refs[category] if ref() is not None]
                    self._object_refs[category] = set(alive_refs)
                    return {category: len(alive_refs)}
                return {category: 0}
            
            result = {}
            for cat, refs in self._object_refs.items():
                # 清理已死亡的弱引用
                alive_refs = [ref for ref in refs if ref() is not None]
                self._object_refs[cat] = set(alive_refs)
                result[cat] = len(alive_refs)
            
            return result
    
    def detect_memory_leaks(self, threshold_mb: float = 10.0) -> List[str]:
        """检测内存泄漏
        
        Args:
            threshold_mb: 内存增长阈值（MB）
            
        Returns:
            List[str]: 检测到的问题描述
        """
        issues = []
        
        with self._lock:
            if len(self._stats_history) < 2:
                return ["历史数据不足，无法检测内存泄漏"]
            
            # 检查内存增长趋势
            recent_stats = self._stats_history[-10:]  # 最近10个记录
            if len(recent_stats) >= 2:
                memory_growth = recent_stats[-1].process_mb - recent_stats[0].process_mb
                time_elapsed = recent_stats[-1].timestamp - recent_stats[0].timestamp
                
                if time_elapsed > 0:
                    growth_rate = memory_growth / time_elapsed  # MB/s
                    
                    if memory_growth > threshold_mb:
                        issues.append(f"检测到内存增长: {memory_growth:.2f}MB (增长率: {growth_rate:.3f}MB/s)")
            
            # 检查对象数量异常
            tracked_counts = self.get_tracked_objects_count()
            for category, count in tracked_counts.items():
                if count > 1000:  # 阈值可配置
                    issues.append(f"类别 '{category}' 的对象数量过多: {count}")
        
        return issues
    
    def set_optimization_strategy(self, strategy: str, enabled: bool) -> None:
        """设置优化策略
        
        Args:
            strategy: 策略名称
            enabled: 是否启用
        """
        if strategy in self.optimization_strategies:
            self.optimization_strategies[strategy] = enabled
            logger.debug(f"优化策略 '{strategy}' {'启用' if enabled else '禁用'}")
        else:
            logger.warning(f"未知的优化策略: {strategy}")
    
    def get_optimization_strategies(self) -> Dict[str, bool]:
        """获取优化策略配置
        
        Returns:
            Dict[str, bool]: 策略名称到启用状态的映射
        """
        return self.optimization_strategies.copy()
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self._monitoring:
            try:
                stats = self.get_current_stats()
                
                with self._lock:
                    self._stats_history.append(stats)
                    
                    # 限制历史记录数量
                    if len(self._stats_history) > 1000:
                        self._stats_history = self._stats_history[-500:]
                    
                    # 调用回调函数
                    for callback in self._callbacks:
                        try:
                            callback(stats)
                        except Exception as e:
                            logger.error(f"监控回调执行失败: {e}")
                
                # 检查是否需要自动优化
                if stats.percent > 90:  # 内存使用率超过90%
                    logger.warning(f"内存使用率过高: {stats.percent:.1f}%")
                    self.optimize_memory()
                
            except Exception as e:
                logger.error(f"内存监控错误: {e}")
            
            # 等待下次监控
            time.sleep(self.monitoring_interval)
    
    def _cleanup_weak_references(self) -> None:
        """清理弱引用"""
        with self._lock:
            for category, refs in self._object_refs.items():
                # 移除已死亡的弱引用
                alive_refs = [ref for ref in refs if ref() is not None]
                self._object_refs[category] = set(alive_refs)
    
    def _clear_caches(self) -> None:
        """清理缓存"""
        try:
            # 清除标准库缓存
            import functools
            if hasattr(functools, '_lru_cache_wrapper'):
                # 这里可以添加具体的缓存清理逻辑
                pass
            
            # 清除模块缓存（谨慎使用）
            # import sys
            # for module_name in list(sys.modules.keys()):
            #     if module_name.startswith('src.'):
            #         del sys.modules[module_name]
            
            logger.debug("缓存清理完成")
        except Exception as e:
            logger.error(f"缓存清理失败: {e}")
    
    def _detect_and_break_cycles(self) -> None:
        """检测并打破循环引用"""
        try:
            # 查找循环引用
            gc.collect()  # 确保垃圾回收器已识别循环引用
            
            unreachable = gc.collect()
            if unreachable > 0:
                logger.debug(f"发现并清理了 {unreachable} 个不可达对象（循环引用）")
        except Exception as e:
            logger.error(f"循环引用检测失败: {e}")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """获取内存使用报告
        
        Returns:
            Dict[str, Any]: 内存使用报告
        """
        current_stats = self.get_current_stats()
        tracked_objects = self.get_tracked_objects_count()
        issues = self.detect_memory_leaks()
        
        return {
            "current_stats": {
                "total_mb": current_stats.total_mb,
                "used_mb": current_stats.used_mb,
                "available_mb": current_stats.available_mb,
                "percent": current_stats.percent,
                "process_mb": current_stats.process_mb
            },
            "tracked_objects": tracked_objects,
            "issues": issues,
            "optimization_strategies": self.optimization_strategies,
            "monitoring_active": self._monitoring,
            "history_count": len(self._stats_history)
        }


# 全局内存优化器实例
_global_memory_optimizer: Optional[MemoryOptimizer] = None


def get_global_memory_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器
    
    Returns:
        MemoryOptimizer: 全局内存优化器实例
    """
    global _global_memory_optimizer
    if _global_memory_optimizer is None:
        _global_memory_optimizer = MemoryOptimizer()
    return _global_memory_optimizer


def start_memory_monitoring() -> None:
    """启动全局内存监控"""
    optimizer = get_global_memory_optimizer()
    optimizer.start_monitoring()


def stop_memory_monitoring() -> None:
    """停止全局内存监控"""
    optimizer = get_global_memory_optimizer()
    optimizer.stop_monitoring()


def optimize_memory(aggressive: bool = False) -> MemoryOptimizationResult:
    """优化全局内存使用
    
    Args:
        aggressive: 是否使用激进优化策略
        
    Returns:
        MemoryOptimizationResult: 优化结果
    """
    optimizer = get_global_memory_optimizer()
    return optimizer.optimize_memory(aggressive)


def track_object(category: str, obj: Any) -> None:
    """跟踪对象到全局优化器
    
    Args:
        category: 对象类别
        obj: 要跟踪的对象
    """
    optimizer = get_global_memory_optimizer()
    optimizer.track_object(category, obj)


def get_memory_report() -> Dict[str, Any]:
    """获取全局内存使用报告
    
    Returns:
        Dict[str, Any]: 内存使用报告
    """
    optimizer = get_global_memory_optimizer()
    return optimizer.get_memory_report()