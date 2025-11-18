"""状态适配器模块

提供状态管理的适配器实现，包括迁移适配器和向后兼容性支持。
"""

from .migration_adapter import (
    LegacyStateManagerAdapter,
    LegacyHistoryManagerAdapter,
    LegacySnapshotStoreAdapter,
    StateMigrationService,
    migrate_to_new_architecture
)

__all__ = [
    # 迁移适配器
    "LegacyStateManagerAdapter",
    "LegacyHistoryManagerAdapter", 
    "LegacySnapshotStoreAdapter",
    "StateMigrationService",
    
    # 便捷函数
    "migrate_to_new_architecture"
]