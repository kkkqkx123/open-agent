"""依赖注入容器相关接口定义"""

import threading
import time
import logging
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable, Union, ContextManager
from enum import Enum
from dataclasses import dataclass
from contextlib import contextmanager

from ..infrastructure.infrastructure_types import ServiceRegistration, ServiceLifetime, T

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    REGISTERED = "registered"
    CREATING = "creating"
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STOPPED = "stopped"
    DISPOSING = "disposing"
    DISPOSED = "disposed"


class ILifecycleAware(ABC):
    """生命周期感知接口"""

    @abstractmethod
    def initialize(self) -> None:
        """初始化服务"""
        pass

    def start(self) -> None:
        """启动服务（可选）"""
        pass

    def stop(self) -> None:
        """停止服务（可选）"""
        pass

    @abstractmethod
    def dispose(self) -> None:
        """释放服务资源"""
        pass


class IServiceTracker(ABC):
    """服务跟踪器接口"""
    
    @abstractmethod
    def track_creation(self, service_type: Type, instance: Any) -> None:
        """跟踪服务创建"""
        pass
    
    @abstractmethod
    def track_disposal(self, service_type: Type, instance: Any) -> None:
        """跟踪服务释放"""
        pass
    
    @abstractmethod
    def get_tracked_services(self) -> Dict[Type, List[Any]]:
        """获取跟踪的服务"""
        pass


class IServiceCache(ABC):
    """服务缓存接口"""
    
    @abstractmethod
    def get(self, service_type: Type) -> Optional[Any]:
        """从缓存获取服务实例"""
        pass
    
    @abstractmethod
    def put(self, service_type: Type, instance: Any) -> None:
        """将服务实例放入缓存"""
        pass
    
    @abstractmethod
    def remove(self, service_type: Type) -> None:
        """从缓存移除服务实例"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有缓存"""
        pass
    
    @abstractmethod
    def optimize(self) -> Dict[str, Any]:
        """优化缓存"""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """获取缓存大小"""
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> int:
        """获取内存使用量"""
        pass


class IPerformanceMonitor(ABC):
    """性能监控接口"""
    
    @abstractmethod
    def record_resolution(self, service_type: Type, start_time: float, end_time: float) -> None:
        """记录服务解析"""
        pass
    
    @abstractmethod
    def record_cache_hit(self, service_type: Type) -> None:
        """记录缓存命中"""
        pass
    
    @abstractmethod
    def record_cache_miss(self, service_type: Type) -> None:
        """记录缓存未命中"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass


class IDependencyAnalyzer(ABC):
    """依赖分析接口"""
    
    @abstractmethod
    def add_dependency(self, service_type: Type, dependency_type: Type) -> None:
        """添加依赖关系"""
        pass
    
    @abstractmethod
    def get_dependencies(self, service_type: Type) -> Set[Type]:
        """获取服务的依赖"""
        pass
    
    @abstractmethod
    def detect_circular_dependencies(self) -> List[List[Type]]:
        """检测循环依赖"""
        pass
    
    @abstractmethod
    def calculate_dependency_depth(self, service_type: Type) -> int:
        """计算依赖深度"""
        pass
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """分析依赖关系"""
        pass
    
    @abstractmethod
    def update_from_implementation(self, interface: Type, implementation: Type) -> None:
        """从实现类更新依赖关系"""
        pass


class IScopeManager(ABC):
    """作用域管理接口"""
    
    @abstractmethod
    def create_scope(self) -> str:
        """创建新作用域"""
        pass
    
    @abstractmethod
    def dispose_scope(self, scope_id: str) -> None:
        """释放作用域"""
        pass
    
    @abstractmethod
    def get_current_scope_id(self) -> Optional[str]:
        """获取当前作用域ID"""
        pass
    
    @abstractmethod
    def set_current_scope_id(self, scope_id: Optional[str]) -> None:
        """设置当前作用域ID"""
        pass
    
    @abstractmethod
    def get_scoped_instance(self, scope_id: str, service_type: Type) -> Optional[Any]:
        """获取作用域内的服务实例"""
        pass
    
    @abstractmethod
    def set_scoped_instance(self, scope_id: str, service_type: Type, instance: Any) -> None:
        """设置作用域内的服务实例"""
        pass
    
    @abstractmethod
    def scope_context(self) -> ContextManager[str]:
        """作用域上下文管理器"""
        pass


class IDependencyContainer(ABC):
    """依赖注入容器接口"""

    @abstractmethod
    def register(
        self,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务实现"""
        pass

    @abstractmethod
    def register_factory(
        self,
        interface: Type,
        factory: Callable[[], Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """注册服务工厂"""
        pass

    @abstractmethod
    def register_instance(
        self, interface: Type, instance: Any, environment: str = "default"
    ) -> None:
        """注册服务实例"""
        pass

    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        pass

    @abstractmethod
    def get_environment(self) -> str:
        """获取当前环境"""
        pass

    @abstractmethod
    def set_environment(self, env: str) -> None:
        """设置当前环境"""
        pass

    @abstractmethod
    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清除所有服务和缓存"""
        pass