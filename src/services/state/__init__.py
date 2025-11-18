"""状态管理服务模块

提供状态管理的服务层实现，包括状态管理、历史记录、快照和持久化服务。
"""

from .manager import EnhancedStateManager, StateWrapper
from .history import StateHistoryService, StateHistoryAnalyzer
from .snapshots import StateSnapshotService, SnapshotScheduler
from .persistence import StatePersistenceService, StateBackupService

__all__ = [
    # 状态管理
    "EnhancedStateManager",
    "StateWrapper",
    
    # 历史管理
    "StateHistoryService",
    "StateHistoryAnalyzer",
    
    # 快照管理
    "StateSnapshotService",
    "SnapshotScheduler",
    
    # 持久化
    "StatePersistenceService",
    "StateBackupService"
]