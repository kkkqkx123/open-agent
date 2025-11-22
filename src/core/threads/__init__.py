"""Threads核心模块初始化"""

from .entities import Thread, ThreadBranch, ThreadSnapshot, ThreadStatus, ThreadType, ThreadMetadata
from .interfaces import IThreadCore, IThreadBranchCore, IThreadSnapshotCore
from .base import ThreadBase
from .factories import ThreadFactory, ThreadBranchFactory, ThreadSnapshotFactory

# 为了向后兼容，保留原有的类名
ThreadCore = ThreadFactory
ThreadBranchCore = ThreadBranchFactory
ThreadSnapshotCore = ThreadSnapshotFactory

__all__ = [
    "Thread",
    "ThreadBranch",
    "ThreadSnapshot",
    "ThreadStatus",
    "ThreadType",
    "ThreadMetadata",
    "IThreadCore",
    "IThreadBranchCore",
    "IThreadSnapshotCore",
    "ThreadBase",
    "ThreadFactory",
    "ThreadBranchFactory",
    "ThreadSnapshotFactory",
    # 向后兼容的别名
    "ThreadCore",
    "ThreadBranchCore",
    "ThreadSnapshotCore",
]