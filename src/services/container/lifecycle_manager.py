"""生命周期管理器实现"""

import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional, Callable, Set
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from src.interfaces.container import (
    ILifecycleManager,
    ILifecycleAware,
    ServiceStatus
)

logger = logging.getLogger(__name__)

# 全局生命周期管理器实例
_global_lifecycle_manager: Optional["LifecycleManager"] = None
_global_lifecycle_manager_lock = threading.Lock()


@dataclass
class LifecycleEvent:
    """生命周期事件"""
    service_name: str
    event_type: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None


@dataclass
class ServiceLifecycleInfo:
    """服务生命周期信息"""
    service_name: str
    service_instance: ILifecycleAware
    status: ServiceStatus
    created_at: datetime
    initialized_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    disposed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[str] = None
    
    def mark_initialized(self) -> None:
        """标记已初始化"""
        self.initialized_at = datetime.now()
        self.status = ServiceStatus.INITIALIZED
    
    def mark_started(self) -> None:
        """标记已启动"""
        self.started_at = datetime.now()
        self.status = ServiceStatus.CREATED  # 这里可能需要调整
    
    def mark_stopped(self) -> None:
        """标记已停止"""
        self.stopped_at = datetime.now()
        self.status = ServiceStatus.STOPPED
    
    def mark_disposed(self) -> None:
        """标记已释放"""
        self.disposed_at = datetime.now()
        self.status = ServiceStatus.DISPOSED
    
    def record_error(self, error: str) -> None:
        """记录错误"""
        self.error_count += 1
        self.last_error = error


class LifecycleManager(ILifecycleManager):
    """生命周期管理器实现"""
    
    def __init__(self):
        self._services: Dict[str, ServiceLifecycleInfo] = {}
        self._event_handlers: Dict[str, List[Callable[[str], None]]] = defaultdict(list)
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self._events: List[LifecycleEvent] = []
        self._max_events = 1000  # 最大事件记录数
        
        logger.debug("LifecycleManager初始化完成")
    
    def register_service(self, service_name: str, service_instance: ILifecycleAware, 
                        dependencies: Optional[List[str]] = None) -> None:
        """注册服务"""
        with self._lock:
            if service_name in self._services:
                logger.warning(f"服务已存在，将被覆盖: {service_name}")
            
            # 更新依赖关系
            if dependencies:
                self._dependency_graph[service_name] = set(dependencies)
                for dep in dependencies:
                    self._reverse_dependency_graph[dep].add(service_name)
            
            # 创建服务信息
            service_info = ServiceLifecycleInfo(
                service_name=service_name,
                service_instance=service_instance,
                status=ServiceStatus.REGISTERED,
                created_at=datetime.now(),
                dependencies=dependencies or []
            )
            
            self._services[service_name] = service_info
            
            # 记录事件
            self._record_event(service_name, "registered")
            
            logger.debug(f"注册服务: {service_name}")
    
    async def unregister_service(self, service_name: str) -> None:
        """注销服务"""
        with self._lock:
            if service_name not in self._services:
                logger.warning(f"服务不存在: {service_name}")
                return
            
            # 先释放服务
            try:
                await self.dispose_service(service_name)
            except Exception as e:
                logger.error(f"释放服务 {service_name} 失败: {e}")
            
            # 清理依赖关系
            for dep in self._dependency_graph.get(service_name, set()):
                self._reverse_dependency_graph[dep].discard(service_name)
            
            for dependent in self._reverse_dependency_graph.get(service_name, set()):
                self._dependency_graph[dependent].discard(service_name)
            
            self._dependency_graph.pop(service_name, None)
            self._reverse_dependency_graph.pop(service_name, None)
            
            # 移除服务
            del self._services[service_name]
            
            # 记录事件
            self._record_event(service_name, "unregistered")
            
            logger.debug(f"注销服务: {service_name}")
    
    async def initialize_service(self, service_name: str) -> bool:
        """初始化服务"""
        with self._lock:
            service_info = self._services.get(service_name)
            if not service_info:
                logger.error(f"服务不存在: {service_name}")
                return False
            
            if service_info.status != ServiceStatus.REGISTERED:
                logger.warning(f"服务 {service_name} 状态不正确，无法初始化: {service_info.status}")
                return False
            
            try:
                # 先初始化依赖
                for dep in self._dependency_graph.get(service_name, set()):
                    if not await self.initialize_service(dep):
                        logger.error(f"初始化依赖服务失败: {dep}")
                        return False
                
                # 初始化服务
                logger.debug(f"初始化服务: {service_name}")
                service_info.service_instance.initialize()
                service_info.mark_initialized()
                
                # 触发事件
                self._trigger_event_handlers("initialized", service_name)
                self._record_event(service_name, "initialized")
                
                logger.info(f"服务初始化完成: {service_name}")
                return True
                
            except Exception as e:
                error_msg = f"初始化服务 {service_name} 失败: {e}"
                logger.error(error_msg)
                service_info.record_error(error_msg)
                self._record_event(service_name, "initialize_failed", {"error": str(e)})
                return False
    
    async def start_service(self, service_name: str) -> bool:
        """启动服务"""
        with self._lock:
            service_info = self._services.get(service_name)
            if not service_info:
                logger.error(f"服务不存在: {service_name}")
                return False
            
            if service_info.status not in [ServiceStatus.INITIALIZED, ServiceStatus.STOPPED]:
                logger.warning(f"服务 {service_name} 状态不正确，无法启动: {service_info.status}")
                return False
            
            try:
                # 先启动依赖
                for dep in self._dependency_graph.get(service_name, set()):
                    if not await self.start_service(dep):
                        logger.error(f"启动依赖服务失败: {dep}")
                        return False
                
                # 启动服务
                logger.debug(f"启动服务: {service_name}")
                service_info.service_instance.start()
                service_info.mark_started()
                
                # 触发事件
                self._trigger_event_handlers("started", service_name)
                self._record_event(service_name, "started")
                
                logger.info(f"服务启动完成: {service_name}")
                return True
                
            except Exception as e:
                error_msg = f"启动服务 {service_name} 失败: {e}"
                logger.error(error_msg)
                service_info.record_error(error_msg)
                self._record_event(service_name, "start_failed", {"error": str(e)})
                return False
    
    async def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        with self._lock:
            service_info = self._services.get(service_name)
            if not service_info:
                logger.error(f"服务不存在: {service_name}")
                return False
            
            if service_info.status not in [ServiceStatus.CREATED, ServiceStatus.INITIALIZED]:
                logger.warning(f"服务 {service_name} 状态不正确，无法停止: {service_info.status}")
                return False
            
            try:
                # 先停止依赖此服务的服务
                for dependent in self._reverse_dependency_graph.get(service_name, set()):
                    if not await self.stop_service(dependent):
                        logger.error(f"停止依赖服务失败: {dependent}")
                        return False
                
                # 停止服务
                logger.debug(f"停止服务: {service_name}")
                service_info.service_instance.stop()
                service_info.mark_stopped()
                
                # 触发事件
                self._trigger_event_handlers("stopped", service_name)
                self._record_event(service_name, "stopped")
                
                logger.info(f"服务停止完成: {service_name}")
                return True
                
            except Exception as e:
                error_msg = f"停止服务 {service_name} 失败: {e}"
                logger.error(error_msg)
                service_info.record_error(error_msg)
                self._record_event(service_name, "stop_failed", {"error": str(e)})
                return False
    
    async def dispose_service(self, service_name: str) -> bool:
        """释放服务"""
        with self._lock:
            service_info = self._services.get(service_name)
            if not service_info:
                logger.error(f"服务不存在: {service_name}")
                return False
            
            if service_info.status == ServiceStatus.DISPOSED:
                logger.warning(f"服务已释放: {service_name}")
                return True
            
            try:
                # 先释放依赖此服务的服务
                for dependent in self._reverse_dependency_graph.get(service_name, set()):
                    if not await self.dispose_service(dependent):
                        logger.error(f"释放依赖服务失败: {dependent}")
                        return False
                
                # 释放服务
                logger.debug(f"释放服务: {service_name}")
                service_info.service_instance.dispose()
                service_info.mark_disposed()
                
                # 触发事件
                self._trigger_event_handlers("disposed", service_name)
                self._record_event(service_name, "disposed")
                
                logger.info(f"服务释放完成: {service_name}")
                return True
                
            except Exception as e:
                error_msg = f"释放服务 {service_name} 失败: {e}"
                logger.error(error_msg)
                service_info.record_error(error_msg)
                self._record_event(service_name, "dispose_failed", {"error": str(e)})
                return False
    
    async def initialize_all_services(self) -> Dict[str, bool]:
        """初始化所有服务"""
        results = {}
        
        # 按依赖顺序初始化
        ordered_services = self._get_topological_order()
        
        for service_name in ordered_services:
            results[service_name] = await self.initialize_service(service_name)
        
        return results
    
    async def start_all_services(self) -> Dict[str, bool]:
        """启动所有服务"""
        results = {}
        
        # 按依赖顺序启动
        ordered_services = self._get_topological_order()
        
        for service_name in ordered_services:
            results[service_name] = await self.start_service(service_name)
        
        return results
    
    async def stop_all_services(self) -> Dict[str, bool]:
        """停止所有服务"""
        results = {}
        
        # 按反向依赖顺序停止
        ordered_services = list(reversed(self._get_topological_order()))
        
        for service_name in ordered_services:
            results[service_name] = await self.stop_service(service_name)
        
        return results
    
    async def dispose_all_services(self) -> Dict[str, bool]:
        """释放所有服务"""
        results = {}
        
        # 按反向依赖顺序释放
        ordered_services = list(reversed(self._get_topological_order()))
        
        for service_name in ordered_services:
            results[service_name] = await self.dispose_service(service_name)
        
        return results
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """获取服务状态"""
        with self._lock:
            service_info = self._services.get(service_name)
            return service_info.status if service_info else None
    
    def get_all_service_status(self) -> Dict[str, ServiceStatus]:
        """获取所有服务状态"""
        with self._lock:
            return {name: info.status for name, info in self._services.items()}
    
    def register_lifecycle_event_handler(self, event_type: str, handler: Callable[[str], None]) -> None:
        """注册生命周期事件处理器"""
        with self._lock:
            self._event_handlers[event_type].append(handler)
            logger.debug(f"注册事件处理器: {event_type}")
    
    def unregister_lifecycle_event_handler(self, event_type: str, handler: Callable[[str], None]) -> bool:
        """注销生命周期事件处理器"""
        with self._lock:
            if event_type in self._event_handlers:
                try:
                    self._event_handlers[event_type].remove(handler)
                    logger.debug(f"注销事件处理器: {event_type}")
                    return True
                except ValueError:
                    logger.warning(f"事件处理器不存在: {event_type}")
                    return False
            return False
    
    def get_service_info(self, service_name: str) -> Optional[ServiceLifecycleInfo]:
        """获取服务详细信息"""
        with self._lock:
            service_info = self._services.get(service_name)
            if service_info:
                # 返回副本以避免外部修改
                return ServiceLifecycleInfo(
                    service_name=service_info.service_name,
                    service_instance=service_info.service_instance,
                    status=service_info.status,
                    created_at=service_info.created_at,
                    initialized_at=service_info.initialized_at,
                    started_at=service_info.started_at,
                    stopped_at=service_info.stopped_at,
                    disposed_at=service_info.disposed_at,
                    dependencies=service_info.dependencies.copy(),
                    dependents=service_info.dependents.copy(),
                    error_count=service_info.error_count,
                    last_error=service_info.last_error
                )
            return None
    
    def get_recent_events(self, limit: int = 100) -> List[LifecycleEvent]:
        """获取最近的事件"""
        with self._lock:
            return self._events[-limit:] if limit > 0 else self._events.copy()
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖图"""
        with self._lock:
            return {k: list(v) for k, v in self._dependency_graph.items()}
    
    def get_services_by_status(self, status: ServiceStatus) -> List[str]:
        """根据状态获取服务列表"""
        with self._lock:
            return [name for name, info in self._services.items() if info.status == status]
    
    def get_error_summary(self) -> Dict[str, Dict[str, Any]]:
        """获取错误摘要"""
        with self._lock:
            error_summary = {}
            for name, info in self._services.items():
                if info.error_count > 0:
                    error_summary[name] = {
                        "error_count": info.error_count,
                        "last_error": info.last_error,
                        "status": info.status
                    }
            return error_summary
    
    def _trigger_event_handlers(self, event_type: str, service_name: str) -> None:
        """触发事件处理器"""
        for handler in self._event_handlers.get(event_type, []):
            try:
                handler(service_name)
            except Exception as e:
                logger.error(f"执行事件处理器失败: {e}")
    
    def _record_event(self, service_name: str, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """记录事件"""
        event = LifecycleEvent(
            service_name=service_name,
            event_type=event_type,
            timestamp=datetime.now(),
            data=data
        )
        
        self._events.append(event)
        
        # 限制事件数量
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
    
    def _get_topological_order(self) -> List[str]:
        """获取拓扑排序顺序"""
        # Kahn算法
        in_degree = defaultdict(int)
        all_services = set(self._services.keys())
        
        # 计算入度
        for service in all_services:
            in_degree[service] = 0
        
        for service, deps in self._dependency_graph.items():
            for dep in deps:
                in_degree[service] += 1
        
        # 找到入度为0的节点
        from collections import deque
        queue = deque([service for service in all_services if in_degree[service] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in self._reverse_dependency_graph.get(current, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有循环依赖
        if len(result) != len(all_services):
            logger.warning("存在循环依赖，无法完成拓扑排序")
        
        return result
    
    def clear_events(self) -> None:
        """清除事件记录"""
        with self._lock:
            self._events.clear()
            logger.debug("事件记录已清除")
    
    def get_lifecycle_statistics(self) -> Dict[str, Any]:
        """获取生命周期统计信息"""
        with self._lock:
            status_counts = defaultdict(int)
            total_errors = 0
            
            for info in self._services.values():
                status_counts[info.status] += 1
                total_errors += info.error_count
            
            return {
                "total_services": len(self._services),
                "status_distribution": dict(status_counts),
                "total_errors": total_errors,
                "recent_events_count": len(self._events),
                "dependency_edges": sum(len(deps) for deps in self._dependency_graph.values())
            }
    
    async def execute_lifecycle_phase(
        self, 
        phase: str, 
        service_names: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """执行生命周期阶段"""
        results: Dict[str, bool] = {}
        
        # 如果未指定服务名称，使用所有服务
        target_services = service_names if service_names else list(self._services.keys())
        
        # 获取排序顺序（对于停止和释放，需要反向）
        if phase in ["stop", "dispose"]:
            ordered_services = list(reversed(self._get_topological_order()))
            # 只保留目标服务
            ordered_services = [s for s in ordered_services if s in target_services]
        else:
            ordered_services = self._get_topological_order()
            # 只保留目标服务
            ordered_services = [s for s in ordered_services if s in target_services]
        
        # 执行对应的生命周期方法
        if phase == "initialize":
            for service_name in ordered_services:
                results[service_name] = await self.initialize_service(service_name)
        elif phase == "start":
            for service_name in ordered_services:
                results[service_name] = await self.start_service(service_name)
        elif phase == "stop":
            for service_name in ordered_services:
                results[service_name] = await self.stop_service(service_name)
        elif phase == "dispose":
            for service_name in ordered_services:
                results[service_name] = await self.dispose_service(service_name)
        else:
            logger.error(f"无效的生命周期阶段: {phase}")
        
        return results
    
    def get_dependency_order(self, service_names: Optional[List[str]] = None) -> List[str]:
        """获取服务依赖顺序"""
        if service_names:
            # 只返回指定服务的依赖顺序
            ordered = self._get_topological_order()
            return [s for s in ordered if s in service_names]
        else:
            # 返回所有服务的依赖顺序
            return self._get_topological_order()


def get_global_lifecycle_manager() -> LifecycleManager:
    """获取全局生命周期管理器实例（单例模式）"""
    global _global_lifecycle_manager
    
    if _global_lifecycle_manager is None:
        with _global_lifecycle_manager_lock:
            if _global_lifecycle_manager is None:
                _global_lifecycle_manager = LifecycleManager()
                logger.debug("创建全局LifecycleManager实例")
    
    return _global_lifecycle_manager