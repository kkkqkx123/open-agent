"""
会话服务绑定
"""

from typing import Dict, Any
from src.interfaces.sessions import ISessionService
from src.interfaces.container.core import ServiceLifetime

class SessionServiceBindings:
    """会话服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册会话服务"""
        # 注册会话服务
        def session_service():
            from src.infrastructure.sessions.session_service import SessionService
            return SessionService(config)
        
        container.register_factory(
            ISessionService,
            session_service,
            lifetime=ServiceLifetime.SINGLETON
        )