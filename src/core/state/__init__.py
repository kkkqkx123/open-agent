"""核心状态管理模块

提供状态管理的核心接口、实体和基础实现。
"""

from src.interfaces.state import (
    IStateHistoryManager,
    IStateSnapshotManager,
    IStateSerializer,
    IEnhancedStateManager
)

from .entities import (
    StateSnapshot,
    StateHistoryEntry,
    StateDiff,
    StateStatistics,
    ConflictType,
    ConflictResolutionStrategy,
    StateConflict
)

from .base import (
    BaseStateSerializer,
    BaseStateHistoryManager,
    BaseStateSnapshotManager,
    BaseStateManager,
    StateValidationMixin
)

__all__ = [
    # 接口
    "IStateHistoryManager",
    "IStateSnapshotManager", 
    "IStateSerializer",
    "IEnhancedStateManager",
    
    # 实体
    "StateSnapshot",
    "StateHistoryEntry",
    "StateDiff",
    "StateStatistics",
    "ConflictType",
    "ConflictResolutionStrategy",
    "StateConflict",
    
    # 基础实现
    "BaseStateSerializer",
    "BaseStateHistoryManager",
    "BaseStateSnapshotManager",
    "BaseStateManager",
    "StateValidationMixin"
]