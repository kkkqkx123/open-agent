"""状态管理模块

提供统一的状态管理功能，支持不同类型的状态转换和持久化。
"""

from .interfaces import (
    IStateManager,
    IEnhancedStateManager,
    IStateCollaborationManager,
    ConflictType,
    ConflictResolutionStrategy
)

__all__ = [
    "IStateManager",
    "IEnhancedStateManager",
    "IStateCollaborationManager",
    "ConflictType",
    "ConflictResolutionStrategy"
]