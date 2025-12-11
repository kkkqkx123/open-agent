"""管理器注册表

统一管理所有管理器实例，提供标准化的管理器接口和通信机制。
"""

from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from src.interfaces.dependency_injection import get_logger
from dataclasses import dataclass
from datetime import datetime

logger = get_logger(__name__)


class ManagerStatus(Enum):
    """管理器状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class ManagerInfo:
    """管理器信息"""
    name: str
    manager_class: str
    status: ManagerStatus
    instance: Any
    dependencies: List[str]
    dependents: List[str]
    created_at: datetime
    last_updated: datetime
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ManagerRegistry:
    """管理器注册表
    
    负责：
    1. 管理器实例的注册和获取
    2. 管理器依赖关系的管理
    3. 管理器状态跟踪
    4. 管理器间通信接口
    """
    
    def __init__(self):
        """初始化管理器注册表"""
        self._managers: Dict[str, ManagerInfo] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._communication_handlers: Dict[str, Dict[str, Callable]] = {}
    
    def register_manager(
        self, 
        name: str, 
        manager_instance: Any, 
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册管理器实例
        
        Args:
            name: 管理器名称
            manager_instance: 管理器实例
            dependencies: 依赖的管理器列表
            metadata: 元数据
        """
        if name in self._managers:
            logger.warning(f"管理器 {name} 已存在，将被覆盖")
        
        manager_info = ManagerInfo(
            name=name,
            manager_class=manager_instance.__class__.__name__,
            status=ManagerStatus.UNINITIALIZED,
            instance=manager_instance,
            dependencies=dependencies or [],
            dependents=[],
            created_at=datetime.now(),
            last_updated=datetime.now(),
            metadata=metadata
        )
        
        self._managers[name] = manager_info
        
        # 更新依赖关系
        self._update_dependencies(name, dependencies or [])
        
        logger.info(f"注册管理器: {name} ({manager_instance.__class__.__name__})")
        
        # 触发注册事件
        self._trigger_event("manager_registered", name, manager_info)
    
    def unregister_manager(self, name: str) -> bool:
        """
        注销管理器
        
        Args:
            name: 管理器名称
            
        Returns:
            是否成功注销
        """
        if name not in self._managers:
            return False
        
        # 检查是否有依赖此管理器的其他管理器
        manager_info = self._managers[name]
        if manager_info.dependents:
            logger.warning(f"管理器 {name} 仍被其他管理器依赖: {manager_info.dependents}")
            return False
        
        # 清理依赖关系
        self._cleanup_dependencies(name)
        
        # 移除管理器
        del self._managers[name]
        
        # 清理通信处理器
        if name in self._communication_handlers:
            del self._communication_handlers[name]
        
        logger.info(f"注销管理器: {name}")
        
        # 触发注销事件
        self._trigger_event("manager_unregistered", name)
        
        return True
    
    def get_manager(self, name: str) -> Optional[Any]:
        """
        获取管理器实例
        
        Args:
            name: 管理器名称
            
        Returns:
            管理器实例，如果不存在则返回None
        """
        manager_info = self._managers.get(name)
        return manager_info.instance if manager_info else None
    
    def get_manager_info(self, name: str) -> Optional[ManagerInfo]:
        """
        获取管理器信息
        
        Args:
            name: 管理器名称
            
        Returns:
            管理器信息，如果不存在则返回None
        """
        return self._managers.get(name)
    
    def list_managers(self) -> List[str]:
        """
        列出所有已注册的管理器名称
        
        Returns:
            管理器名称列表
        """
        return list(self._managers.keys())
    
    def get_managers_by_status(self, status: ManagerStatus) -> List[str]:
        """
        根据状态获取管理器列表
        
        Args:
            status: 管理器状态
            
        Returns:
            符合状态的管理器名称列表
        """
        return [
            name for name, info in self._managers.items() 
            if info.status == status
        ]
    
    def update_manager_status(self, name: str, status: ManagerStatus, error_message: Optional[str] = None) -> None:
        """
        更新管理器状态
        
        Args:
            name: 管理器名称
            status: 新状态
            error_message: 错误消息（可选）
        """
        if name not in self._managers:
            logger.warning(f"管理器 {name} 不存在，无法更新状态")
            return
        
        old_status = self._managers[name].status
        self._managers[name].status = status
        self._managers[name].last_updated = datetime.now()
        self._managers[name].error_message = error_message
        
        logger.info(f"管理器 {name} 状态更新: {old_status.value} -> {status.value}")
        
        # 触发状态变更事件
        self._trigger_event("manager_status_changed", name, old_status, status)
    
    def register_communication_handler(self, manager_name: str, event: str, handler: Callable) -> None:
        """
        注册通信处理器
        
        Args:
            manager_name: 管理器名称
            event: 事件名称
            handler: 处理器函数
        """
        if manager_name not in self._communication_handlers:
            self._communication_handlers[manager_name] = {}
        
        self._communication_handlers[manager_name][event] = handler
        logger.debug(f"注册通信处理器: {manager_name}.{event}")
    
    def send_message(self, from_manager: str, to_manager: str, event: str, data: Any) -> bool:
        """
        发送消息到指定管理器
        
        Args:
            from_manager: 发送方管理器名称
            to_manager: 接收方管理器名称
            event: 事件名称
            data: 消息数据
            
        Returns:
            是否成功发送
        """
        if to_manager not in self._communication_handlers:
            logger.warning(f"管理器 {to_manager} 没有注册通信处理器")
            return False
        
        if event not in self._communication_handlers[to_manager]:
            logger.warning(f"管理器 {to_manager} 没有注册 {event} 事件处理器")
            return False
        
        try:
            handler = self._communication_handlers[to_manager][event]
            handler(from_manager, data)
            logger.debug(f"消息发送成功: {from_manager} -> {to_manager}.{event}")
            return True
        except Exception as e:
            logger.error(f"消息发送失败: {from_manager} -> {to_manager}.{event}: {e}")
            return False
    
    def broadcast_message(self, from_manager: str, event: str, data: Any) -> int:
        """
        广播消息到所有管理器
        
        Args:
            from_manager: 发送方管理器名称
            event: 事件名称
            data: 消息数据
            
        Returns:
            成功发送的管理器数量
        """
        success_count = 0
        for manager_name in self._managers:
            if manager_name != from_manager:
                if self.send_message(from_manager, manager_name, event, data):
                    success_count += 1
        
        logger.debug(f"广播消息完成: {from_manager} -> {success_count}/{len(self._managers)-1} 个管理器")
        return success_count
    
    def register_event_handler(self, event: str, handler: Callable) -> None:
        """
        注册全局事件处理器
        
        Args:
            event: 事件名称
            handler: 处理器函数
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        
        self._event_handlers[event].append(handler)
        logger.debug(f"注册全局事件处理器: {event}")
    
    def get_registry_status(self) -> Dict[str, Any]:
        """
        获取注册表状态
        
        Returns:
            注册表状态信息
        """
        status_counts = {}
        for status in ManagerStatus:
            status_counts[status.value] = len(self.get_managers_by_status(status))
        
        return {
            "total_managers": len(self._managers),
            "status_counts": status_counts,
            "managers": {
                name: {
                    "class": info.manager_class,
                    "status": info.status.value,
                    "dependencies": info.dependencies,
                    "dependents": info.dependents,
                    "created_at": info.created_at.isoformat(),
                    "last_updated": info.last_updated.isoformat(),
                    "has_error": info.error_message is not None
                }
                for name, info in self._managers.items()
            }
        }
    
    def _update_dependencies(self, name: str, dependencies: List[str]) -> None:
        """更新依赖关系"""
        for dep_name in dependencies:
            if dep_name in self._managers:
                if name not in self._managers[dep_name].dependents:
                    self._managers[dep_name].dependents.append(name)
    
    def _cleanup_dependencies(self, name: str) -> None:
        """清理依赖关系"""
        manager_info = self._managers.get(name)
        if not manager_info:
            return
        
        # 从依赖的管理器中移除当前管理器
        for dep_name in manager_info.dependencies:
            if dep_name in self._managers:
                if name in self._managers[dep_name].dependents:
                    self._managers[dep_name].dependents.remove(name)
    
    def _trigger_event(self, event: str, *args, **kwargs) -> None:
        """触发事件"""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {event}: {e}")


# 全局管理器注册表实例
manager_registry = ManagerRegistry()