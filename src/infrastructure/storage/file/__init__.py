"""
文件存储模块

提供基于文件系统的存储后端实现，支持数据持久化和文件管理。
"""

from .file_storage import FileStorage
from .file_config import FileStorageConfig

__all__ = [
    "FileStorage",
    "FileStorageConfig"
]