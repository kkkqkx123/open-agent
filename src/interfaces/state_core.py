"""核心状态管理接口定义

定义状态管理系统的核心接口，扩展基础状态接口以支持历史记录、快照和冲突管理功能。
"""

# TYPE_CHECKING：避免运行时循环依赖
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state_interfaces import (
        IStateHistoryManager,
        IStateSnapshotManager,
        IStateSerializer,
        IEnhancedStateManager,
    )
    from src.interfaces.storage_interfaces import (
        IStorageBackend,
        IStorageSerializer,
        IStorageCache,
        IStorageMetrics,
    )
    from ..core.state.adapter_interfaces import (
        IStateStorageAdapter,
        IStorageAdapterFactory,
        IStorageMigration,
    )
    from ..core.state.async_adapter_interfaces import (
        IAsyncStateStorageAdapter,
        IAsyncStorageAdapterFactory,
        IAsyncStorageMigration,
    )
else:
    # 在运行时导入
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
    from ..core.state.adapter_interfaces import (
        IStateStorageAdapter,
        IStorageAdapterFactory,
        IStorageMigration,
    )
    from ..core.state.async_adapter_interfaces import (
        IAsyncStateStorageAdapter,
        IAsyncStorageAdapterFactory,
        IAsyncStorageMigration,
    )

from .entities import (
    ConflictType,
    ConflictResolutionStrategy,
    StateConflict
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
    'IAsyncStateStorageAdapter',
    'IAsyncStorageAdapterFactory',
    'IAsyncStorageMigration',
    
    # 实体类型
    'ConflictType',
    'ConflictResolutionStrategy',
    'StateConflict'
]