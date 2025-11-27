"""存储适配器工厂

提供创建异步存储适配器的工厂实现。
"""

import logging
from typing import Dict, Any, Optional, List

from src.interfaces.state.storage.adapter import (
    IStateStorageAdapter,
    IStorageAdapterFactory,
)
from src.interfaces.state.storage.backend import IStorageBackend
from .adapters.async_adapter import AsyncStateStorageAdapter
from .core.metrics import StorageMetrics
from .core.transaction import TransactionManager
from .registry import storage_registry

logger = logging.getLogger(__name__)


class StorageAdapterFactory(IStorageAdapterFactory):
    """存储适配器工厂实现
    
    提供创建异步存储适配器的功能，使用注册表管理存储类型。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化存储适配器工厂
        
        Args:
            config_path: 配置文件路径（可选）
        """
        # 从配置文件加载存储类型
        if config_path:
            storage_registry.load_from_config(config_path)
    
    async def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建异步存储适配器
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            异步存储适配器实例
        """
        try:
            # 获取存储类
            storage_class = storage_registry.get_storage_class(storage_type)
            
            # 获取工厂函数（如果有）
            factory = storage_registry.get_storage_factory(storage_type)
            
            if factory:
                # 使用工厂函数创建后端
                backend = factory(**config)
            else:
                # 直接实例化存储类
                backend = storage_class(**config)
            
            # 创建指标收集器
            metrics = StorageMetrics()
            
            # 创建事务管理器
            transaction_manager = TransactionManager(backend)
            
            # 创建异步适配器
            adapter = AsyncStateStorageAdapter(
                backend=backend,
                metrics=metrics,
                transaction_manager=transaction_manager
            )
            
            logger.info(f"Created async storage adapter for type: {storage_type}")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create adapter for type '{storage_type}': {e}")
            raise
    
    def get_supported_types(self) -> List[str]:
        """获取支持的存储类型
        
        Returns:
            支持的存储类型列表
        """
        return storage_registry.get_registered_types()
    
    def get_storage_info(self, storage_type: str) -> Dict[str, Any]:
        """获取存储类型信息
        
        Args:
            storage_type: 存储类型
            
        Returns:
            存储类型信息
        """
        if not storage_registry.is_registered(storage_type):
            raise ValueError(f"Storage type '{storage_type}' is not registered")
        
        storage_class = storage_registry.get_storage_class(storage_type)
        metadata = storage_registry.get_storage_metadata(storage_type)
        
        return {
            "type": storage_type,
            "class_name": storage_class.__name__,
            "module": storage_class.__module__,
            "metadata": metadata
        }
    
    async def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """异步验证配置参数
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not storage_registry.is_registered(storage_type):
            errors.append(f"Unsupported storage type: {storage_type}")
            return errors
        
        # 根据存储类型验证特定配置
        if storage_type in ['sqlite', 'checkpoint_sqlite']:
            if 'database_path' not in config and 'db_path' not in config:
                errors.append("database_path or db_path is required for sqlite storage")
        elif storage_type in ['file']:
            if 'base_path' not in config and 'storage_path' not in config:
                errors.append("base_path or storage_path is required for file storage")
        elif storage_type in ['checkpoint_memory', 'langgraph']:
            # checkpoint内存存储和langgraph不需要特殊配置验证
            pass
        
        return errors


def create_storage_adapter(storage_type: str, config: Dict[str, Any],
                          config_path: Optional[str] = None) -> IStateStorageAdapter:
    """创建存储适配器的便捷函数
    
    Args:
        storage_type: 存储类型
        config: 配置参数
        config_path: 配置文件路径（可选）
        
    Returns:
        异步存储适配器实例
    """
    import asyncio
    
    async def _create():
        factory = StorageAdapterFactory(config_path)
        return await factory.create_adapter(storage_type, config)
    
    # 运行异步创建
    result = asyncio.run(_create())
    return result