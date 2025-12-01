"""配置管理器工厂实现

提供模块特定的配置管理器创建和管理功能。
"""

from typing import Dict, Any, Optional, Type

from src.interfaces.config.interfaces import IConfigManagerFactory, IUnifiedConfigManager
from .config_manager import ConfigManager


class ConfigManagerFactory(IConfigManagerFactory):
    """配置管理器工厂

    负责创建和管理模块特定的配置管理器实例。
    """

    def __init__(self, base_manager: Optional[IUnifiedConfigManager] = None):
        """初始化配置管理器工厂

        Args:
            base_manager: 基础配置管理器实例，如果为None则需要在使用前设置
        """
        self._base_manager = base_manager
        self._managers: Dict[str, IUnifiedConfigManager] = {}
        self._manager_decorators: Dict[str, Type] = {}
    
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
        # 获取基础配置管理器
        if self._base_manager is None:
            raise RuntimeError("基础配置管理器未初始化，无法创建管理器")

        base_manager = self._base_manager

        # 如果有模块特定的装饰器，应用装饰器
        if module_type in self._manager_decorators:
            decorator_class = self._manager_decorators[module_type]
            manager: IUnifiedConfigManager = decorator_class(base_manager)
        else:
            manager = base_manager

        return manager
    
    def register_manager_decorator(self, module_type: str, decorator_class: Type) -> None:
        """注册管理器装饰器

        Args:
            module_type: 模块类型
            decorator_class: 装饰器类
        """
        self._manager_decorators[module_type] = decorator_class

        # 如果已经创建了该模块的管理器，需要重新创建
        if module_type in self._managers:
            del self._managers[module_type]

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
        else:
            self._managers.clear()

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


def set_global_factory(factory: ConfigManagerFactory) -> None:
    """设置全局配置管理器工厂

    Args:
        factory: 工厂实例
    """
    global _global_factory
    _global_factory = factory


def get_global_factory() -> Optional[ConfigManagerFactory]:
    """获取全局配置管理器工厂

    Returns:
        全局工厂实例，如果没有设置则返回None
    """
    return _global_factory


def get_module_manager(module_type: str) -> Optional[IUnifiedConfigManager]:
    """获取模块配置管理器的便捷函数

    Args:
        module_type: 模块类型

    Returns:
        配置管理器实例，如果没有工厂则返回None
    """
    factory = get_global_factory()
    if factory:
        return factory.get_manager(module_type)
    return None


def register_module_decorator(module_type: str, decorator_class: Type) -> bool:
    """注册模块装饰器的便捷函数

    Args:
        module_type: 模块类型
        decorator_class: 装饰器类

    Returns:
        注册是否成功
    """
    factory = get_global_factory()
    if factory:
        factory.register_manager_decorator(module_type, decorator_class)
        return True
    return False