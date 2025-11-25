"""会话接口模块导出"""

from .service import ISessionService
from ..repository.session import ISessionRepository

__all__ = [
    "ISessionService",
    "ISessionRepository",
]