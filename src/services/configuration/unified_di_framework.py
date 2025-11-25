"""统一DI框架入口"""

import logging
from typing import Dict, Any, Optional, List, Type, TypeVar

from src.interfaces.configuration import (
    IConfigurationManager,
    IModuleConfigurator,
    IConfigurationValidator,
    ValidationResult
)
from src.interfaces.container import (
    IEnhancedDependencyContainer,
    IDependencyContainer,
    IContainerPlugin
)
from src.services.configuration.configuration_manager import (
    ConfigurationManager,
    SimpleConfigurationValidator
)
from src.services.configuration.template_system import (
    TemplateManager,
    TemplateRenderer,
    get_global_template_manager
)
from src.services.container.enhanced_container import EnhancedContainer
from src.services.container.lifecycle_manager import LifecycleManager
from src.services.container.dependency_analyzer import DependencyAnalyzer
from src.services.container.service_tracker import ServiceTracker

logger = logging.getLogger(__name__)


class UnifiedDIFramework:
    """统一DI框架主类"""
    
    def __init__(self) -> None:
        self._container: Optional[IEnhancedDependencyContainer] = None
        self._configuration_manager: Optional[IConfigurationManager] = None
        self._template_manager: Optional[TemplateManager] = None
        self._lifecycle_manager: Optional[LifecycleManager] = None
        self._validator: Optional[IConfigurationValidator] = None
        self._initialized = False
        
        logger.debug("UnifiedDIFramework初始化完成")
    
    def initialize(self, environment: str = "default") -> IEnhancedDependencyContainer:
        """初始化框架"""
        if self._initialized:
            logger.warning("框架已初始化，返回现有容器")
            return self._container  # type: ignore
        
        try:
            # 创建增强容器
            self._container = EnhancedContainer(environment)
            
            # 创建配置管理器
            self._validator = SimpleConfigurationValidator()
            self._configuration_manager = ConfigurationManager(self._validator)
            
            # 创建模板管理器
            self._template_manager = TemplateManager()
            
            # 创建生命周期管理器
            self._lifecycle_manager = LifecycleManager()
            
            # 初始化插件
            self._container.initialize_plugins()
            
            self._initialized = True
            logger.info(f"统一DI框架初始化完成，环境: {environment}")
            
            return self._container
            
        except Exception as e:
            logger.error(f"框架初始化失败: {e}")
            raise
    
    def get_container(self) -> IEnhancedDependencyContainer:
        """获取容器"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        return self._container  # type: ignore
    
    def get_configuration_manager(self) -> IConfigurationManager:
        """获取配置管理器"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        return self._configuration_manager  # type: ignore
    
    def get_template_manager(self) -> TemplateManager:
        """获取模板管理器"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        return self._template_manager  # type: ignore
    
    def get_lifecycle_manager(self) -> LifecycleManager:
        """获取生命周期管理器"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        return self._lifecycle_manager  # type: ignore
    
    def register_configurator(self, module_name: str, configurator: IModuleConfigurator) -> None:
        """注册模块配置器"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        self._configuration_manager.register_configurator(module_name, configurator)  # type: ignore
        logger.debug(f"注册模块配置器: {module_name}")
    
    def configure_from_template(self, template_name: str, 
                               variables: Optional[Dict[str, Any]] = None,
                               overrides: Optional[Dict[str, Any]] = None) -> None:
        """从模板配置"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        # 渲染模板
        renderer = TemplateRenderer(self._template_manager)  # type: ignore
        config = renderer.render_configuration(template_name, variables, overrides)
        
        # 应用配置
        self.configure_all_modules(config)
        
        logger.info(f"从模板 {template_name} 配置完成")
    
    def configure_module(self, module_name: str, config: Dict[str, Any]) -> None:
        """配置单个模块"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        self._configuration_manager.configure_module(module_name, config)  # type: ignore
        
        # 注册到生命周期管理器
        self._register_module_services(module_name)
        
        logger.info(f"模块 {module_name} 配置完成")
    
    def configure_all_modules(self, config: Dict[str, Any]) -> None:
        """配置所有模块"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        # 验证配置
        validation_result = self._configuration_manager.validate_configuration(config)  # type: ignore
        if not validation_result.is_success():
            error_msg = f"配置验证失败: {validation_result.errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 配置所有模块
        self._configuration_manager.configure_all_modules(config)  # type: ignore
        
        # 注册所有服务到生命周期管理器
        for module_name in config.keys():
            self._register_module_services(module_name)
        
        logger.info("所有模块配置完成")
    
    def register_plugin(self, plugin: IContainerPlugin) -> None:
        """注册插件"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        self._container.register_plugin(plugin)  # type: ignore
        logger.debug(f"注册插件: {plugin.get_plugin_name()}")
    
    def start_all_services(self) -> Dict[str, bool]:
        """启动所有服务"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        return self._lifecycle_manager.start_all_services()  # type: ignore
    
    def stop_all_services(self) -> Dict[str, bool]:
        """停止所有服务"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        return self._lifecycle_manager.stop_all_services()  # type: ignore
    
    def dispose_all_services(self) -> Dict[str, bool]:
        """释放所有服务"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        return self._lifecycle_manager.dispose_all_services()  # type: ignore
    
    def get_framework_status(self) -> Dict[str, Any]:
        """获取框架状态"""
        if not self._initialized:
            return {"initialized": False}
        
        # 获取容器指标
        container_metrics = self._container.get_service_metrics()  # type: ignore
        
        # 获取配置状态
        config_status = self._configuration_manager.get_configuration_status()  # type: ignore
        
        # 获取生命周期统计
        lifecycle_stats = self._lifecycle_manager.get_lifecycle_statistics()  # type: ignore
        
        # 获取依赖分析
        dep_analysis = self._container.analyze_dependencies()  # type: ignore
        
        return {
            "initialized": True,
            "container_metrics": {
                "total_services": container_metrics.total_services,
                "singleton_count": container_metrics.singleton_count,
                "transient_count": container_metrics.transient_count,
                "scoped_count": container_metrics.scoped_count,
                "average_resolution_time": container_metrics.average_resolution_time,
                "cache_hit_rate": container_metrics.cache_hit_rate,
                "memory_usage": container_metrics.memory_usage
            },
            "configuration_status": {k: v.value for k, v in config_status.items()},
            "lifecycle_statistics": lifecycle_stats,
            "dependency_analysis": {
                "total_services": len(dep_analysis.dependency_graph),
                "circular_dependencies": len(dep_analysis.circular_dependencies),
                "max_dependency_depth": dep_analysis.max_dependency_depth,
                "orphaned_services": len(dep_analysis.orphaned_services)
            }
        }
    
    def optimize_configuration(self) -> Dict[str, Any]:
        """优化配置"""
        if not self._initialized:
            raise RuntimeError("框架未初始化，请先调用 initialize()")
        
        suggestions = self._container.optimize_configuration()  # type: ignore
        
        return {
            "suggestions": [
                {
                    "service_type": s.service_type.__name__,
                    "suggestion_type": s.suggestion_type,
                    "description": s.description,
                    "impact": s.impact
                }
                for s in suggestions.suggestions
            ],
            "total_impact_score": suggestions.total_impact_score,
            "high_priority_count": len(suggestions.get_high_priority_suggestions())
        }
    
    def _register_module_services(self, module_name: str) -> None:
        """注册模块服务到生命周期管理器"""
        # 这里需要根据实际情况获取模块中的服务
        # 由于框架的通用性，这里只是一个示例实现
        pass
    
    def shutdown(self) -> None:
        """关闭框架"""
        if not self._initialized:
            return
        
        try:
            # 停止所有服务
            self.stop_all_services()
            
            # 释放所有服务
            self.dispose_all_services()
            
            # 清理容器
            self._container.clear()  # type: ignore
            
            self._initialized = False
            logger.info("统一DI框架已关闭")
            
        except Exception as e:
            logger.error(f"关闭框架时发生错误: {e}")
            raise


# 全局框架实例
_global_framework: Optional[UnifiedDIFramework] = None


def get_global_framework() -> UnifiedDIFramework:
    """获取全局框架实例"""
    global _global_framework
    if _global_framework is None:
        _global_framework = UnifiedDIFramework()
    return _global_framework


def initialize_framework(environment: str = "default") -> IEnhancedDependencyContainer:
    """初始化全局框架"""
    framework = get_global_framework()
    return framework.initialize(environment)


def shutdown_framework() -> None:
    """关闭全局框架"""
    global _global_framework
    if _global_framework is not None:
        _global_framework.shutdown()
        _global_framework = None


# 便捷函数
def register_module_configurator(module_name: str, configurator: IModuleConfigurator) -> None:
    """便捷的模块配置器注册函数"""
    framework = get_global_framework()
    framework.register_configurator(module_name, configurator)


def configure_from_template(template_name: str, 
                           variables: Optional[Dict[str, Any]] = None,
                           overrides: Optional[Dict[str, Any]] = None) -> None:
    """便捷的模板配置函数"""
    framework = get_global_framework()
    framework.configure_from_template(template_name, variables, overrides)


def get_service(service_type: Type[T]) -> T:
    """便捷的服务获取函数"""
    framework = get_global_framework()
    container = framework.get_container()
    return container.get(service_type)


def get_framework_status() -> Dict[str, Any]:
    """便捷的框架状态获取函数"""
    framework = get_global_framework()
    return framework.get_framework_status()


T = TypeVar('T')