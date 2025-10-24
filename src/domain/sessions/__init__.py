"""会话管理模块

提供工作流会话的创建、管理、持久化和恢复功能。
"""

from .store import ISessionStore, FileSessionStore

__all__ = [
    "ISessionStore",
    "FileSessionStore",
]