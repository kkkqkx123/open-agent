"""历史核心DI配置

负责注册历史核心相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.history.repository import IHistoryRepository, HistoryRepository
from src.domain.history.interfaces import IHistoryManager

logger = logging.getLogger(__name__)


class HistoryConfigRegistration:
    """历史核心注册类
    
    负责注册历史核心相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册历史核心服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册历史核心服务")
        
        # 注册历史仓储
        container.register_factory(
            IHistoryRepository,
            lambda: HistoryRepository(
                history_store=container.get(
                    IHistoryManager
                ) if container.has_service(
                    IHistoryManager
                ) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("历史核心服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "history_repository": IHistoryRepository,
        }