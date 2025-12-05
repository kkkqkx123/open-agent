"""Repository接口层

定义数据访问层的Repository接口，实现状态与存储的解耦。
"""

from .state import IStateRepository
from .history import IHistoryRepository  
from .snapshot import ISnapshotRepository
from .checkpoint import ICheckpointRepository
from .session import ISessionRepository
from .exceptions import (
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryOperationError,
    RepositoryConnectionError,
    RepositoryTransactionError,
    RepositoryValidationError,
    RepositoryTimeoutError,
)

__all__ = [
    # 接口
    "IStateRepository",
    "IHistoryRepository", 
    "ISnapshotRepository",
    "ICheckpointRepository",
    "ISessionRepository",
    # 异常
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
    "RepositoryValidationError",
    "RepositoryTimeoutError",
]