"""存储适配器包

提供状态存储的适配器实现。
"""

# 导入主要的适配器类
from .adapters.sync_adapter import SyncStateStorageAdapter
from .adapters.async_adapter import AsyncStateStorageAdapter

# 导入工厂类
from .factory import StorageAdapterFactory, AsyncStorageAdapterFactory, create_storage_adapter

# 导入辅助类
from .core.metrics import StorageMetrics
from .core.transaction import TransactionManager
from .core.error_handler import StorageErrorHandler

# 定义包的公共接口
__all__ = [
    # 适配器类
    'SyncStateStorageAdapter',
    'AsyncStateStorageAdapter',
    
    # 工厂类
    'StorageAdapterFactory',
    'AsyncStorageAdapterFactory',
    'create_storage_adapter',
    
    # 辅助类
    'StorageMetrics',
    'TransactionManager',
    'StorageErrorHandler',
]