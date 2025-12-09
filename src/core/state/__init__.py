"""集中化状态管理模块

提供统一的状态管理功能，整合了接口、核心组件、实现和存储适配器。
"""

from typing import Any, Dict, List, Optional, Union

# 工具状态类型枚举 - 需要从中央接口层获取或重新定义
from enum import Enum

class StateType(Enum):
    """状态类型枚举"""
    CONNECTION = "connection"
    SESSION = "session"
    BUSINESS = "business"
    CACHE = "cache"

# 实体定义（具体实现）
from .entities import (
    StateSnapshot,
    StateHistoryEntry,
    StateConflict,
    ConflictType,
    ConflictResolutionStrategy,
    StateStatistics,
    StateDiff
)

# 核心组件
from .core import (
    # 基础实现
    BaseState,
    BaseStateSerializer,
    BaseStateValidator,
    BaseStateLifecycleManager,
    BaseStateHistoryManager,
    BaseStateSnapshotManager,
    BaseStateManager,
    StateValidationMixin,
    
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
    
    # 线程状态实现
    ThreadState,
    BranchThreadState,
    
    # 检查点状态实现
    CheckpointState,
    AutoCheckpointState
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
    StateHistoryPlayer
)

# 快照管理
from .snapshots import (
    StateSnapshotManager,
    StateSnapshotCreator,
    StateSnapshotRestorer
)

# 工具类
# from .utils import (
#     # 这里可以导入其他工具类
# )

# 便捷函数
def create_state_manager(
    config: Optional[Dict[str, Any]] = None,
    storage_adapter: Optional[Any] = None
) -> StateManager:
    """创建状态管理器的便捷函数
    
    Args:
        config: 配置字典，如果为None则使用默认配置
        storage_adapter: 存储适配器，如果为None则使用默认内存适配器
        
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
    
    # 如果没有提供存储适配器，创建一个默认的内存适配器
    if storage_adapter is None:
        # 创建一个简单的内存存储适配器
        class _SimpleMemoryAdapter:  # type: ignore[no-untyped-call]
            """简单的内存存储适配器实现"""
            def __init__(self) -> None:
                self._data: Dict[str, Union[str, bytes]] = {}
            
            def get(self, key: str) -> Optional[Union[str, bytes]]:
                return self._data.get(key)
            
            def save(self, key: str, data: Union[str, bytes]) -> bool:
                self._data[key] = data
                return True
            
            def delete(self, key: str) -> bool:
                if key in self._data:
                    del self._data[key]
                    return True
                return False
            
            def list(self, filters: Optional[Dict[str, Any]] = None) -> List[str]:
                return list(self._data.keys())
            
            def get_statistics(self) -> Dict[str, Any]:
                return {'total_items': len(self._data), 'type': 'memory'}
        
        storage_adapter = _SimpleMemoryAdapter()  # type: ignore[assignment]
    
    return StateManager(config, storage_adapter=storage_adapter)


def create_workflow_state(**kwargs: Any) -> WorkflowState:
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


def create_session_state(**kwargs: Any) -> SessionState:
    """创建会话状态的便捷函数
    
    Args:
        **kwargs: 状态参数
        
    Returns:
        会话状态实例
    """
    return SessionState(**kwargs)


def create_thread_state(**kwargs: Any) -> ThreadState:
    """创建线程状态的便捷函数
    
    Args:
        **kwargs: 状态参数
        
    Returns:
        线程状态实例
    """
    return ThreadState(**kwargs)


def create_checkpoint_state(**kwargs: Any) -> CheckpointState:
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
    
    # 注意：接口定义应该从src.interfaces.state导入，不在此模块导出
    # 工具状态类型（从interfaces.tools导入）
    "StateType",
    
    # 实体定义（具体实现）
    "StateSnapshot",
    "StateHistoryEntry",
    "StateConflict",
    "ConflictType",
    "ConflictResolutionStrategy",
    "StateStatistics",
    "StateDiff",
    
    # 核心组件
    "BaseState",
    "BaseStateSerializer",
    "BaseStateValidator",
    "BaseStateLifecycleManager",
    "BaseStateHistoryManager",
    "BaseStateSnapshotManager",
    "BaseStateManager",
    "StateValidationMixin",
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
    "ThreadState",
    "BranchThreadState",
    "CheckpointState",
    "AutoCheckpointState",
    
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
    
    # 快照管理
    "StateSnapshotManager",
    "StateSnapshotCreator",
    "StateSnapshotRestorer",
    
    # 便捷函数
    "create_state_manager",
    "create_workflow_state",
    "create_tool_state",
    "create_session_state",
    "create_thread_state",
    "create_checkpoint_state"
]