"""核心状态管理接口定义

定义状态管理系统的核心接口，扩展基础状态接口以支持历史记录和快照功能。
"""

# 导入所有接口
from .state_interfaces import (
    IStateHistoryManager,
    IStateSnapshotManager,
    IStateSerializer,
    IEnhancedStateManager,
)

from .storage_interfaces import (
    IStorageBackend,
    IStorageSerializer,
    IStorageCache,
    IStorageMetrics,
)

from .adapter_interfaces import (
    IStateStorageAdapter,
    IStorageAdapterFactory,
    IStorageMigration,
)

# 前向引用的类型提示
__all__ = [
    # 状态管理接口
    'IStateHistoryManager',
    'IStateSnapshotManager',
    'IStateSerializer',
    'IEnhancedStateManager',
    
    # 存储接口
    'IStorageBackend',
    'IStorageSerializer',
    'IStorageCache',
    'IStorageMetrics',
    
    # 适配器接口
    'IStateStorageAdapter',
    'IStorageAdapterFactory',
    'IStorageMigration',
]