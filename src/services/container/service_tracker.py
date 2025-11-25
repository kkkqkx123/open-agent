"""服务追踪器实现"""

import logging
import threading
import time
import weakref
from typing import Type, Dict, Any, List, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.interfaces.container import IServiceTracker

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstanceInfo:
    """服务实例信息"""
    instance: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    creation_stack: Optional[str] = None
    is_disposed: bool = False
    disposal_time: Optional[datetime] = None
    memory_usage: int = 0
    
    def mark_accessed(self) -> None:
        """标记访问"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def mark_disposed(self) -> None:
        """标记已释放"""
        self.is_disposed = True
        self.disposal_time = datetime.now()


@dataclass
class MemoryLeakReport:
    """内存泄漏报告"""
    service_type: Type
    leak_instances: List[ServiceInstanceInfo]
    total_instances: int
    leak_duration: timedelta
    estimated_memory_usage: int
    
    def has_leak(self) -> bool:
        return len(self.leak_instances) > 0


@dataclass
class ServiceUsageStats:
    """服务使用统计"""
    service_type: Type
    total_created: int = 0
    total_disposed: int = 0
    current_active: int = 0
    average_lifetime: timedelta = field(default_factory=timedelta)
    peak_active: int = 0
    total_access_count: int = 0
    creation_rate: float = 0.0  # 每秒创建数
    disposal_rate: float = 0.0  # 每秒释放数


class ServiceTracker(IServiceTracker):
    """服务追踪器实现"""
    
    def __init__(self, enable_weak_references: bool = True):
        self._tracked_services: Dict[Type, List[ServiceInstanceInfo]] = defaultdict(list)
        self._service_stats: Dict[Type, ServiceUsageStats] = {}
        self._enable_weak_references = enable_weak_references
        self._weak_refs: Dict[Type, List[weakref.ref]] = defaultdict(list)
        self._lock = threading.RLock()
        self._start_time = datetime.now()
        
        logger.debug("ServiceTracker初始化完成")
    
    def track_creation(self, service_type: Type, instance: Any) -> None:
        """跟踪服务创建"""
        with self._lock:
            # 创建实例信息
            instance_info = ServiceInstanceInfo(
                instance=instance,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                creation_stack=self._get_creation_stack()
            )
            
            # 添加到追踪列表
            self._tracked_services[service_type].append(instance_info)
            
            # 更新统计信息
            stats = self._service_stats.setdefault(service_type, ServiceUsageStats(service_type))
            stats.total_created += 1
            stats.current_active += 1
            stats.peak_active = max(stats.peak_active, stats.current_active)
            
            # 计算创建率
            elapsed = (datetime.now() - self._start_time).total_seconds()
            if elapsed > 0:
                stats.creation_rate = stats.total_created / elapsed
            
            # 使用弱引用跟踪（如果启用）
            if self._enable_weak_references:
                weak_ref = weakref.ref(
                    instance, 
                    lambda ref: self._on_instance_collected(service_type, ref)
                )
                self._weak_refs[service_type].append(weak_ref)
            
            logger.debug(f"跟踪服务创建: {service_type.__name__}, 实例ID: {id(instance)}")
    
    def track_disposal(self, service_type: Type, instance: Any) -> None:
        """跟踪服务释放"""
        with self._lock:
            # 查找实例信息
            instance_info = self._find_instance_info(service_type, instance)
            if instance_info:
                instance_info.mark_disposed()
                
                # 更新统计信息
                stats = self._service_stats.get(service_type)
                if stats:
                    stats.total_disposed += 1
                    stats.current_active -= 1
                    
                    # 计算平均生命周期
                    lifetime = instance_info.disposal_time - instance_info.created_at
                    if stats.total_disposed > 0:
                        total_lifetime = stats.average_lifetime * (stats.total_disposed - 1) + lifetime
                        stats.average_lifetime = total_lifetime / stats.total_disposed
                    
                    # 计算释放率
                    elapsed = (datetime.now() - self._start_time).total_seconds()
                    if elapsed > 0:
                        stats.disposal_rate = stats.total_disposed / elapsed
                
                # 清理弱引用
                self._cleanup_weak_ref(service_type, instance)
                
                logger.debug(f"跟踪服务释放: {service_type.__name__}, 实例ID: {id(instance)}")
            else:
                logger.warning(f"未找到要释放的服务实例: {service_type.__name__}, 实例ID: {id(instance)}")
    
    def get_tracked_services(self) -> Dict[Type, List[Any]]:
        """获取跟踪的服务"""
        with self._lock:
            result = {}
            for service_type, instances in self._tracked_services.items():
                # 只返回未释放的实例
                active_instances = [
                    info.instance for info in instances 
                    if not info.is_disposed
                ]
                if active_instances:
                    result[service_type] = active_instances
            return result
    
    def get_service_usage_statistics(self) -> Dict[Type, ServiceUsageStats]:
        """获取服务使用统计"""
        with self._lock:
            return self._service_stats.copy()
    
    def detect_memory_leaks(self, max_age_hours: int = 1, min_instances: int = 5) -> List[MemoryLeakReport]:
        """检测内存泄漏"""
        with self._lock:
            reports = []
            current_time = datetime.now()
            max_age = timedelta(hours=max_age_hours)
            
            for service_type, instances in self._tracked_services.items():
                leak_instances = []
                
                for instance_info in instances:
                    # 检查是否是潜在的泄漏
                    if (not instance_info.is_disposed and 
                        current_time - instance_info.created_at > max_age):
                        leak_instances.append(instance_info)
                
                # 如果泄漏实例数量超过阈值，生成报告
                if len(leak_instances) >= min_instances:
                    total_memory = sum(info.memory_usage for info in leak_instances)
                    leak_duration = current_time - min(
                        info.created_at for info in leak_instances
                    )
                    
                    report = MemoryLeakReport(
                        service_type=service_type,
                        leak_instances=leak_instances,
                        total_instances=len(instances),
                        leak_duration=leak_duration,
                        estimated_memory_usage=total_memory
                    )
                    reports.append(report)
                    
                    logger.warning(
                        f"检测到潜在内存泄漏: {service_type.__name__}, "
                        f"泄漏实例数: {len(leak_instances)}, "
                        f"持续时间: {leak_duration}"
                    )
            
            return reports
    
    def get_service_details(self, service_type: Type) -> List[ServiceInstanceInfo]:
        """获取服务详细信息"""
        with self._lock:
            return self._tracked_services.get(service_type, []).copy()
    
    def mark_accessed(self, service_type: Type, instance: Any) -> None:
        """标记服务被访问"""
        with self._lock:
            instance_info = self._find_instance_info(service_type, instance)
            if instance_info:
                instance_info.mark_accessed()
                
                # 更新访问统计
                stats = self._service_stats.get(service_type)
                if stats:
                    stats.total_access_count += 1
    
    def get_inactive_services(self, inactive_hours: int = 1) -> Dict[Type, List[ServiceInstanceInfo]]:
        """获取不活跃的服务"""
        with self._lock:
            inactive_threshold = timedelta(hours=inactive_hours)
            current_time = datetime.now()
            inactive_services = defaultdict(list)
            
            for service_type, instances in self._tracked_services.items():
                for instance_info in instances:
                    if (not instance_info.is_disposed and 
                        current_time - instance_info.last_accessed > inactive_threshold):
                        inactive_services[service_type].append(instance_info)
            
            return dict(inactive_services)
    
    def cleanup_disposed_instances(self, older_than_hours: int = 24) -> int:
        """清理已释放的实例记录"""
        with self._lock:
            cleanup_threshold = timedelta(hours=older_than_hours)
            current_time = datetime.now()
            cleaned_count = 0
            
            for service_type, instances in list(self._tracked_services.items()):
                # 保留未释放的实例和最近释放的实例
                active_instances = [
                    info for info in instances
                    if (not info.is_disposed or 
                        (info.disposal_time and 
                         current_time - info.disposal_time < cleanup_threshold))
                ]
                
                cleaned_count += len(instances) - len(active_instances)
                self._tracked_services[service_type] = active_instances
            
            logger.debug(f"清理了 {cleaned_count} 个已释放的实例记录")
            return cleaned_count
    
    def get_memory_usage_estimate(self) -> Dict[Type, int]:
        """获取内存使用估算"""
        with self._lock:
            memory_usage = {}
            for service_type, instances in self._tracked_services.items():
                total_memory = sum(info.memory_usage for info in instances if not info.is_disposed)
                memory_usage[service_type] = total_memory
            return memory_usage
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        with self._lock:
            for stats in self._service_stats.values():
                stats.total_created = 0
                stats.total_disposed = 0
                stats.current_active = 0
                stats.average_lifetime = timedelta()
                stats.peak_active = 0
                stats.total_access_count = 0
                stats.creation_rate = 0.0
                stats.disposal_rate = 0.0
            
            logger.debug("服务统计信息已重置")
    
    def clear_all_tracking(self) -> None:
        """清除所有追踪信息"""
        with self._lock:
            self._tracked_services.clear()
            self._service_stats.clear()
            self._weak_refs.clear()
            self._start_time = datetime.now()
            
            logger.debug("所有服务追踪信息已清除")
    
    def _find_instance_info(self, service_type: Type, instance: Any) -> Optional[ServiceInstanceInfo]:
        """查找实例信息"""
        instances = self._tracked_services.get(service_type, [])
        for instance_info in instances:
            if instance_info.instance is instance:
                return instance_info
        return None
    
    def _get_creation_stack(self) -> Optional[str]:
        """获取创建堆栈"""
        try:
            import traceback
            stack = traceback.format_stack()
            # 过滤掉内部堆栈帧
            filtered_stack = [
                frame for frame in stack 
                if 'service_tracker.py' not in frame and 'dependency_container' not in frame
            ]
            return ''.join(filtered_stack[-3:]) if filtered_stack else None
        except Exception:
            return None
    
    def _on_instance_collected(self, service_type: Type, weak_ref: weakref.ref) -> None:
        """实例被垃圾回收时的回调"""
        with self._lock:
            # 从弱引用列表中移除
            if service_type in self._weak_refs:
                try:
                    self._weak_refs[service_type].remove(weak_ref)
                except ValueError:
                    pass
            
            # 查找对应的实例信息并标记为已释放
            instances = self._tracked_services.get(service_type, [])
            for instance_info in instances:
                if not instance_info.is_disposed:
                    try:
                        # 检查弱引用是否已失效
                        if weak_ref() is None:
                            instance_info.mark_disposed()
                            
                            # 更新统计信息
                            stats = self._service_stats.get(service_type)
                            if stats:
                                stats.total_disposed += 1
                                stats.current_active -= 1
                            
                            logger.debug(f"服务实例被垃圾回收: {service_type.__name__}")
                            break
                    except Exception as e:
                        logger.error(f"处理垃圾回收回调时发生错误: {e}")
    
    def _cleanup_weak_ref(self, service_type: Type, instance: Any) -> None:
        """清理弱引用"""
        if service_type in self._weak_refs:
            # 移除指向该实例的弱引用
            remaining_refs = []
            for weak_ref in self._weak_refs[service_type]:
                try:
                    if weak_ref() is not instance:
                        remaining_refs.append(weak_ref)
                except Exception:
                    pass
            
            self._weak_refs[service_type] = remaining_refs
    
    def get_summary_report(self) -> Dict[str, Any]:
        """获取摘要报告"""
        with self._lock:
            total_services = len(self._tracked_services)
            total_instances = sum(len(instances) for instances in self._tracked_services.values())
            active_instances = sum(
                len([info for info in instances if not info.is_disposed])
                for instances in self._tracked_services.values()
            )
            
            memory_leaks = self.detect_memory_leaks()
            
            return {
                "total_tracked_services": total_services,
                "total_instances_created": total_instances,
                "currently_active_instances": active_instances,
                "disposed_instances": total_instances - active_instances,
                "memory_leak_count": len(memory_leaks),
                "tracking_duration": datetime.now() - self._start_time,
                "services_with_leaks": [leak.service_type.__name__ for leak in memory_leaks]
            }