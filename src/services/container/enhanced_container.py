"""增强依赖注入容器实现"""

import logging
import threading
import time
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable, Tuple
from collections import defaultdict

from src.interfaces.container import (
    IEnhancedDependencyContainer,
    IDependencyAnalyzer,
    IServiceTracker,
    IPluginManager,
    IContainerPlugin,
    ServiceLifetime,
    DependencyAnalysisResult,
    ServiceMetrics,
    OptimizationSuggestions,
    OptimizationSuggestion
)
from src.services.container.container import DependencyContainer, ServiceRegistration
from src.services.container.dependency_analyzer import DependencyAnalyzer
from src.services.container.service_tracker import ServiceTracker

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PluginManager(IPluginManager):
    """插件管理器实现"""
    
    def __init__(self):
        self._plugins: List[IContainerPlugin] = []
        self._lock = threading.RLock()
    
    def register_plugin(self, plugin: IContainerPlugin) -> None:
        """注册插件"""
        with self._lock:
            # 检查是否已存在同名插件
            for existing in self._plugins:
                if existing.get_plugin_name() == plugin.get_plugin_name():
                    logger.warning(f"插件已存在，将被覆盖: {plugin.get_plugin_name()}")
                    self._plugins.remove(existing)
                    break
            
            self._plugins.append(plugin)
            # 按优先级排序
            self._plugins.sort(key=lambda x: x.get_plugin_priority())
            
            logger.debug(f"注册插件: {plugin.get_plugin_name()} v{plugin.get_plugin_version()}")
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """注销插件"""
        with self._lock:
            for plugin in self._plugins:
                if plugin.get_plugin_name() == plugin_name:
                    try:
                        plugin.cleanup()
                    except Exception as e:
                        logger.error(f"清理插件 {plugin_name} 时发生错误: {e}")
                    
                    self._plugins.remove(plugin)
                    logger.debug(f"注销插件: {plugin_name}")
                    return
            
            logger.warning(f"插件不存在: {plugin_name}")
    
    def load_plugins_from_directory(self, plugin_dir: str) -> None:
        """从目录加载插件"""
        import os
        import importlib.util
        
        if not os.path.exists(plugin_dir):
            logger.warning(f"插件目录不存在: {plugin_dir}")
            return
        
        with self._lock:
            for filename in os.listdir(plugin_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    plugin_path = os.path.join(plugin_dir, filename)
                    try:
                        # 动态加载插件模块
                        spec = importlib.util.spec_from_file_location(
                            filename[:-3], plugin_path
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # 查找插件类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                issubclass(attr, IContainerPlugin) and 
                                attr != IContainerPlugin):
                                
                                plugin_instance = attr()
                                self.register_plugin(plugin_instance)
                                logger.info(f"从文件加载插件: {filename} -> {plugin_instance.get_plugin_name()}")
                    
                    except Exception as e:
                        logger.error(f"加载插件文件 {filename} 失败: {e}")
    
    def get_loaded_plugins(self) -> List[IContainerPlugin]:
        """获取已加载的插件"""
        with self._lock:
            return self._plugins.copy()
    
    def initialize_plugins(self, container: 'IDependencyContainer') -> None:
        """初始化所有插件"""
        with self._lock:
            for plugin in self._plugins:
                try:
                    plugin.initialize(container)
                    logger.debug(f"初始化插件: {plugin.get_plugin_name()}")
                except Exception as e:
                    logger.error(f"初始化插件 {plugin.get_plugin_name()} 失败: {e}")


class EnhancedContainer(DependencyContainer, IEnhancedDependencyContainer):
    """增强依赖注入容器实现"""
    
    def __init__(self, environment: str = "default"):
        super().__init__(environment)
        
        # 初始化增强功能
        self._dependency_analyzer = DependencyAnalyzer()
        self._service_tracker = ServiceTracker()
        self._plugin_manager = PluginManager()
        
        # 增强注册信息
        self._conditional_registrations: Dict[Type, List[Dict[str, Any]]] = defaultdict(list)
        self._named_registrations: Dict[str, Dict[Type, ServiceRegistration]] = defaultdict(dict)
        self._metadata_registrations: Dict[Type, Dict[str, Any]] = {}
        self._decorators: Dict[Type, List[Callable[[Any], Any]]] = defaultdict(list)
        
        # 性能优化
        self._resolution_cache: Dict[Type, Any] = {}
        self._prewarmed_services: Set[Type] = set()
        
        logger.debug("EnhancedContainer初始化完成")
    
    # 高级注册功能
    def register_conditional(
        self,
        interface: Type,
        condition: Callable[[], bool],
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """条件注册服务实现"""
        with self._lock:
            registration_info = {
                "condition": condition,
                "implementation": implementation,
                "environment": environment,
                "lifetime": lifetime,
                "timestamp": time.time()
            }
            self._conditional_registrations[interface].append(registration_info)
            
            logger.debug(f"条件注册: {interface.__name__} -> {implementation.__name__}")
    
    def register_named(
        self,
        name: str,
        interface: Type,
        implementation: Type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """命名注册服务实现"""
        with self._lock:
            if environment not in self._named_registrations:
                self._named_registrations[environment] = {}
            
            registration = ServiceRegistration(
                interface=interface,
                implementation=implementation,
                lifetime=lifetime
            )
            self._named_registrations[environment][interface] = registration
            
            logger.debug(f"命名注册: {name} -> {interface.__name__} -> {implementation.__name__}")
    
    def register_with_metadata(
        self,
        interface: Type,
        implementation: Type,
        metadata: Dict[str, Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """带元数据注册服务实现"""
        with self._lock:
            # 先进行标准注册
            self.register(interface, implementation, environment, lifetime)
            
            # 存储元数据
            self._metadata_registrations[interface] = metadata
            
            logger.debug(f"带元数据注册: {interface.__name__} -> {implementation.__name__}")
    
    def register_decorator(
        self,
        interface: Type,
        decorator: Callable[[Any], Any],
        environment: str = "default",
    ) -> None:
        """注册服务装饰器"""
        with self._lock:
            self._decorators[interface].append(decorator)
            logger.debug(f"注册装饰器: {interface.__name__}")
    
    # 高级解析功能
    def get_all(self, interface: Type) -> List[Any]:
        """获取接口的所有实现"""
        implementations = []
        
        # 获取标准注册的实现
        try:
            instance = self.get(interface)
            implementations.append(instance)
        except ValueError:
            pass
        
        # 获取条件注册的实现
        for registration_info in self._conditional_registrations.get(interface, []):
            try:
                if registration_info["condition"]():
                    instance = self._create_instance_from_info(registration_info)
                    implementations.append(instance)
            except Exception as e:
                logger.error(f"创建条件注册实例失败: {e}")
        
        return implementations
    
    def get_named(self, interface: Type, name: str) -> Any:
        """按名称获取服务实例"""
        with self._lock:
            environment_registrations = self._named_registrations.get(self._environment, {})
            if interface in environment_registrations:
                registration = environment_registrations[interface]
                return self._create_instance_from_registration(registration)
            
            # 尝试默认环境
            default_registrations = self._named_registrations.get("default", {})
            if interface in default_registrations:
                registration = default_registrations[interface]
                return self._create_instance_from_registration(registration)
            
            raise ValueError(f"未找到命名服务: {name} -> {interface.__name__}")
    
    def try_get(self, service_type: Type[T]) -> Optional[T]:
        """尝试获取服务实例，不抛异常"""
        try:
            return self.get(service_type)
        except ValueError:
            return None
    
    def get_with_metadata(self, service_type: Type[T]) -> Tuple[T, Dict[str, Any]]:
        """获取服务实例及其元数据"""
        instance = self.get(service_type)
        metadata = self._metadata_registrations.get(service_type, {})
        return instance, metadata
    
    def get_lazy(self, service_type: Type[T]) -> Callable[[], T]:
        """获取懒加载服务代理"""
        def lazy_factory() -> T:
            return self.get(service_type)
        
        return lazy_factory
    
    def prewarm_services(self, service_types: List[Type]) -> None:
        """预热服务"""
        for service_type in service_types:
            if service_type not in self._prewarmed_services:
                try:
                    self.get(service_type)
                    self._prewarmed_services.add(service_type)
                    logger.debug(f"预热服务: {service_type.__name__}")
                except Exception as e:
                    logger.error(f"预热服务 {service_type.__name__} 失败: {e}")
    
    # 分析和优化功能
    def analyze_dependencies(self) -> DependencyAnalysisResult:
        """分析依赖关系"""
        return self._dependency_analyzer.get_analysis_result()
    
    def get_service_metrics(self) -> ServiceMetrics:
        """获取服务指标"""
        # 获取性能统计
        perf_stats = self._performance_monitor.get_stats()
        
        # 获取服务统计
        total_services = len(self._registrations.get(self._environment, {}))
        singleton_count = sum(
            1 for reg in self._registrations.get(self._environment, {}).values()
            if reg.lifetime == ServiceLifetime.SINGLETON
        )
        transient_count = sum(
            1 for reg in self._registrations.get(self._environment, {}).values()
            if reg.lifetime == ServiceLifetime.TRANSIENT
        )
        scoped_count = sum(
            1 for reg in self._registrations.get(self._environment, {}).values()
            if reg.lifetime == ServiceLifetime.SCOPED
        )
        
        # 获取内存使用
        memory_usage = self._service_tracker.get_memory_usage_estimate()
        total_memory = sum(memory_usage.values())
        
        return ServiceMetrics(
            total_services=total_services,
            singleton_count=singleton_count,
            transient_count=transient_count,
            scoped_count=scoped_count,
            average_resolution_time=perf_stats.get("average_resolution_times", {}).get("overall", 0.0),
            cache_hit_rate=perf_stats.get("cache_hit_rate", 0.0),
            memory_usage=total_memory
        )
    
    def optimize_configuration(self) -> OptimizationSuggestions:
        """优化配置建议"""
        suggestions = []
        
        # 分析依赖关系
        dep_analysis = self.analyze_dependencies()
        
        # 检查循环依赖
        if dep_analysis.has_circular_dependencies():
            for circular_dep in dep_analysis.circular_dependencies:
                suggestions.append(OptimizationSuggestion(
                    service_type=circular_dep.dependency_chain[0],
                    suggestion_type="circular_dependency",
                    description=f"存在循环依赖: {' -> '.join([t.__name__ for t in circular_dep.dependency_chain])}",
                    impact="high"
                ))
        
        # 检查孤立服务
        for orphaned in dep_analysis.orphaned_services:
            suggestions.append(OptimizationSuggestion(
                service_type=orphaned,
                suggestion_type="orphaned_service",
                description=f"服务 {orphaned.__name__} 没有被其他服务依赖",
                impact="medium"
            ))
        
        # 检查内存泄漏
        memory_leaks = self._service_tracker.detect_memory_leaks()
        for leak in memory_leaks:
            suggestions.append(OptimizationSuggestion(
                service_type=leak.service_type,
                suggestion_type="memory_leak",
                description=f"检测到内存泄漏: {leak.total_instances} 个实例，持续时间 {leak.leak_duration}",
                impact="high"
            ))
        
        # 检查性能问题
        metrics = self.get_service_metrics()
        if metrics.cache_hit_rate < 0.8:
            suggestions.append(OptimizationSuggestion(
                service_type=type(self),
                suggestion_type="cache_optimization",
                description=f"缓存命中率较低: {metrics.cache_hit_rate:.2%}",
                impact="medium"
            ))
        
        # 计算总影响分数
        total_impact = sum(
            3 if s.impact == "high" else 2 if s.impact == "medium" else 1
            for s in suggestions
        )
        
        return OptimizationSuggestions(
            suggestions=suggestions,
            total_impact_score=total_impact
        )
    
    # 重写创建实例方法以支持追踪和装饰
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """创建服务实例（增强版）"""
        # 创建实例
        instance = super()._create_instance(registration)
        
        # 追踪实例创建
        self._service_tracker.track_creation(registration.interface, instance)
        
        # 应用装饰器
        decorators = self._decorators.get(registration.interface, [])
        for decorator in decorators:
            try:
                instance = decorator(instance)
            except Exception as e:
                logger.error(f"应用装饰器失败: {e}")
        
        # 更新依赖分析
        self._dependency_analyzer.update_from_implementation(
            registration.interface, 
            type(instance)
        )
        
        return instance
    
    def _create_instance_from_info(self, registration_info: Dict[str, Any]) -> Any:
        """从注册信息创建实例"""
        registration = ServiceRegistration(
            interface=None,  # 这里需要根据实际情况设置
            implementation=registration_info["implementation"],
            lifetime=registration_info["lifetime"]
        )
        return self._create_instance(registration)
    
    # 插件管理
    def register_plugin(self, plugin: IContainerPlugin) -> None:
        """注册插件"""
        self._plugin_manager.register_plugin(plugin)
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """注销插件"""
        self._plugin_manager.unregister_plugin(plugin_name)
    
    def get_loaded_plugins(self) -> List[IContainerPlugin]:
        """获取已加载的插件"""
        return self._plugin_manager.get_loaded_plugins()
    
    def initialize_plugins(self) -> None:
        """初始化所有插件"""
        self._plugin_manager.initialize_plugins(self)
    
    # 清理和重置
    def clear(self) -> None:
        """清除所有服务和缓存"""
        super().clear()
        
        with self._lock:
            self._conditional_registrations.clear()
            self._named_registrations.clear()
            self._metadata_registrations.clear()
            self._decorators.clear()
            self._resolution_cache.clear()
            self._prewarmed_services.clear()
            
            # 清理分析器和追踪器
            self._dependency_analyzer.clear()
            self._service_tracker.clear_all_tracking()
            
            logger.debug("EnhancedContainer已清除")
    
    def get_service_tracker(self) -> IServiceTracker:
        """获取服务追踪器"""
        return self._service_tracker
    
    def get_dependency_analyzer(self) -> IDependencyAnalyzer:
        """获取依赖分析器"""
        return self._dependency_analyzer
    
    def get_plugin_manager(self) -> IPluginManager:
        """获取插件管理器"""
        return self._plugin_manager