"""Repository适配器模块

提供各种存储后端的Repository实现。
"""

# 基类
from .base import BaseRepository
from .sqlite_base import SQLiteBaseRepository
from .memory_base import MemoryBaseRepository
from .file_base import FileBaseRepository

# 工具类
from .utils import JsonUtils, TimeUtils, FileUtils, SQLiteUtils, IdUtils

# 历史记录Repository
from .history import SQLiteHistoryRepository, MemoryHistoryRepository

# 快照Repository
from .snapshot import SQLiteSnapshotRepository, MemorySnapshotRepository, FileSnapshotRepository

# 状态Repository
from .state import SQLiteStateRepository, MemoryStateRepository, FileStateRepository

# 检查点Repository
from .checkpoint import SQLiteCheckpointRepository, MemoryCheckpointRepository, FileCheckpointRepository

__all__ = [
    # 基类
    "BaseRepository",
    "SQLiteBaseRepository", 
    "MemoryBaseRepository",
    "FileBaseRepository",
    
    # 工具类
    "JsonUtils",
    "TimeUtils",
    "FileUtils",
    "SQLiteUtils",
    "IdUtils",
    
    # 历史记录Repository
    "SQLiteHistoryRepository",
    "MemoryHistoryRepository",
    
    # 快照Repository
    "SQLiteSnapshotRepository",
    "MemorySnapshotRepository", 
    "FileSnapshotRepository",
    
    # 状态Repository
    "SQLiteStateRepository",
    "MemoryStateRepository",
    "FileStateRepository",
    
    # 检查点Repository
    "SQLiteCheckpointRepository",
    "MemoryCheckpointRepository",
    "FileCheckpointRepository"
]