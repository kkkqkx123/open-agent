"""存储适配器工厂

提供创建同步和异步存储适配器的工厂实现。
"""

import logging
from typing import Dict, Any, Optional, Union

from src.core.state.adapter_interfaces import (
    IStateStorageAdapter,
    IStorageAdapterFactory,
)
from src.core.state.async_adapter_interfaces import IAsyncStateStorageAdapter
from src.core.state.storage_interfaces import IStorageBackend
from .adapters.async_adapter import AsyncStateStorageAdapter
from .adapters.sync_adapter import SyncStateStorageAdapter
from .core.metrics import StorageMetrics
from .core.transaction import TransactionManager

logger = logging.getLogger(__name__)


class StorageAdapterFactory(IStorageAdapterFactory):
    """存储适配器工厂实现
    
    提供创建同步存储适配器的功能。
    """
    
    def __init__(self):
        """初始化存储适配器工厂"""
        self._supported_types = {
            'memory': 'In-memory storage backend',
            'sqlite': 'SQLite storage backend',
            'file': 'File-based storage backend'
        }
    
    def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建同步存储适配器
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            同步存储适配器实例
        """
        # 导入后端实现
        if storage_type == 'memory':
            from .backends.memory_backend import MemoryStorageBackend
            backend = MemoryStorageBackend(**config)
        elif storage_type == 'sqlite':
            from .backends.sqlite_backend import SQLiteStorageBackend
            backend = SQLiteStorageBackend(**config)
        elif storage_type == 'file':
            from .backends.file_backend import FileStorageBackend
            backend = FileStorageBackend(**config)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
        
        # 创建指标收集器
        metrics = StorageMetrics()
        
        # 创建事务管理器
        transaction_manager = TransactionManager(backend)
        
        # 创建适配器
        adapter = SyncStateStorageAdapter(
            backend=backend,
            metrics=metrics,
            transaction_manager=transaction_manager
        )
        
        logger.info(f"Created sync storage adapter for type: {storage_type}")
        return adapter
    
    def get_supported_types(self) -> list[str]:
        """获取支持的存储类型
        
        Returns:
            支持的存储类型列表
        """
        return list(self._supported_types.keys())
    
    def validate_config(self, storage_type: str, config: Dict[str, Any]) -> list[str]:
        """验证配置参数
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if storage_type not in self._supported_types:
            errors.append(f"Unsupported storage type: {storage_type}")
        
        # 根据存储类型验证特定配置
        if storage_type == 'sqlite':
            if 'database_path' not in config:
                errors.append("database_path is required for sqlite storage")
        elif storage_type == 'file':
            if 'storage_path' not in config:
                errors.append("storage_path is required for file storage")
        
        return errors


class AsyncStorageAdapterFactory:
    """异步存储适配器工厂实现
    
    提供创建异步存储适配器的功能。
    """
    
    def __init__(self):
        """初始化异步存储适配器工厂"""
        self._supported_types = {
            'memory': 'In-memory storage backend',
            'sqlite': 'SQLite storage backend',
            'file': 'File-based storage backend'
        }
    
    async def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IAsyncStateStorageAdapter:
        """异步创建存储适配器
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            异步存储适配器实例
        """
        # 导入后端实现
        if storage_type == 'memory':
            from .backends.memory_backend import MemoryStorageBackend
            backend = MemoryStorageBackend(**config)
        elif storage_type == 'sqlite':
            from .backends.sqlite_backend import SQLiteStorageBackend
            backend = SQLiteStorageBackend(**config)
        elif storage_type == 'file':
            from .backends.file_backend import FileStorageBackend
            backend = FileStorageBackend(**config)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
        
        # 创建指标收集器
        metrics = StorageMetrics()
        
        # 创建事务管理器
        transaction_manager = TransactionManager(backend)
        
        # 创建适配器
        adapter = AsyncStateStorageAdapter(
            backend=backend,
            metrics=metrics,
            transaction_manager=transaction_manager
        )
        
        logger.info(f"Created async storage adapter for type: {storage_type}")
        return adapter
    
    def get_supported_types(self) -> list[str]:
        """获取支持的存储类型
        
        Returns:
            支持的存储类型列表
        """
        return list(self._supported_types.keys())
    
    async def validate_config(self, storage_type: str, config: Dict[str, Any]) -> list[str]:
        """异步验证配置参数
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if storage_type not in self._supported_types:
            errors.append(f"Unsupported storage type: {storage_type}")
        
        # 根据存储类型验证特定配置
        if storage_type == 'sqlite':
            if 'database_path' not in config:
                errors.append("database_path is required for sqlite storage")
        elif storage_type == 'file':
            if 'storage_path' not in config:
                errors.append("storage_path is required for file storage")
        
        return errors


def create_storage_adapter(storage_type: str, config: Dict[str, Any], 
                          async_mode: bool = False) -> Union[IStateStorageAdapter, IAsyncStateStorageAdapter]:
    """创建存储适配器的便捷函数
    
    Args:
        storage_type: 存储类型
        config: 配置参数
        async_mode: 是否创建异步适配器
        
    Returns:
        存储适配器实例
    """
    if async_mode:
        # 异步适配器需要在异步上下文中创建
        import asyncio
        
        async def _create():
            factory = AsyncStorageAdapterFactory()
            return await factory.create_adapter(storage_type, config)
        
        # 如果在事件循环中，使用 run_coroutine_threadsafe
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，需要特殊处理
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _create())
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，直接运行
            return asyncio.run(_create())
    else:
        factory = StorageAdapterFactory()
        return factory.create_adapter(storage_type, config)