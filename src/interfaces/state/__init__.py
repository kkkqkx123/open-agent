"""状态接口模块

这个模块提供了所有状态相关的接口定义，包括核心状态、工作流状态、历史管理、快照管理等。

架构层次：
- IState: 核心状态接口，纯粹的状态抽象
- IWorkflowState: 工作流状态接口，继承自 IState，添加工作流特定功能
"""

# 核心状态接口
from .interfaces import IState

# 工作流状态接口
from .workflow import IWorkflowState, IWorkflowStateBuilder

# 工作流状态接口（向后兼容，已弃用）
from .workflow import IWorkflowState as LegacyIWorkflowState

# 会话状态接口
from .session import ISessionState, ISessionStateManager

# 历史管理接口
from .history import IStateHistoryManager

# 快照管理接口
from .snapshot import IStateSnapshotManager

# 序列化接口
from .serializer import IStateSerializer

# 增强状态管理接口
from .manager import IStateManager

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

# 注意：具体实现（StateSnapshot等）应该从src.core.state导入，而不是从接口层
# 接口层只负责定义合约，不导出具体实现

# 存储相关接口（统一为异步接口）
from .storage import (
    IStorageBackend,
    IStateStorageAdapter,
    IStorageAdapterFactory,
    IStorageMigration,
    IStorageCache,
    IStorageMetrics
)

__all__ = [
    # 核心状态接口
    'IState',
    'IStateManager',
    
    # 工作流状态接口
    'IWorkflowState',
    'IWorkflowStateBuilder',
    
    # 会话状态接口
    'ISessionState',
    'ISessionStateManager',
    
    # 历史管理接口
    'IStateHistoryManager',
    
    # 快照管理接口
    'IStateSnapshotManager',
    
    # 序列化接口
    'IStateSerializer',
    
    # 增强状态管理接口
    'IStateManager',
    
    # 工厂接口
    'IStateFactory',
    
    # 生命周期管理接口
    'IStateLifecycleManager',
    
    # 实体定义
    'AbstractStateSnapshot',
    'AbstractStateHistoryEntry',
    'AbstractStateConflict',
    'AbstractStateStatistics',
    
    
    # 存储相关接口（统一异步）
    'IStorageBackend',
    'IStateStorageAdapter',
    'IStorageAdapterFactory',
    'IStorageMigration',
    'IStorageCache',
    'IStorageMetrics'
]