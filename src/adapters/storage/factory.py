"""存储适配器工厂

提供存储适配器的创建和注册机制，支持动态扩展。
"""

import logging
from typing import Dict, Any, Optional, Type, Callable, Union, List
from abc import ABC, abstractmethod

from src.core.state.interfaces import IStateStorageAdapter
from src.core.state.exceptions import StorageError, StorageConfigurationError as ConfigurationError
from .memory import MemoryStateStorageAdapter
from .sqlite import SQLiteStateStorageAdapter
from .file import FileStateStorageAdapter


logger = logging.getLogger(__name__)


class StorageAdapterFactory(ABC):
    """存储适配器工厂抽象基类"""
    
    @abstractmethod
    def create_adapter(self, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建存储适配器
        
        Args:
            config: 配置参数
            
        Returns:
            存储适配器实例
        """
        pass
    
    @abstractmethod
    def get_adapter_type(self) -> str:
        """获取适配器类型
        
        Returns:
            适配器类型字符串
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置参数
        
        Args:
            config: 配置参数
            
        Returns:
            是否验证通过
        """
        pass


class MemoryStorageAdapterFactory(StorageAdapterFactory):
    """内存存储适配器工厂"""
    
    def create_adapter(self, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建内存存储适配器"""
        return MemoryStateStorageAdapter(**config)
    
    def get_adapter_type(self) -> str:
        """获取适配器类型"""
        return "memory"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置参数"""
        # 内存存储配置验证
        if "max_size" in config and config["max_size"] is not None:
            if not isinstance(config["max_size"], int) or config["max_size"] <= 0:
                return False
        
        if "max_memory_mb" in config and config["max_memory_mb"] is not None:
            if not isinstance(config["max_memory_mb"], int) or config["max_memory_mb"] <= 0:
                return False
        
        return True


class SQLiteStorageAdapterFactory(StorageAdapterFactory):
    """SQLite存储适配器工厂"""
    
    def create_adapter(self, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建SQLite存储适配器"""
        return SQLiteStateStorageAdapter(**config)
    
    def get_adapter_type(self) -> str:
        """获取适配器类型"""
        return "sqlite"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置参数"""
        # SQLite存储配置验证
        if "db_path" not in config or not config["db_path"]:
            return False
        
        if "timeout" in config:
            if not isinstance(config["timeout"], (int, float)) or config["timeout"] <= 0:
                return False
        
        if "connection_pool_size" in config:
            if not isinstance(config["connection_pool_size"], int) or config["connection_pool_size"] <= 0:
                return False
        
        return True


class FileStorageAdapterFactory(StorageAdapterFactory):
    """文件存储适配器工厂"""
    
    def create_adapter(self, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建文件存储适配器"""
        return FileStateStorageAdapter(**config)
    
    def get_adapter_type(self) -> str:
        """获取适配器类型"""
        return "file"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置参数"""
        # 文件存储配置验证
        if "base_path" not in config or not config["base_path"]:
            return False
        
        if "max_files_per_directory" in config:
            if not isinstance(config["max_files_per_directory"], int) or config["max_files_per_directory"] <= 0:
                return False
        
        return True


class StorageAdapterFactoryRegistry:
    """存储适配器工厂注册表
    
    管理存储适配器工厂的注册和创建。
    """
    
    def __init__(self) -> None:
        """初始化工厂注册表"""
        self._factories: Dict[str, StorageAdapterFactory] = {}
        self._custom_factories: Dict[str, Type[StorageAdapterFactory]] = {}
        
        # 注册默认工厂
        self._register_default_factories()
        
        logger.info("StorageAdapterFactoryRegistry initialized")
    
    def _register_default_factories(self) -> None:
        """注册默认工厂"""
        self.register_factory("memory", MemoryStorageAdapterFactory())
        self.register_factory("sqlite", SQLiteStorageAdapterFactory())
        self.register_factory("file", FileStorageAdapterFactory())
    
    def register_factory(self, adapter_type: str, factory: StorageAdapterFactory) -> bool:
        """注册存储适配器工厂
        
        Args:
            adapter_type: 适配器类型
            factory: 工厂实例
            
        Returns:
            是否注册成功
        """
        try:
            if adapter_type in self._factories:
                logger.warning(f"Factory for {adapter_type} already exists, overriding...")
            
            self._factories[adapter_type] = factory
            logger.info(f"Registered factory for adapter type: {adapter_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register factory for {adapter_type}: {e}")
            return False
    
    def register_custom_factory(
        self, 
        adapter_type: str, 
        factory_class: Type[StorageAdapterFactory]
    ) -> bool:
        """注册自定义存储适配器工厂类
        
        Args:
            adapter_type: 适配器类型
            factory_class: 工厂类
            
        Returns:
            是否注册成功
        """
        try:
            if not issubclass(factory_class, StorageAdapterFactory):
                raise ConfigurationError(f"Factory class must inherit from StorageAdapterFactory")
            
            self._custom_factories[adapter_type] = factory_class
            logger.info(f"Registered custom factory class for adapter type: {adapter_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register custom factory for {adapter_type}: {e}")
            return False
    
    def unregister_factory(self, adapter_type: str) -> bool:
        """注销存储适配器工厂
        
        Args:
            adapter_type: 适配器类型
            
        Returns:
            是否注销成功
        """
        try:
            removed = False
            
            if adapter_type in self._factories:
                del self._factories[adapter_type]
                removed = True
            
            if adapter_type in self._custom_factories:
                del self._custom_factories[adapter_type]
                removed = True
            
            if removed:
                logger.info(f"Unregistered factory for adapter type: {adapter_type}")
                return True
            else:
                logger.warning(f"Factory for {adapter_type} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to unregister factory for {adapter_type}: {e}")
            return False
    
    def create_adapter(self, adapter_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建存储适配器
        
        Args:
            adapter_type: 适配器类型
            config: 配置参数
            
        Returns:
            存储适配器实例
            
        Raises:
            StorageError: 创建失败
        """
        try:
            # 获取工厂
            factory = self.get_factory(adapter_type)
            if factory is None:
                raise StorageError(f"No factory registered for adapter type: {adapter_type}")
            
            # 验证配置
            if not factory.validate_config(config):
                raise ConfigurationError(f"Invalid configuration for adapter type: {adapter_type}")
            
            # 创建适配器
            adapter = factory.create_adapter(config)
            
            logger.info(f"Created adapter of type: {adapter_type}")
            return adapter
            
        except Exception as e:
            if isinstance(e, (StorageError, ConfigurationError)):
                raise
            raise StorageError(f"Failed to create adapter of type {adapter_type}: {e}")
    
    def get_factory(self, adapter_type: str) -> Optional[StorageAdapterFactory]:
        """获取存储适配器工厂
        
        Args:
            adapter_type: 适配器类型
            
        Returns:
            工厂实例或None
        """
        # 首先尝试从已注册的工厂中获取
        if adapter_type in self._factories:
            return self._factories[adapter_type]
        
        # 尝试从自定义工厂类中创建实例
        if adapter_type in self._custom_factories:
            try:
                factory_class = self._custom_factories[adapter_type]
                factory_instance = factory_class()
                self._factories[adapter_type] = factory_instance
                return factory_instance
            except Exception as e:
                logger.error(f"Failed to create factory instance for {adapter_type}: {e}")
        
        return None
    
    def list_adapter_types(self) -> List[str]:
        """列出所有已注册的适配器类型
        
        Returns:
            适配器类型列表
        """
        types = set(self._factories.keys())
        types.update(self._custom_factories.keys())
        return list(types)
    
    def get_factory_info(self, adapter_type: str) -> Optional[Dict[str, Any]]:
        """获取工厂信息
        
        Args:
            adapter_type: 适配器类型
            
        Returns:
            工厂信息或None
        """
        factory = self.get_factory(adapter_type)
        if factory is None:
            return None
        
        return {
            "adapter_type": factory.get_adapter_type(),
            "factory_class": factory.__class__.__name__,
            "is_custom": adapter_type in self._custom_factories
        }
    
    def validate_adapter_config(self, adapter_type: str, config: Dict[str, Any]) -> bool:
        """验证适配器配置
        
        Args:
            adapter_type: 适配器类型
            config: 配置参数
            
        Returns:
            是否验证通过
        """
        try:
            factory = self.get_factory(adapter_type)
            if factory is None:
                return False
            
            return factory.validate_config(config)
            
        except Exception as e:
            logger.error(f"Failed to validate config for {adapter_type}: {e}")
            return False


# 全局工厂注册表实例
_global_factory_registry: Optional[StorageAdapterFactoryRegistry] = None


def get_factory_registry() -> StorageAdapterFactoryRegistry:
    """获取全局工厂注册表
    
    Returns:
        工厂注册表实例
    """
    global _global_factory_registry
    
    if _global_factory_registry is None:
        _global_factory_registry = StorageAdapterFactoryRegistry()
    
    return _global_factory_registry


def create_storage_adapter(adapter_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
    """创建存储适配器的便捷函数
    
    Args:
        adapter_type: 适配器类型
        config: 配置参数
        
    Returns:
        存储适配器实例
    """
    registry = get_factory_registry()
    return registry.create_adapter(adapter_type, config)


def register_storage_factory(
    adapter_type: str, 
    factory: StorageAdapterFactory
) -> bool:
    """注册存储适配器工厂的便捷函数
    
    Args:
        adapter_type: 适配器类型
        factory: 工厂实例
        
    Returns:
        是否注册成功
    """
    registry = get_factory_registry()
    return registry.register_factory(adapter_type, factory)


def register_custom_storage_factory(
    adapter_type: str, 
    factory_class: Type[StorageAdapterFactory]
) -> bool:
    """注册自定义存储适配器工厂类的便捷函数
    
    Args:
        adapter_type: 适配器类型
        factory_class: 工厂类
        
    Returns:
        是否注册成功
    """
    registry = get_factory_registry()
    return registry.register_custom_factory(adapter_type, factory_class)


# 装饰器：用于注册自定义工厂
def storage_adapter_factory(adapter_type: str) -> Callable[[Type[StorageAdapterFactory]], Type[StorageAdapterFactory]]:
    """存储适配器工厂装饰器
    
    Args:
        adapter_type: 适配器类型
        
    Returns:
        装饰器函数
    """
    def decorator(factory_class: Type[StorageAdapterFactory]) -> Type[StorageAdapterFactory]:
        register_custom_storage_factory(adapter_type, factory_class)
        return factory_class
    
    return decorator