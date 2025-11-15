"""检查点核心DI配置

负责注册检查点核心相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.checkpoint.repository import ICheckpointRepository, CheckpointRepository
from src.domain.checkpoint.interfaces import ICheckpointStore

logger = logging.getLogger(__name__)


class CheckpointConfigRegistration:
    """检查点核心注册类
    
    负责注册检查点核心相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册检查点核心服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册检查点核心服务")
        
        # 注册检查点仓储
        container.register_factory(
            ICheckpointRepository,
            lambda: CheckpointRepository(
                checkpoint_store=container.get(
                    ICheckpointStore
                ) if container.has_service(
                    ICheckpointStore
                ) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("检查点核心服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "checkpoint_repository": ICheckpointRepository,
        }