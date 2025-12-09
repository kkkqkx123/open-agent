"""存储后端接口层

提供所有存储相关的抽象接口定义。
"""

from .storage import IStorage, ISessionStorage, IThreadStorage
from .backend import IStorageBackend, IStorageProvider

__all__ = [
    "IStorage",
    "ISessionStorage", 
    "IThreadStorage",
    "IStorageBackend",
    "IStorageProvider"
]