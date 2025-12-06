"""Thread检查点模块

提供Thread检查点的完整领域实现，基于统一的checkpoint模型。
"""

from .service import ThreadCheckpointService
from .extensions import ThreadCheckpointExtension
from .adapters import ThreadCheckpointRepositoryAdapter

# 重新导出核心模型
from src.core.checkpoint.models import (
    Checkpoint,
    CheckpointStatus,
    CheckpointType,
    CheckpointMetadata,
    CheckpointStatistics
)

# 重新导出接口
from src.core.threads.interfaces import IThreadCheckpointService

__all__ = [
    # 服务类
    "ThreadCheckpointService",
    
    # 扩展功能
    "ThreadCheckpointExtension",
    
    # 适配器
    "ThreadCheckpointRepositoryAdapter",
    
    # 接口
    "IThreadCheckpointService",
    
    # 核心模型
    "Checkpoint",
    "CheckpointStatus",
    "CheckpointType",
    "CheckpointMetadata",
    "CheckpointStatistics",
]