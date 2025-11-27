"""状态存储相关接口模块

这个模块提供了状态存储相关的所有接口定义，包括存储后端、适配器、缓存等。
"""

from .backend import IStorageBackend
from .adapter import IStateStorageAdapter, IStorageAdapterFactory, IStorageMigration
from .cache import IStorageCache
from .metrics import IStorageMetrics
from .migration import IAsyncStorageMigration

__all__ = [
    # 存储后端接口
    'IStorageBackend',
    
    # 存储适配器接口
    'IStateStorageAdapter',
    'IStorageAdapterFactory',
    
    # 缓存接口
    'IStorageCache',
    
    # 指标接口
    'IStorageMetrics',
    
    # 迁移接口
    'IStorageMigration',
    'IAsyncStorageMigration'
]