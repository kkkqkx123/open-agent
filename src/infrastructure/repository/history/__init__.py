"""历史Repository模块

提供符合IHistoryRepository接口的历史记录存储实现。
"""

from .memory_repository import MemoryHistoryRepository
from .sqlite_repository import SQLiteHistoryRepository

__all__ = [
    "MemoryHistoryRepository",
    "SQLiteHistoryRepository"
]