"""线程管理接口定义"""
from .collaboration import IThreadCollaborationService
from .service import IThreadService
from .branch_service import IThreadBranchService
from .coordinator_service import IThreadCoordinatorService
from .storage import IThreadRepository, IThreadBranchRepository, IThreadSnapshotRepository
from .checkpoint import (
    IThreadCheckpointStorage,
    IThreadCheckpointManager,
    IThreadCheckpointSerializer,
    IThreadCheckpointPolicy
)
from .checkpoint_adapter import (
    LegacyCheckpointStoreAdapter,
    LegacyCheckpointManagerAdapter,
    LegacyCheckpointSerializerAdapter,
    LegacyCheckpointPolicyAdapter,
    CheckpointCompatibilityWrapper
)

__all__ = [
    "IThreadBranchRepository",
    "IThreadSnapshotRepository",
    "IThreadCollaborationService",
    "IThreadService",
    "IThreadBranchService",
    "IThreadCoordinatorService",
    "IThreadRepository",
    "IThreadCheckpointStorage",
    "IThreadCheckpointManager",
    "IThreadCheckpointSerializer",
    "IThreadCheckpointPolicy",
    "LegacyCheckpointStoreAdapter",
    "LegacyCheckpointManagerAdapter",
    "LegacyCheckpointSerializerAdapter",
    "LegacyCheckpointPolicyAdapter",
    "CheckpointCompatibilityWrapper",
]