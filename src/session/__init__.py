"""会话管理模块

提供工作流会话的创建、管理、持久化和恢复功能。
"""

from .manager import ISessionManager, SessionManager
from .store import ISessionStore, FileSessionStore
from .event_collector import IEventCollector, EventCollector
from .player import IPlayer, Player
from .git_manager import IGitManager, GitManager

__all__ = [
    "ISessionManager",
    "SessionManager",
    "ISessionStore",
    "FileSessionStore",
    "IEventCollector",
    "EventCollector",
    "IPlayer",
    "Player",
    "IGitManager",
    "GitManager",
]