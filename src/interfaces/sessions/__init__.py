"""会话接口模块导出"""

from .service import ISessionService
from ..repository.session import ISessionRepository
from .entities import ISession, IUserRequest, IUserInteraction, ISessionContext

__all__ = [
    "ISessionService",
    "ISessionRepository",
    "ISession",
    "IUserRequest",
    "IUserInteraction",
    "ISessionContext",
]