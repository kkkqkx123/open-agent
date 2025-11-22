"""会话核心模块导出"""

from .entities import SessionEntity, UserInteractionEntity, UserRequestEntity
from .interfaces import ISessionCore, ISessionValidator, ISessionStateTransition

__all__ = [
    "SessionEntity",
    "UserInteractionEntity", 
    "UserRequestEntity",
    "ISessionCore",
    "ISessionValidator",
    "ISessionStateTransition"
]