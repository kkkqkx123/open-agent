"""配置管理器工厂实现

提供模块特定的配置管理器创建和管理功能。
"""

from src.services.logger import get_logger
from typing import Dict, Any, Optional, Type

from src.interfaces.config.interfaces import IConfigManagerFactory, IUnifiedConfigManager
from src.interfaces.container import IDependencyContainer
from src.core.common.types import ServiceLifetime
from .config_manager import ConfigManager

logger = get_logger(__name__)


class ConfigManagerFactory(IConfigManagerFactory):
    """配置管理器工厂
    
    负责创建和管理模块特定的配置管理器实例。
    """
    
    def __init__(self, container: IDependencyContainer):
        """初始化配置管理器工厂
        
        Args:
            container: 依赖注入容器
        """
        self.container = container
        self._managers: Dict[str, IUnifiedConfigManager] = {}
        self._manager_decorators: Dict[str, Type] = {}
        
        logger.info("配置管理器工厂初始化完成")
    
    def get_manager(self, module_type: str) -> IUnifiedConfigManager:
        """获取模块特定的配置管理器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置管理器实例
        """
        if module_type not in self._managers:
            self._managers[module_type] = self._create_manager(module_type)
        
        return self._managers[module_type]
    
    def _create_manager(self, module_type: str) -> IUnifiedConfigManager:
        """创建模块特定的配置管理器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置管理器实例
        """
        try:
            # 获取基础配置管理器
            base_manager = self._create_base_manager()
            
            # 如果有模块特定的装饰器，应用装饰器
            if module_type in self._manager_decorators:
                decorator_class = self._manager_decorators[module_type]
                manager: IUnifiedConfigManager = decorator_class(base_manager)
                logger.info(f"已创建带装饰器的配置管理器: {module_type}")
            else:
                manager = base_manager
                logger.info(f"已创建基础配置管理器: {module_type}")
            
            return manager
            
        except Exception as e:
            logger.error(f"创建配置管理器失败 {module_type}: {e}")
            raise
    
    def _create_base_manager(self) -> ConfigManager:
        """创建基础配置管理器
        
        Returns:
            基础配置管理器实例
        """
        # 从容器获取依赖
        # 这里假设容器中已经注册了必要的依赖
        # 如果没有，则创建默认实例
        
        try:
            # 尝试从容器获取配置管理器
            return self.container.get(ConfigManager)
        except:
            # 如果容器中没有，创建默认实例
            return ConfigManager()
    
    def register_manager_decorator(self, module_type: str, decorator_class: Type) -> None:
        """注册管理器装饰器
        
        Args:
            module_type: 模块类型
            decorator_class: 装饰器类
        """
        self._manager_decorators[module_type] = decorator_class
        logger.info(f"已注册管理器装饰器: {module_type} -> {decorator_class.__name__}")
        
        # 如果已经创建了该模块的管理器，需要重新创建
        if module_type in self._managers:
            del self._managers[module_type]
            logger.info(f"已清除 {module_type} 模块的缓存管理器")
    
    def unregister_manager_decorator(self, module_type: str) -> bool:
        """注销管理器装饰器
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否成功注销
        """
        if module_type in self._manager_decorators:
            del self._manager_decorators[module_type]
            
            # 清除缓存的管理器
            if module_type in self._managers:
                del self._managers[module_type]
            
            logger.info(f"已注销管理器装饰器: {module_type}")
            return True
        
        return False
    
    def clear_manager_cache(self, module_type: Optional[str] = None) -> None:
        """清除管理器缓存
        
        Args:
            module_type: 模块类型，如果为None则清除所有缓存
        """
        if module_type:
            if module_type in self._managers:
                del self._managers[module_type]
                logger.info(f"已清除 {module_type} 模块的管理器缓存")
        else:
            self._managers.clear()
            logger.info("已清除所有管理器缓存")
    
    def get_registered_modules(self) -> list:
        """获取已注册的模块列表
        
        Returns:
            模块类型列表
        """
        return list(self._manager_decorators.keys())
    
    def get_active_managers(self) -> list:
        """获取活跃的管理器列表
        
        Returns:
            模块类型列表
        """
        return list(self._managers.keys())
    
    def get_factory_status(self) -> Dict[str, Any]:
        """获取工厂状态
        
        Returns:
            状态信息
        """
        return {
            "registered_decorators": list(self._manager_decorators.keys()),
            "active_managers": list(self._managers.keys()),
            "decorator_count": len(self._manager_decorators),
            "manager_count": len(self._managers)
        }


# 全局工厂实例
_global_factory: Optional[ConfigManagerFactory] = None


def get_global_factory() -> ConfigManagerFactory:
    """获取全局配置管理器工厂
    
    Returns:
        全局工厂实例
    """
    global _global_factory
    if _global_factory is None:
        # 这里需要获取容器实例
        # 暂时创建一个简单的工厂实例
        from src.services.container import get_global_container
        container = get_global_container()
        _global_factory = ConfigManagerFactory(container)
    return _global_factory


def set_global_factory(factory: ConfigManagerFactory) -> None:
    """设置全局配置管理器工厂
    
    Args:
        factory: 工厂实例
    """
    global _global_factory
    _global_factory = factory


def get_module_manager(module_type: str) -> IUnifiedConfigManager:
    """获取模块配置管理器的便捷函数
    
    Args:
        module_type: 模块类型
        
    Returns:
        配置管理器实例
    """
    return get_global_factory().get_manager(module_type)


def register_module_decorator(module_type: str, decorator_class: Type) -> None:
    """注册模块装饰器的便捷函数
    
    Args:
        module_type: 模块类型
        decorator_class: 装饰器类
    """
    get_global_factory().register_manager_decorator(module_type, decorator_class)