"""
检查点接口模块

导出所有检查点相关的接口定义。
"""

from .service import ICheckpointService
from .saver import ICheckpointSaver
from .exceptions import (
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

# 仓库接口使用现有的 src.interfaces.repository.checkpoint.ICheckpointRepository
from src.interfaces.repository.checkpoint import ICheckpointRepository

__all__ = [
    "ICheckpointService",
    "ICheckpointRepository",
    "ICheckpointSaver",
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