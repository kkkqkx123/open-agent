"""回放管理DI配置

负责注册回放管理相关服务。
"""

import logging
from typing import Dict, Type, TYPE_CHECKING

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.application.replay.manager import IReplayManager, ReplayManager

if TYPE_CHECKING:
    from src.domain.history.interfaces import IHistoryManager
    from src.application.sessions.manager import ISessionManager

logger = logging.getLogger(__name__)


class ReplayConfigRegistration:
    """回放管理注册类
    
    负责注册回放管理相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册回放管理服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册回放管理服务")
        
        # 注册回放管理器
        container.register_factory(
            IReplayManager,
            lambda: ReplayManager(
                history_manager=container.get(
                    Type["IHistoryManager"]
                ) if container.has_service(
                    Type["IHistoryManager"]
                ) else None,
                session_manager=container.get(
                    Type["ISessionManager"]
                ) if container.has_service(
                    Type["ISessionManager"]
                ) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("回放管理服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "replay_manager": IReplayManager,
        }