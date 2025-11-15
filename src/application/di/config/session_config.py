"""会话管理DI配置

负责注册会话管理相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.application.sessions.manager import ISessionManager, SessionManager
from src.application.sessions.git_manager import IGitManager, GitManager, MockGitManager

logger = logging.getLogger(__name__)


class SessionConfigRegistration:
    """会话管理注册类
    
    负责注册会话管理相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册会话管理服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册会话管理服务")
        
        # 注册Git管理器
        container.register_factory(
            IGitManager,
            lambda: GitManager(),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册会话管理器
        container.register_factory(
            ISessionManager,
            lambda: SessionManager(
                thread_service=container.get(
                    "src.application.threads.interfaces.IThreadService"
                ) if container.has_service(
                    "src.application.threads.interfaces.IThreadService"
                ) else None,
                session_store=container.get(
                    "src.domain.sessions.store.ISessionStore"
                ) if container.has_service(
                    "src.domain.sessions.store.ISessionStore"
                ) else None,
                state_manager=container.get(
                    "src.domain.state.interfaces.IStateManager"
                ) if container.has_service(
                    "src.domain.state.interfaces.IStateManager"
                ) else None,
                git_manager=container.get(IGitManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("会话管理服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "git_manager": IGitManager,
            "session_manager": ISessionManager,
        }