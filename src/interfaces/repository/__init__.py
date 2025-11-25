"""Repository接口层

定义数据访问层的Repository接口，实现状态与存储的解耦。
"""

from .state import IStateRepository
from .history import IHistoryRepository  
from .snapshot import ISnapshotRepository
from .checkpoint import ICheckpointRepository
from .session import ISessionRepository

__all__ = [
    "IStateRepository",
    "IHistoryRepository", 
    "ISnapshotRepository",
    "ICheckpointRepository",
    "ISessionRepository",
]