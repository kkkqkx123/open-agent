"""存储适配器模块

提供Repository层和Storage Backend层之间的统一适配器实现。
"""

from .storage_adapter import StorageAdapter
from .data_transformer import (
    DefaultDataTransformer,
    StateDataTransformer,
    HistoryDataTransformer,
    SnapshotDataTransformer
)
from .config_manager import (
    StorageConfigManager,
    get_global_config_manager,
    set_global_config_manager
)

__all__ = [
    "StorageAdapter",
    "DefaultDataTransformer",
    "StateDataTransformer",
    "HistoryDataTransformer",
    "SnapshotDataTransformer",
    "StorageConfigManager",
    "get_global_config_manager",
    "set_global_config_manager"
]