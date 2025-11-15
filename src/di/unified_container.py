"""统一依赖注入容器管理器

提供统一的容器管理，整合各层的DI配置。
"""

import logging
from typing import Dict, Any, Optional, List, Type

from src.infrastructure.container.enhanced_container import EnhancedDependencyContainer
from src.infrastructure.container_interfaces import IDependencyContainer
from .environment_config import EnvironmentConfigManager
from .interfaces import IServiceModule

logger = logging.getLogger(__name__)


class UnifiedContainerManager:
    """统一容器管理器
    
    统一管理所有层的DI配置，提供统一的配置入口。
    """
    
    def __init__(self):
        """初始化统一容器管理器"""
        self.container = EnhancedDependencyContainer()
        self.environment_manager = EnvironmentConfigManager()
        self._configured = False
        self._modules: Dict[str, IServiceModule] = {}
        
        # 配置验证结果缓存
        self._validation_cache: Optional[Dict[str, Any]] = None
        
        logger.debug("UnifiedContainerManager初始化完成")
    
    def register_module(self, module: IServiceModule) -> None:
        """注册服务模块
        
        Args:
            module: 服务模块
        """
        module_name = module.get_module_name()
        if module_name in self._modules:
            logger.warning(f"模块 {module_name} 已存在，将被覆盖")
        
        self._modules[module_name] = module
        logger.debug(f"注册服务模块: {module_name}")
    
    def configure_all_layers(self, 
                           environment: str = "default",
                           modules: Optional[List[str]] = None) -> IDependencyContainer:
        """配置所有层的服务
        
        Args:
            environment: 环境名称
            modules: 要配置的模块列表，如果为None则配置所有模块
            
        Returns:
            配置好的依赖注入容器
        """
        if self._configured:
            logger.warning("容器已经配置过，重新配置将清除现有配置")
            self.container.clear()
        
        # 设置环境
        self.environment_manager.set_environment(environment)
        self.container.set_environment(environment)
        
        # 确定要配置的模块
        modules_to_configure = modules or list(self._modules.keys())
        
        try:
            # 按依赖顺序配置模块
            configured_modules = self._get_configuration_order(modules_to_configure)
            
            for module_name in configured_modules:
                if module_name not in self._modules:
                    logger.warning(f"模块 {module_name} 未注册，跳过配置")
                    continue
                
                module = self._modules[module_name]
                self._configure_module(module, environment)
            
            self._configured = True
            self._validation_cache = None  # 清除验证缓存
            
            logger.info(f"所有层服务配置完成，环境: {environment}")
            return self.container
            
        except Exception as e:
            logger.error(f"配置过程中发生错误: {e}")
            self._configured = False
            raise
    
    def _configure_module(self, module: IServiceModule, environment: str) -> None:
        """配置单个模块
        
        Args:
            module: 服务模块
            environment: 环境名称
        """
        module_name = module.get_module_name()
        logger.info(f"开始配置模块: {module_name}")
        
        try:
            # 注册基础服务
            module.register_services(self.container)
            
            # 注册环境特定服务
            module.register_environment_services(self.container, environment)
            
            logger.debug(f"模块 {module_name} 配置完成")
            
        except Exception as e:
            logger.error(f"配置模块 {module_name} 失败: {e}")
            raise
    
    def _get_configuration_order(self, modules: List[str]) -> List[str]:
        """获取模块配置顺序（基于依赖关系）
        
        Args:
            modules: 模块名称列表
            
        Returns:
            按依赖顺序排列的模块名称列表
        """
        # 简单的拓扑排序实现
        ordered = []
        remaining = modules.copy()
        
        while remaining:
            # 找到没有未配置依赖的模块
            ready = []
            for module_name in remaining:
                module = self._modules.get(module_name)
                if not module:
                    continue
                
                dependencies = module.get_dependencies()
                if all(dep in ordered for dep in dependencies):
                    ready.append(module_name)
            
            if not ready:
                # 检测循环依赖
                logger.error("检测到模块间循环依赖")
                raise RuntimeError("模块间存在循环依赖")
            
            # 添加第一个就绪的模块
            module_name = ready[0]
            ordered.append(module_name)
            remaining.remove(module_name)
        
        return ordered
    
    def get_container(self) -> IDependencyContainer:
        """获取配置好的容器
        
        Returns:
            配置好的依赖注入容器
            
        Raises:
            RuntimeError: 如果容器尚未配置
        """
        if not self._configured:
            raise RuntimeError("容器尚未配置，请先调用configure_all_layers()")
        return self.container
    
    def validate_configuration(self) -> Dict[str, Any]:
        """验证配置
        
        Returns:
            验证结果
        """
        if not self._configured:
            return {
                "valid": False,
                "error": "容器尚未配置"
            }
        
        # 使用缓存的验证结果
        if self._validation_cache is not None:
            return self._validation_cache
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "modules": {},
            "registered_services": []
        }
        
        # 验证各模块配置
        for module_name, module in self._modules.items():
            module_validation = module.validate_configuration(self.container)
            validation_results["modules"][module_name] = module_validation
            
            if not module_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(
                    [f"{module_name}: {error}" for error in module_validation["errors"]]
                )
            
            validation_results["warnings"].extend(
                [f"{module_name}: {warning}" for warning in module_validation["warnings"]]
            )
        
        # 获取已注册的服务列表
        try:
            validation_results["registered_services"] = [
                service_type.__name__ for service_type in self.container.get_registered_services()
            ]
        except Exception as e:
            validation_results["warnings"].append(f"获取已注册服务列表失败: {e}")
        
        # 缓存验证结果
        self._validation_cache = validation_results
        
        return validation_results
    
    def get_module_info(self) -> Dict[str, Any]:
        """获取模块信息
        
        Returns:
            模块信息字典
        """
        return {
            name: {
                "name": module.get_module_name(),
                "services": list(module.get_registered_services().keys()),
                "dependencies": module.get_dependencies()
            }
            for name, module in self._modules.items()
        }
    
    def reload_module(self, module_name: str) -> None:
        """重新加载模块
        
        Args:
            module_name: 模块名称
        """
        if module_name not in self._modules:
            raise ValueError(f"模块 {module_name} 未注册")
        
        if not self._configured:
            raise RuntimeError("容器尚未配置")
        
        module = self._modules[module_name]
        environment = self.environment_manager.get_current_environment()
        
        logger.info(f"重新加载模块: {module_name}")
        self._configure_module(module, environment)
        
        # 清除验证缓存
        self._validation_cache = None
    
    def get_environment_manager(self) -> EnvironmentConfigManager:
        """获取环境管理器
        
        Returns:
            环境管理器实例
        """
        return self.environment_manager
    
    def reset(self) -> None:
        """重置容器管理器"""
        self.container.clear()
        self._configured = False
        self._validation_cache = None
        logger.info("容器管理器已重置")
    
    def dispose(self) -> None:
        """释放容器管理器资源"""
        if self._configured:
            self.container.dispose()
        
        self._configured = False
        self._validation_cache = None
        logger.info("容器管理器已释放")


# 全局容器管理器实例
_unified_manager: Optional[UnifiedContainerManager] = None


def get_unified_container(environment: str = "default", 
                        force_reconfigure: bool = False) -> IDependencyContainer:
    """获取统一配置的容器
    
    Args:
        environment: 环境名称
        force_reconfigure: 是否强制重新配置
        
    Returns:
        统一配置的依赖注入容器
    """
    global _unified_manager
    
    if _unified_manager is None or force_reconfigure:
        _unified_manager = UnifiedContainerManager()
        
        # 自动注册所有可用的模块
        _auto_register_modules(_unified_manager)
        
        _unified_manager.configure_all_layers(environment)
    
    return _unified_manager.get_container()


def reset_unified_container() -> None:
    """重置统一容器"""
    global _unified_manager
    if _unified_manager:
        _unified_manager.dispose()
    _unified_manager = None


def _auto_register_modules(manager: UnifiedContainerManager) -> None:
    """自动注册所有可用的模块
    
    Args:
        manager: 统一容器管理器
    """
    # 这里可以自动发现和注册模块
    # 为了简化，我们手动导入和注册各层模块
    
    try:
        from src.infrastructure.di.infrastructure_module import InfrastructureModule
        manager.register_module(InfrastructureModule())
    except ImportError as e:
        logger.warning(f"无法注册基础设施模块: {e}")
    
    try:
        from src.domain.di.domain_module import DomainModule
        manager.register_module(DomainModule())
    except ImportError as e:
        logger.warning(f"无法注册领域模块: {e}")
    
    try:
        from src.application.di.application_module import ApplicationModule
        manager.register_module(ApplicationModule())
    except ImportError as e:
        logger.warning(f"无法注册应用模块: {e}")
    
    try:
        from src.presentation.di.presentation_module import PresentationModule
        manager.register_module(PresentationModule())
    except ImportError as e:
        logger.warning(f"无法注册表示模块: {e}")


def configure_specific_modules(environment: str, 
                             modules: Optional[list] = None) -> IDependencyContainer:
    """配置特定模块
    
    Args:
        environment: 环境名称
        modules: 要配置的模块列表，如果为None则配置所有模块
        
    Returns:
        配置好的依赖注入容器
    """
    global _unified_manager
    
    if _unified_manager is None:
        _unified_manager = UnifiedContainerManager()
        
        # 自动注册所有可用的模块
        _auto_register_modules(_unified_manager)
    
    _unified_manager.configure_all_layers(environment, modules)
    return _unified_manager.get_container()


def validate_unified_configuration() -> Dict[str, Any]:
    """验证统一配置
    
    Returns:
        验证结果
    """
    global _unified_manager
    
    if not _unified_manager:
        return {
            "valid": False,
            "error": "统一容器管理器未初始化"
        }
    
    return _unified_manager.validate_configuration()