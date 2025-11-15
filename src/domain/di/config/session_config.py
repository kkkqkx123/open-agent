"""会话核心DI配置

负责注册会话核心相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.sessions.repository import ISessionRepository, SessionRepository

logger = logging.getLogger(__name__)


class SessionConfigRegistration:
    """会话核心注册类
    
    负责注册会话核心相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册会话核心服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册会话核心服务")
        
        # 注册会话仓储
        container.register_factory(
            ISessionRepository,
            lambda: SessionRepository(
                session_store=container.get(
                    "src.domain.sessions.store.ISessionStore"
                ) if container.has_service(
                    "src.domain.sessions.store.ISessionStore"
                ) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("会话核心服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "session_repository": ISessionRepository,
        }