"""基础设施层状态存储模块

提供状态存储的具体技术实现，包括快照存储、历史存储等。
这些实现为状态管理系统提供底层技术支持。

使用方式：
- 快照存储：from src.infrastructure.state.snapshots import MemorySnapshotStorage
- 历史存储：from src.infrastructure.state.history import MemoryHistoryStorage
"""

# 导出快照存储相关
from .snapshots.snapshot_storage import (
    StateSnapshot,
    ISnapshotStorage,
    MemorySnapshotStorage,
    FileSnapshotStorage
)

# 导出历史存储相关
from .history.history_storage import (
    HistoryEntry,
    IHistoryStorage,
    MemoryHistoryStorage,
    SQLiteHistoryStorage
)

# 导出所有公共符号
__all__ = [
    # 快照存储
    "StateSnapshot",
    "ISnapshotStorage",
    "MemorySnapshotStorage",
    "FileSnapshotStorage",
    
    # 历史存储
    "HistoryEntry",
    "IHistoryStorage",
    "MemoryHistoryStorage",
    "SQLiteHistoryStorage"
]