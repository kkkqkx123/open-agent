"""状态管理器工厂

提供创建各种状态管理器的工厂类。
"""

from typing import Any, Dict, Optional, Type, Union

from src.interfaces.state.manager import IStateManager
from src.interfaces.storage import IStateStorageAdapter as IStorageAdapter
from ..core.state_manager import StateManager
# TODO: 修复 memory_backend 和 sqlite_backend 模块缺失问题
# from src.adapters.storage.backends.memory_backend import MemoryStorageBackend
# from src.adapters.storage.backends.sqlite_backend import SQLiteStorageBackend
# TODO: 修复 file_backend 模块缺失问题
# from src.adapters.storage.backends.file_backend import FileStorageBackend


class StateManagerFactory:
    """状态管理器工厂类
    
    提供创建各种状态管理器的统一接口。
    """
    
    # 存储适配器注册表
    _adapter_registry: Dict[str, Union[Type[IStorageAdapter], Any]] = {
        # TODO: 修复 memory_backend 和 sqlite_backend 模块缺失问题
        # "memory": MemoryStorageBackend,
        # "sqlite": SQLiteStorageBackend,
        # "file": FileStorageBackend
    }
    
    @classmethod
    def create_manager(cls,
                      storage_type: str = "memory",
                      config: Optional[Dict[str, Any]] = None,
                      **storage_kwargs) -> IStateManager:
        """创建状态管理器
        
        Args:
            storage_type: 存储类型
            config: 状态配置
            **storage_kwargs: 存储适配器参数
            
        Returns:
            IStateManager: 状态管理器实例
            
        Raises:
            ValueError: 当存储类型不支持时
        """
        # 创建配置字典
        full_config = {
            "storage": {
                "type": storage_type,
                **storage_kwargs
            }
        }
        
        # 合并用户配置
        if config:
            full_config.update(config)
        
        # 创建状态管理器
        return StateManager(full_config)
    
    @classmethod
    def create_memory_manager(cls,
                             config: Optional[Dict[str, Any]] = None,
                             **kwargs) -> IStateManager:
        """创建内存状态管理器
        
        Args:
            config: 状态配置
            **kwargs: 存储适配器参数
            
        Returns:
            IStateManager: 状态管理器实例
        """
        return cls.create_manager("memory", config, **kwargs)
    
    @classmethod
    def create_sqlite_manager(cls,
                             database_path: str,
                             config: Optional[Dict[str, Any]] = None,
                             **kwargs) -> IStateManager:
        """创建SQLite状态管理器
        
        Args:
            database_path: 数据库路径
            config: 状态配置
            **kwargs: 存储适配器参数
            
        Returns:
            IStateManager: 状态管理器实例
        """
        return cls.create_manager("sqlite", config, database_path=database_path, **kwargs)
    
    @classmethod
    def create_file_manager(cls,
                           storage_path: str,
                           config: Optional[Dict[str, Any]] = None,
                           **kwargs) -> IStateManager:
        """创建文件状态管理器
        
        Args:
            storage_path: 存储路径
            config: 状态配置
            **kwargs: 存储适配器参数
            
        Returns:
            IStateManager: 状态管理器实例
        """
        return cls.create_manager("file", config, storage_path=storage_path, **kwargs)
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> IStateManager:
        """从配置创建状态管理器
        
        Args:
            config: 状态配置
            
        Returns:
            IStateManager: 状态管理器实例
        """
        storage_type = config.get("storage", {}).get("type", "memory")
        storage_config = config.get("storage", {})
        
        return cls.create_manager(storage_type, config, **storage_config)
    
    @classmethod
    def create_storage_adapter(cls, 
                              storage_type: str,
                              **kwargs) -> IStorageAdapter:
        """创建存储适配器
        
        Args:
            storage_type: 存储类型
            **kwargs: 存储适配器参数
            
        Returns:
            IStorageAdapter: 存储适配器实例
            
        Raises:
            ValueError: 当存储类型不支持时
        """
        if storage_type not in cls._adapter_registry:
            raise ValueError(f"Unsupported storage type: {storage_type}")
        
        adapter_class = cls._adapter_registry[storage_type]
        return adapter_class(**kwargs)
    
    @classmethod
    def register_storage_adapter(cls, 
                                storage_type: str,
                                adapter_class: Type[IStorageAdapter]) -> None:
        """注册新的存储适配器
        
        Args:
            storage_type: 存储类型名称
            adapter_class: 存储适配器类
            
        Raises:
            TypeError: 当适配器类不是IStorageAdapter的子类时
        """
        if not issubclass(adapter_class, IStorageAdapter):
            raise TypeError(f"Adapter class must inherit from IStorageAdapter: {adapter_class}")
        
        cls._adapter_registry[storage_type] = adapter_class
    
    @classmethod
    def get_supported_storage_types(cls) -> list[str]:
        """获取支持的存储类型列表
        
        Returns:
            list[str]: 支持的存储类型列表
        """
        return list(cls._adapter_registry.keys())
    
    @classmethod
    def is_storage_type_supported(cls, storage_type: str) -> bool:
        """检查存储类型是否支持
        
        Args:
            storage_type: 存储类型
            
        Returns:
            bool: 是否支持
        """
        return storage_type in cls._adapter_registry


# 便捷函数
def create_state_manager(storage_type: str = "memory",
                        config: Optional[Dict[str, Any]] = None,
                        **storage_kwargs) -> IStateManager:
    """创建状态管理器的便捷函数
    
    Args:
        storage_type: 存储类型
        config: 状态配置
        **storage_kwargs: 存储适配器参数
        
    Returns:
        IStateManager: 状态管理器实例
    """
    return StateManagerFactory.create_manager(storage_type, config, **storage_kwargs)


def create_memory_state_manager(config: Optional[Dict[str, Any]] = None,
                               **kwargs) -> IStateManager:
    """创建内存状态管理器的便捷函数
    
    Args:
        config: 状态配置
        **kwargs: 存储适配器参数
        
    Returns:
        IStateManager: 状态管理器实例
    """
    return StateManagerFactory.create_memory_manager(config, **kwargs)


def create_sqlite_state_manager(database_path: str,
                               config: Optional[Dict[str, Any]] = None,
                               **kwargs) -> IStateManager:
    """创建SQLite状态管理器的便捷函数
    
    Args:
        database_path: 数据库路径
        config: 状态配置
        **kwargs: 存储适配器参数
        
    Returns:
        IStateManager: 状态管理器实例
    """
    return StateManagerFactory.create_sqlite_manager(database_path, config, **kwargs)


def create_file_state_manager(storage_path: str,
                             config: Optional[Dict[str, Any]] = None,
                             **kwargs) -> IStateManager:
    """创建文件状态管理器的便捷函数
    
    Args:
        storage_path: 存储路径
        config: 状态配置
        **kwargs: 存储适配器参数
        
    Returns:
        IStateManager: 状态管理器实例
    """
    return StateManagerFactory.create_file_manager(storage_path, config, **kwargs)