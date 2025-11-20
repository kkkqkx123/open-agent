"""存储适配器包

提供状态存储的适配器实现。
"""

# 导入主要的适配器类
from .sync_adapter import SyncStateStorageAdapter
from .async_adapter import AsyncStateStorageAdapter

# 导入工厂类
from .factory import StorageAdapterFactory, AsyncStorageAdapterFactory, create_storage_adapter

# 导入辅助类
from .metrics import StorageMetrics
from .transaction import TransactionManager
from .error_handler import StorageErrorHandler

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