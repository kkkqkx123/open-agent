"""注册表基类模块

提供注册表的基础接口和管理器。
"""

from .registry_manager import IRegistryManager, RegistryManager, get_global_registry_manager

__all__ = ["IRegistryManager", "RegistryManager", "get_global_registry_manager"]