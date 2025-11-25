"""依赖注入容器相关接口定义"""

import threading
import time
import logging
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable, Union, ContextManager, overload, ClassVar, Tuple
from enum import Enum
from dataclasses import dataclass
from contextlib import contextmanager

from .common import ServiceLifetime
from .configuration import ValidationResult

# 泛型类型变量用于 get 方法
_ServiceT = TypeVar("_ServiceT")

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
    
    def __init__(self) -> None:
        self._initialized: bool = False

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
    def get(self, service_type: Type[_ServiceT]) -> _ServiceT:
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


# 新增高级注册接口
class IEnhancedDependencyContainer(IDependencyContainer):
    """增强依赖注入容器接口"""
    
    @abstractmethod
    def register_conditional(
        self,
        interface: Type,
        condition: Callable[[], bool],
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """条件注册服务实现"""
        pass
    
    @abstractmethod
    def register_named(
        self,
        name: str,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """命名注册服务实现"""
        pass
    
    @abstractmethod
    def register_with_metadata(
        self,
        interface: Type,
        implementation: Type,
        metadata: Dict[str, Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """带元数据注册服务实现"""
        pass
    
    @abstractmethod
    def register_decorator(
        self,
        interface: Type,
        decorator: Callable[[Any], Any],
        environment: str = "default",
    ) -> None:
        """注册服务装饰器"""
        pass
    
    @abstractmethod
    def get_all(self, interface: Type) -> List[Any]:
        """获取接口的所有实现"""
        pass
    
    @abstractmethod
    def get_named(self, interface: Type, name: str) -> Any:
        """按名称获取服务实例"""
        pass
    
    @abstractmethod
    def try_get(self, service_type: Type[_ServiceT]) -> Optional[_ServiceT]:
        """尝试获取服务实例，不抛异常"""
        pass
    
    @abstractmethod
    def get_with_metadata(self, service_type: Type[_ServiceT]) -> Tuple[_ServiceT, Dict[str, Any]]:
        """获取服务实例及其元数据"""
        pass
    
    @abstractmethod
    def get_lazy(self, service_type: Type[_ServiceT]) -> Callable[[], _ServiceT]:
        """获取懒加载服务代理"""
        pass
    
    @abstractmethod
    def prewarm_services(self, service_types: List[Type]) -> None:
        """预热服务"""
        pass
    
    @abstractmethod
    def analyze_dependencies(self) -> 'DependencyAnalysisResult':
        """分析依赖关系"""
        pass
    
    @abstractmethod
    def get_service_metrics(self) -> 'ServiceMetrics':
        """获取服务指标"""
        pass
    
    @abstractmethod
    def optimize_configuration(self) -> 'OptimizationSuggestions':
        """优化配置建议"""
        pass


# 新增数据类和枚举
@dataclass
class CircularDependency:
    """循环依赖信息"""
    dependency_chain: List[Type]
    description: str


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    service_type: Type
    suggestion_type: str
    description: str
    impact: str


@dataclass
class OptimizationSuggestions:
    """优化建议集合"""
    suggestions: List[OptimizationSuggestion]
    total_impact_score: int
    
    def get_high_priority_suggestions(self) -> List[OptimizationSuggestion]:
        """获取高优先级建议"""
        return [s for s in self.suggestions if s.impact == "high"]


@dataclass
class ServiceMetrics:
    """服务指标"""
    total_services: int
    singleton_count: int
    transient_count: int
    scoped_count: int
    average_resolution_time: float
    cache_hit_rate: float
    memory_usage: int


@dataclass
class DependencyAnalysisResult:
    """依赖分析结果"""
    dependency_graph: Dict[Type, Set[Type]]
    circular_dependencies: List[CircularDependency]
    max_dependency_depth: int
    orphaned_services: List[Type]
    
    def has_circular_dependencies(self) -> bool:
        return len(self.circular_dependencies) > 0


# 新增插件接口
class IContainerPlugin(ABC):
    """容器插件接口"""
    
    @abstractmethod
    def initialize(self, container: IDependencyContainer) -> None:
        """初始化插件"""
        pass
    
    @abstractmethod
    def get_plugin_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_plugin_version(self) -> str:
        """获取插件版本"""
        pass
    
    def cleanup(self) -> None:
        """清理插件资源"""
        pass
    
    def get_plugin_priority(self) -> int:
        """获取插件优先级"""
        return 0


class IPluginManager(ABC):
    """插件管理器接口"""
    
    @abstractmethod
    def register_plugin(self, plugin: IContainerPlugin) -> None:
        """注册插件"""
        pass
    
    @abstractmethod
    def unregister_plugin(self, plugin_name: str) -> None:
        """注销插件"""
        pass
    
    @abstractmethod
    def load_plugins_from_directory(self, plugin_dir: str) -> None:
        """从目录加载插件"""
        pass
    
    @abstractmethod
    def get_loaded_plugins(self) -> List[IContainerPlugin]:
        """获取已加载的插件"""
        pass
    
    @abstractmethod
    def initialize_plugins(self, container: IDependencyContainer) -> None:
        """初始化所有插件"""
        pass


# 新增生命周期管理器接口
class ILifecycleManager(ABC):
    """生命周期管理器接口"""
    
    @abstractmethod
    def initialize_service(self, service_name: str) -> bool:
        """初始化服务"""
        pass
    
    @abstractmethod
    def start_service(self, service_name: str) -> bool:
        """启动服务"""
        pass
    
    @abstractmethod
    def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        pass
    
    @abstractmethod
    def dispose_service(self, service_name: str) -> bool:
        """释放服务"""
        pass
    
    @abstractmethod
    def initialize_all_services(self) -> Dict[str, bool]:
        """初始化所有服务"""
        pass
    
    @abstractmethod
    def start_all_services(self) -> Dict[str, bool]:
        """启动所有服务"""
        pass
    
    @abstractmethod
    def stop_all_services(self) -> Dict[str, bool]:
        """停止所有服务"""
        pass
    
    @abstractmethod
    def dispose_all_services(self) -> Dict[str, bool]:
        """释放所有服务"""
        pass
    
    @abstractmethod
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """获取服务状态"""
        pass
    
    @abstractmethod
    def get_all_service_status(self) -> Dict[str, ServiceStatus]:
        """获取所有服务状态"""
        pass
    
    @abstractmethod
    def register_lifecycle_event_handler(self, event_type: str, handler: Callable[[str], None]) -> None:
        """注册生命周期事件处理器"""
        pass


# 新增配置集成接口
class IConfigurationAwareContainer(IDependencyContainer):
    """配置感知容器接口"""
    
    @abstractmethod
    def configure_from_dict(self, config: Dict[str, Any]) -> None:
        """从字典配置容器"""
        pass
    
    @abstractmethod
    def configure_from_file(self, config_file: str) -> None:
        """从文件配置容器"""
        pass
    
    @abstractmethod
    def get_configuration_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        pass
    
    @abstractmethod
    def validate_configuration(self) -> 'ValidationResult':
        """验证配置"""
        pass