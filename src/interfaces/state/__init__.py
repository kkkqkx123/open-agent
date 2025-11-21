"""状态接口模块

这个模块提供了所有状态相关的接口定义，包括核心状态、工作流状态、历史管理、快照管理等。
"""

# 核心状态接口
from .interfaces import IState, IStateManager

# 工作流状态接口
from .workflow import IWorkflowState

# 历史管理接口
from .history import IStateHistoryManager

# 快照管理接口
from .snapshot import IStateSnapshotManager

# 序列化接口
from .serializer import IStateSerializer

# 增强状态管理接口
from .enhanced import IEnhancedStateManager

# 工厂接口
from .factory import IStateFactory

# 生命周期管理接口
from .lifecycle import IStateLifecycleManager

# 实体定义
from .entities import (
    AbstractStateSnapshot,
    AbstractStateHistoryEntry,
    AbstractStateConflict,
    AbstractStateStatistics
)

# 具体实现（从核心模块导入）
from src.core.state.entities import (
    StateSnapshot,
    StateHistoryEntry,
    StateConflict,
    ConflictType,
    ConflictResolutionStrategy,
    StateStatistics,
    StateDiff
)

# 存储相关接口
from .storage import (
    IStorageBackend,
    IStateStorageAdapter,
    IStorageAdapterFactory,
    IStorageMigration,
    IAsyncStateStorageAdapter,
    IAsyncStorageAdapterFactory,
    IAsyncStorageMigration,
    IStorageCache,
    IStorageMetrics
)

__all__ = [
    # 核心状态接口
    'IState',
    'IStateManager',
    
    # 工作流状态接口
    'IWorkflowState',
    
    # 历史管理接口
    'IStateHistoryManager',
    
    # 快照管理接口
    'IStateSnapshotManager',
    
    # 序列化接口
    'IStateSerializer',
    
    # 增强状态管理接口
    'IEnhancedStateManager',
    
    # 工厂接口
    'IStateFactory',
    
    # 生命周期管理接口
    'IStateLifecycleManager',
    
    # 实体定义
    'AbstractStateSnapshot',
    'AbstractStateHistoryEntry',
    'AbstractStateConflict',
    'AbstractStateStatistics',
    
    # 具体实现
    'StateSnapshot',
    'StateHistoryEntry',
    'StateConflict',
    'StateStatistics',
    'StateDiff',
    'ConflictType',
    'ConflictResolutionStrategy',
    
    # 存储相关接口
    'IStorageBackend',
    'IStateStorageAdapter',
    'IStorageAdapterFactory',
    'IStorageMigration',
    'IAsyncStateStorageAdapter',
    'IAsyncStorageAdapterFactory',
    'IAsyncStorageMigration',
    'IStorageCache',
    'IStorageMetrics'
]