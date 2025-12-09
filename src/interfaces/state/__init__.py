"""状态接口模块

这个模块提供了所有状态相关的接口定义，包括核心状态、工作流状态、历史管理、快照管理等。

架构层次：
- IState: 核心状态接口，纯粹的状态抽象
- IWorkflowState: 工作流状态接口，继承自 IState，添加工作流特定功能
"""

# 核心状态接口
from .base import IState
from .cache import IStateCache

# 工作流状态接口
from .workflow import IWorkflowState, IWorkflowStateBuilder

# 会话状态接口
from .session import ISessionState
from .session_manager import ISessionStateManager

# 历史管理接口
from .history import IStateHistoryManager

# 快照管理接口
from .snapshot import IStateSnapshotManager

# 增强状态管理接口
from .manager import IStateManager

# 序列化器接口
from .serializer import IStateSerializer

# 工厂接口
from .factory import IStateFactory

# 生命周期管理接口
from .lifecycle import IStateLifecycleManager

# 实体接口定义
from .entities import (
    IStateSnapshot,
    IStateHistoryEntry,
    IStateConflict,
    IStateStatistics
)

# 注意：具体实现（StateSnapshot等）应该从src.core.state导入，而不是从接口层
# 接口层只负责定义合约，不导出具体实现

# 异常定义
from .exceptions import (
    StateException,
    StateNotFoundError,
    StateValidationError,
    StateConflictError,
    StateSerializationError,
    StateCacheError
)

__all__ = [
    # 核心状态接口
    'IState',
    'IStateCache',
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
    
    # 增强状态管理接口
    'IStateManager',
    
    # 序列化器接口
    'IStateSerializer',
    
    # 工厂接口
    'IStateFactory',
    
    # 生命周期管理接口
    'IStateLifecycleManager',
    
    # 实体接口定义
    'IStateSnapshot',
    'IStateHistoryEntry',
    'IStateConflict',
    'IStateStatistics',
    
    # 异常定义
    'StateException',
    'StateNotFoundError',
    'StateValidationError',
    'StateConflictError',
    'StateSerializationError',
    'StateCacheError'
]