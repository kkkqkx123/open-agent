"""简化的服务生命周期管理器

提供统一的服务生命周期管理，优化服务创建和销毁逻辑。
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable, Set
from enum import Enum
from contextlib import contextmanager
from dataclasses import dataclass

from src.interfaces.container import ILifecycleAware, ServiceStatus

logger = logging.getLogger(__name__)


class LifecycleEvent(Enum):
    """生命周期事件枚举"""
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    STARTED = "started"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DISPOSING = "disposing"
    DISPOSED = "disposed"


@dataclass
class LifecycleEventInfo:
    """生命周期事件信息"""
    event: LifecycleEvent
    service_type: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None


class LifecycleManager:
    """简化的生命周期管理器
    
    负责管理所有服务的生命周期，包括初始化、启动、停止和销毁。
    """
    
    def __init__(self):
        """初始化生命周期管理器"""
        self._services: Dict[str, ILifecycleAware] = {}
        self._service_status: Dict[str, ServiceStatus] = {}
        self._event_listeners: Dict[LifecycleEvent, List[Callable]] = {}
        self._lock = threading.RLock()
        self._disposed = False
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        
        logger.debug("LifecycleManager初始化完成")
    
    def register_service(self, name: str, service: ILifecycleAware) -> None:
        """注册服务
        
        Args:
            name: 服务名称
            service: 服务实例
        """
        with self._lock:
            if self._disposed:
                raise RuntimeError("生命周期管理器已释放，无法注册服务")
            
            self._services[name] = service
            self._service_status[name] = ServiceStatus.REGISTERED
            logger.debug(f"服务注册: {name}")
    
    def unregister_service(self, name: str) -> None:
        """注销服务
        
        Args:
            name: 服务名称
        """
        with self._lock:
            if name in self._services:
                # 先停止并释放服务
                self._stop_service(name)
                self._dispose_service(name)
                
                # 移除服务
                del self._services[name]
                del self._service_status[name]
                
                # 从启动和关闭顺序中移除
                if name in self._startup_order:
                    self._startup_order.remove(name)
                if name in self._shutdown_order:
                    self._shutdown_order.remove(name)
                
                logger.debug(f"服务注销: {name}")
    
    def initialize_service(self, name: str) -> bool:
        """初始化服务
        
        Args:
            name: 服务名称
            
        Returns:
            bool: 是否成功初始化
        """
        with self._lock:
            if name not in self._services:
                logger.warning(f"服务不存在: {name}")
                return False
            
            if self._service_status[name] != ServiceStatus.REGISTERED:
                logger.debug(f"服务 {name} 已初始化或正在初始化")
                return True
            
            service = self._services[name]
            
            try:
                # 触发初始化前事件
                self._trigger_event(LifecycleEvent.INITIALIZING, name)
                
                # 初始化服务
                self._service_status[name] = ServiceStatus.INITIALIZING
                service.initialize()
                
                # 更新状态
                self._service_status[name] = ServiceStatus.INITIALIZED
                
                # 添加到启动顺序
                if name not in self._startup_order:
                    self._startup_order.append(name)
                
                # 触发初始化完成事件
                self._trigger_event(LifecycleEvent.INITIALIZED, name)
                
                logger.debug(f"服务初始化完成: {name}")
                return True
                
            except Exception as e:
                self._service_status[name] = ServiceStatus.DISPOSED
                logger.error(f"服务初始化失败: {name}, 错误: {e}")
                return False
    
    def start_service(self, name: str) -> bool:
        """启动服务
        
        Args:
            name: 服务名称
            
        Returns:
            bool: 是否成功启动
        """
        with self._lock:
            if name not in self._services:
                logger.warning(f"服务不存在: {name}")
                return False
            
            # 确保服务已初始化
            if self._service_status[name] == ServiceStatus.REGISTERED:
                if not self.initialize_service(name):
                    return False
            
            if self._service_status[name] not in [ServiceStatus.INITIALIZED, ServiceStatus.STOPPED]:
                logger.debug(f"服务 {name} 已启动或正在启动")
                return True
            
            service = self._services[name]
            
            try:
                # 触发启动前事件
                self._trigger_event(LifecycleEvent.STARTING, name)
                
                # 启动服务（如果服务有start方法）
                if hasattr(service, 'start'):
                    self._service_status[name] = ServiceStatus.CREATING  # 临时状态
                    service.start()
                
                # 更新状态
                self._service_status[name] = ServiceStatus.CREATED  # 使用CREATED表示运行中
                
                # 添加到关闭顺序
                if name not in self._shutdown_order:
                    self._shutdown_order.insert(0, name)  # 添加到开头，后进先出
                
                # 触发启动完成事件
                self._trigger_event(LifecycleEvent.STARTED, name)
                
                logger.debug(f"服务启动完成: {name}")
                return True
                
            except Exception as e:
                self._service_status[name] = ServiceStatus.DISPOSED
                logger.error(f"服务启动失败: {name}, 错误: {e}")
                return False
    
    def stop_service(self, name: str) -> bool:
        """停止服务
        
        Args:
            name: 服务名称
            
        Returns:
            bool: 是否成功停止
        """
        with self._lock:
            return self._stop_service(name)
    
    def _stop_service(self, name: str) -> bool:
        """内部停止服务方法
        
        Args:
            name: 服务名称
            
        Returns:
            bool: 是否成功停止
        """
        if name not in self._services:
            logger.warning(f"服务不存在: {name}")
            return False
        
        if self._service_status[name] != ServiceStatus.CREATED:
            logger.debug(f"服务 {name} 未运行")
            return True
        
        service = self._services[name]
        
        try:
            # 触发停止前事件
            self._trigger_event(LifecycleEvent.STOPPING, name)
            
            # 停止服务（如果服务有stop方法）
            if hasattr(service, 'stop'):
                service.stop()
            
            # 更新状态
            self._service_status[name] = ServiceStatus.STOPPED
            
            # 触发停止完成事件
            self._trigger_event(LifecycleEvent.STOPPED, name)
            
            logger.debug(f"服务停止完成: {name}")
            return True
            
        except Exception as e:
            logger.error(f"服务停止失败: {name}, 错误: {e}")
            return False
    
    def dispose_service(self, name: str) -> bool:
        """释放服务
        
        Args:
            name: 服务名称
            
        Returns:
            bool: 是否成功释放
        """
        with self._lock:
            return self._dispose_service(name)
    
    def _dispose_service(self, name: str) -> bool:
        """内部释放服务方法
        
        Args:
            name: 服务名称
            
        Returns:
            bool: 是否成功释放
        """
        if name not in self._services:
            logger.warning(f"服务不存在: {name}")
            return False
        
        service = self._services[name]
        
        try:
            # 先停止服务
            if self._service_status[name] == ServiceStatus.CREATED:
                self._stop_service(name)
            
            # 触发释放前事件
            self._trigger_event(LifecycleEvent.DISPOSING, name)
            
            # 释放服务
            self._service_status[name] = ServiceStatus.DISPOSING
            service.dispose()
            
            # 更新状态
            self._service_status[name] = ServiceStatus.DISPOSED
            
            # 触发释放完成事件
            self._trigger_event(LifecycleEvent.DISPOSED, name)
            
            logger.debug(f"服务释放完成: {name}")
            return True
            
        except Exception as e:
            logger.error(f"服务释放失败: {name}, 错误: {e}")
            return False
    
    def initialize_all_services(self) -> Dict[str, bool]:
        """初始化所有服务
        
        Returns:
            Dict[str, bool]: 服务名称到初始化结果的映射
        """
        results = {}
        for name in self._services:
            results[name] = self.initialize_service(name)
        return results
    
    def start_all_services(self) -> Dict[str, bool]:
        """启动所有服务
        
        Returns:
            Dict[str, bool]: 服务名称到启动结果的映射
        """
        results = {}
        for name in self._startup_order:
            results[name] = self.start_service(name)
        return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """停止所有服务
        
        Returns:
            Dict[str, bool]: 服务名称到停止结果的映射
        """
        results = {}
        for name in self._shutdown_order:
            results[name] = self.stop_service(name)
        return results
    
    def dispose_all_services(self) -> Dict[str, bool]:
        """释放所有服务
        
        Returns:
            Dict[str, bool]: 服务名称到释放结果的映射
        """
        results = {}
        for name in self._shutdown_order:
            results[name] = self.dispose_service(name)
        return results
    
    def get_service_status(self, name: str) -> Optional[ServiceStatus]:
        """获取服务状态
        
        Args:
            name: 服务名称
            
        Returns:
            服务状态，如果服务不存在则返回None
        """
        return self._service_status.get(name)
    
    def get_all_services_status(self) -> Dict[str, ServiceStatus]:
        """获取所有服务状态
        
        Returns:
            所有服务的状态
        """
        return self._service_status.copy()
    
    def add_event_listener(self, event: LifecycleEvent, listener: Callable[[LifecycleEventInfo], None]) -> None:
        """添加事件监听器
        
        Args:
            event: 生命周期事件
            listener: 监听器函数
        """
        with self._lock:
            if event not in self._event_listeners:
                self._event_listeners[event] = []
            self._event_listeners[event].append(listener)
    
    def remove_event_listener(self, event: LifecycleEvent, listener: Callable[[LifecycleEventInfo], None]) -> None:
        """移除事件监听器
        
        Args:
            event: 生命周期事件
            listener: 监听器函数
        """
        with self._lock:
            if event in self._event_listeners:
                try:
                    self._event_listeners[event].remove(listener)
                except ValueError:
                    pass  # 监听器不存在
    
    def _trigger_event(self, event: LifecycleEvent, service_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        """触发事件
        
        Args:
            event: 生命周期事件
            service_name: 服务名称
            details: 事件详情
        """
        if event not in self._event_listeners:
            return
        
        event_info = LifecycleEventInfo(
            event=event,
            service_type=service_name,
            timestamp=time.time(),
            details=details
        )
        
        for listener in self._event_listeners[event]:
            try:
                listener(event_info)
            except Exception as e:
                logger.error(f"事件监听器执行失败: {e}")
    
    def dispose(self) -> None:
        """释放生命周期管理器"""
        with self._lock:
            if self._disposed:
                return
            
            self._disposed = True
            
            # 停止并释放所有服务
            self.stop_all_services()
            self.dispose_all_services()
            
            # 清理资源
            self._services.clear()
            self._service_status.clear()
            self._event_listeners.clear()
            self._startup_order.clear()
            self._shutdown_order.clear()
            
            logger.debug("LifecycleManager已释放")
    
    @contextmanager
    def service_scope(self, service_names: List[str]):
        """服务作用域上下文管理器
        
        Args:
            service_names: 要启动的服务名称列表
        """
        # 启动指定服务
        started_services = []
        try:
            for name in service_names:
                if self.start_service(name):
                    started_services.append(name)
            
            yield
            
        finally:
            # 停止已启动的服务
            for name in reversed(started_services):
                self.stop_service(name)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取生命周期管理器指标
        
        Returns:
            指标信息
        """
        with self._lock:
            status_counts = {}
            for status in ServiceStatus:
                status_counts[status.value] = sum(
                    1 for s in self._service_status.values() if s == status
                )
            
            return {
                "total_services": len(self._services),
                "status_distribution": status_counts,
                "startup_order": self._startup_order.copy(),
                "shutdown_order": self._shutdown_order.copy(),
                "disposed": self._disposed
            }


# 全局生命周期管理器实例
_global_lifecycle_manager: Optional[LifecycleManager] = None


def get_global_lifecycle_manager() -> LifecycleManager:
    """获取全局生命周期管理器
    
    Returns:
        全局生命周期管理器实例
    """
    global _global_lifecycle_manager
    if _global_lifecycle_manager is None:
        _global_lifecycle_manager = LifecycleManager()
    return _global_lifecycle_manager


def reset_global_lifecycle_manager() -> None:
    """重置全局生命周期管理器"""
    global _global_lifecycle_manager
    if _global_lifecycle_manager:
        _global_lifecycle_manager.dispose()
    _global_lifecycle_manager = None