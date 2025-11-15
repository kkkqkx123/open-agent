"""线程核心DI配置

负责注册线程核心相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.threads.interfaces import IThreadRepository
from src.domain.threads.repository import ThreadRepository
from src.infrastructure.threads.metadata_store import IThreadMetadataStore

logger = logging.getLogger(__name__)


class ThreadConfigRegistration:
    """线程核心注册类
    
    负责注册线程核心相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册线程核心服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册线程核心服务")
        
        # 注册线程仓储
        container.register_factory(
            IThreadRepository,
            lambda: ThreadRepository(
                metadata_store=container.get(IThreadMetadataStore)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("线程核心服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "thread_repository": IThreadRepository,
        }