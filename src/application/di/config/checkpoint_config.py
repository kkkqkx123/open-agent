"""检查点管理DI配置

负责注册检查点管理相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.application.checkpoint.manager import ICheckpointManager, CheckpointManager
from src.domain.checkpoint.interfaces import ICheckpointStore
from src.domain.checkpoint.config import CheckpointConfig

logger = logging.getLogger(__name__)


class CheckpointConfigRegistration:
    """检查点管理注册类
    
    负责注册检查点管理相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册检查点管理服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册检查点管理服务")
        
        # 注册检查点管理器
        container.register_factory(
            ICheckpointManager,
            lambda: CheckpointManager(
                checkpoint_store=container.get(ICheckpointStore),
                config=CheckpointConfig()
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("检查点管理服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "checkpoint_manager": ICheckpointManager,
        }