"""集中化状态管理模块

提供统一的状态管理功能，整合了接口、核心组件、实现和存储适配器。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

# 接口定义
from .interfaces import (
    # 基础接口
    IState,
    IStateManager,
    IStateSerializer,
    IStateValidator,
    IStateLifecycleManager,
    IStateCache,
    IStateStorageAdapter,
    
    # 工作流状态接口
    IWorkflowState,
    IWorkflowStateBuilder,
    
    # 工具状态接口
    IToolState,
    IToolStateManager,
    IToolStateBuilder,
    StateType,
    
    # 会话状态接口
    ISessionState,
    ISessionStateManager,
    
    # 线程状态接口
    IThreadState,
    IThreadStateManager,
    
    # 检查点状态接口
    ICheckpointState,
    ICheckpointStateManager
)

# 核心组件
from .core import (
    # 基础实现
    BaseState,
    BaseStateSerializer,
    BaseStateValidator,
    BaseStateLifecycleManager,
    
    # 状态管理器
    StateManager
)

# 缓存适配器
from .core.cache_adapter import (
    StateCacheAdapter,
    NoOpCacheAdapter,
    TieredStateCacheAdapter
)

# 具体实现
from .implementations import (
    # 基础实现
    BaseStateImpl,
    
    # 工作流状态实现
    WorkflowState,
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    MessageManager,
    MessageRole,
    
    # 工具状态实现
    ToolState,
    ConnectionState,
    CacheState,
    
    # 会话状态实现
    SessionState,
    UserSessionState,
    
    # 线程状态实现
    ThreadState,
    BranchThreadState,
    
    # 检查点状态实现
    CheckpointState,
    AutoCheckpointState
)

# 存储适配器
from .storage import (
    MemoryStateAdapter,
    SQLiteStateAdapter,
    FileStateAdapter
)

# 工厂类
from .factories import (
    StateFactory,
    StateManagerFactory,
    StateAdapterFactory
)

# 构建器类
from .builders import (
    StateBuilder,
    WorkflowStateBuilder
)

# 历史管理
from .history import (
    StateHistoryManager,
    StateHistoryRecorder,
    StateHistoryPlayer,
    IHistoryStorage,
    MemoryHistoryStorage,
    SQLiteHistoryStorage
)

# 快照管理
from .snapshots import (
    StateSnapshotManager,
    StateSnapshotCreator,
    StateSnapshotRestorer,
    ISnapshotStorage,
    MemorySnapshotStorage,
    FileSnapshotStorage
)

# 工具类
# from .utils import (
#     # 这里可以导入其他工具类
# )

# 便捷函数
def create_state_manager(config: Optional[Dict[str, Any]] = None) -> StateManager:
    """创建状态管理器的便捷函数
    
    Args:
        config: 配置字典，如果为None则使用默认配置
        
    Returns:
        状态管理器实例
    """
    if config is None:
        config = {
            'serializer': {
                'format': 'json',
                'compression': True
            },
            'validation': {
                'strict_mode': False
            },
            'cache': {
                'enabled': True,
                'max_size': 1000,
                'ttl': 300
            },
            'storage': {
                'type': 'memory'
            }
        }
    
    return StateManager(config)


def create_workflow_state(**kwargs) -> WorkflowState:
    """创建工作流状态的便捷函数
    
    Args:
        **kwargs: 状态参数
        
    Returns:
        工作流状态实例
    """
    return WorkflowState(**kwargs)


def create_tool_state(state_type: StateType = StateType.BUSINESS, **kwargs) -> ToolState:
    """创建工具状态的便捷函数
    
    Args:
        state_type: 状态类型
        **kwargs: 状态参数
        
    Returns:
        工具状态实例
    """
    kwargs['state_type'] = state_type
    return ToolState(**kwargs)


def create_session_state(**kwargs) -> SessionState:
    """创建会话状态的便捷函数
    
    Args:
        **kwargs: 状态参数
        
    Returns:
        会话状态实例
    """
    return SessionState(**kwargs)


def create_thread_state(**kwargs) -> ThreadState:
    """创建线程状态的便捷函数
    
    Args:
        **kwargs: 状态参数
        
    Returns:
        线程状态实例
    """
    return ThreadState(**kwargs)


def create_checkpoint_state(**kwargs) -> CheckpointState:
    """创建检查点状态的便捷函数
    
    Args:
        **kwargs: 状态参数
        
    Returns:
        检查点状态实例
    """
    return CheckpointState(**kwargs)


# 版本信息
__version__ = "1.0.0"
__author__ = "状态管理团队"
__description__ = "集中化状态管理系统"

# 导出所有公共符号
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__description__",
    
    # 接口定义
    "IState",
    "IStateManager",
    "IStateSerializer",
    "IStateValidator",
    "IStateLifecycleManager",
    "IStateCache",
    "IStateStorageAdapter",
    "IWorkflowState",
    "IWorkflowStateBuilder",
    "IToolState",
    "IToolStateManager",
    "IToolStateBuilder",
    "StateType",
    "ISessionState",
    "ISessionStateManager",
    "IThreadState",
    "IThreadStateManager",
    "ICheckpointState",
    "ICheckpointStateManager",
    
    # 核心组件
    "BaseState",
    "BaseStateSerializer",
    "BaseStateValidator",
    "BaseStateLifecycleManager",
    "StateManager",
    "StateCacheAdapter",
    "NoOpCacheAdapter",
    "TieredStateCacheAdapter",
    
    # 具体实现
    "BaseStateImpl",
    "WorkflowState",
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "MessageManager",
    "MessageRole",
    "ToolState",
    "ConnectionState",
    "CacheState",
    "SessionState",
    "UserSessionState",
    "ThreadState",
    "BranchThreadState",
    "CheckpointState",
    "AutoCheckpointState",
    
    # 存储适配器
    "MemoryStateAdapter",
    "SQLiteStateAdapter",
    "FileStateAdapter",
    
    # 工厂类
    "StateFactory",
    "StateManagerFactory",
    "StateAdapterFactory",
    
    # 构建器类
    "StateBuilder",
    "WorkflowStateBuilder",
    
    # 历史管理
    "StateHistoryManager",
    "StateHistoryRecorder",
    "StateHistoryPlayer",
    "IHistoryStorage",
    "MemoryHistoryStorage",
    "SQLiteHistoryStorage",
    
    # 快照管理
    "StateSnapshotManager",
    "StateSnapshotCreator",
    "StateSnapshotRestorer",
    "ISnapshotStorage",
    "MemorySnapshotStorage",
    "FileSnapshotStorage",
    
    # 便捷函数
    "create_state_manager",
    "create_workflow_state",
    "create_tool_state",
    "create_session_state",
    "create_thread_state",
    "create_checkpoint_state"
]