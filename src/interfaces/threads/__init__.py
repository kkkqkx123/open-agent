"""线程管理接口定义"""
from .collaboration import IThreadCollaborationService
from .service import IThreadService
from .branch_service import IThreadBranchService
from .storage import IThreadRepository, IThreadBranchRepository, IThreadSnapshotRepository
from .checkpoint import (
    IThreadCheckpointStorage,
    IThreadCheckpointManager,
    IThreadCheckpointSerializer,
    IThreadCheckpointPolicy,
    # 异常定义
    CheckpointError,
    CheckpointValidationError,
    CheckpointNotFoundError,
    CheckpointStorageError,
    CheckpointConflictError,
    CheckpointTimeoutError,
    CheckpointQuotaExceededError,
    CheckpointCorruptionError,
    CheckpointVersionError,
    CheckpointConfigurationError,
    CheckpointHookError,
    CheckpointCacheError,
    CheckpointResourceError,
)
from .entities import IThread, IThreadBranch, IThreadSnapshot

__all__ = [
    "IThreadBranchRepository",
    "IThreadSnapshotRepository",
    "IThreadCollaborationService",
    "IThreadService",
    "IThreadBranchService",
    "IThreadRepository",
    "IThreadCheckpointStorage",
    "IThreadCheckpointManager",
    "IThreadCheckpointSerializer",
    "IThreadCheckpointPolicy",
    "IThread",
    "IThreadBranch",
    "IThreadSnapshot",
    # 异常类型
    "CheckpointError",
    "CheckpointValidationError",
    "CheckpointNotFoundError",
    "CheckpointStorageError",
    "CheckpointConflictError",
    "CheckpointTimeoutError",
    "CheckpointQuotaExceededError",
    "CheckpointCorruptionError",
    "CheckpointVersionError",
    "CheckpointConfigurationError",
    "CheckpointHookError",
    "CheckpointCacheError",
    "CheckpointResourceError",
]