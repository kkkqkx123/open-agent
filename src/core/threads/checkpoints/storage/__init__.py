"""Thread检查点存储模块

提供Thread检查点的完整领域实现，包括模型、仓储、服务和异常。
"""

from .models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointType,
    CheckpointMetadata,
    CheckpointStatistics
)

from .repository import (
    IThreadCheckpointRepository,
    ThreadCheckpointRepository,
    RepositoryError
)

from .service import (
    ThreadCheckpointDomainService,
    CheckpointManager
)

# 注意：ThreadCheckpointManager 在 ..manager.py 中定义，这里不导入以避免循环依赖
# 使用时应直接导入 from src.core.threads.checkpoints.manager import ThreadCheckpointManager

from .exceptions import (
    CheckpointDomainError,
    CheckpointNotFoundError,
    CheckpointValidationError,
    CheckpointRestoreError,
    CheckpointStorageError,
    CheckpointLimitExceededError,
    CheckpointSizeExceededError,
    CheckpointExpiredError,
    CheckpointCorruptedError,
    CheckpointBackupError,
    CheckpointChainError,
    ThreadNotFoundError,
    ThreadStateError,
    CheckpointConcurrencyError,
    CheckpointPermissionError,
    CheckpointConfigurationError
)

__all__ = [
    # 模型类
    "ThreadCheckpoint",
    "CheckpointStatus",
    "CheckpointType",
    "CheckpointMetadata",
    "CheckpointStatistics",
    
    # 仓储类
    "IThreadCheckpointRepository",
    "ThreadCheckpointRepository",
    "RepositoryError",
    
    # 服务类
    "ThreadCheckpointDomainService",
    "CheckpointManager",
    
    # 异常类
    "CheckpointDomainError",
    "CheckpointNotFoundError",
    "CheckpointValidationError",
    "CheckpointRestoreError",
    "CheckpointStorageError",
    "CheckpointLimitExceededError",
    "CheckpointSizeExceededError",
    "CheckpointExpiredError",
    "CheckpointCorruptedError",
    "CheckpointBackupError",
    "CheckpointChainError",
    "ThreadNotFoundError",
    "ThreadStateError",
    "CheckpointConcurrencyError",
    "CheckpointPermissionError",
    "CheckpointConfigurationError",
]