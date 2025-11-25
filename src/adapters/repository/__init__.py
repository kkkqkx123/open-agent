"""Repository适配器层

实现Repository接口的具体适配器，支持多种存储后端。
"""

from .state import *
from .history import *
from .snapshot import *
from .checkpoint import *

__all__ = [
    # State Repository
    "SQLiteStateRepository",
    "MemoryStateRepository", 
    "FileStateRepository",
    
    # History Repository
    "SQLiteHistoryRepository",
    "MemoryHistoryRepository",
    "FileHistoryRepository",
    
    # Snapshot Repository
    "SQLiteSnapshotRepository", 
    "MemorySnapshotRepository",
    "FileSnapshotRepository",
    
    # Checkpoint Repository
    "SQLiteCheckpointRepository",
    "MemoryCheckpointRepository",
    "FileCheckpointRepository"
]