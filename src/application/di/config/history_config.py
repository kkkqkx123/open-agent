"""历史管理DI配置

负责注册历史管理相关服务。
"""

import logging
from typing import Dict, Type
from pathlib import Path

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.application.history.manager import IHistoryManager, HistoryManager
from src.infrastructure.history.storage.file_storage import FileHistoryStorage

logger = logging.getLogger(__name__)


class HistoryConfigRegistration:
    """历史管理注册类
    
    负责注册历史管理相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册历史管理服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册历史管理服务")
        
        # 注册历史管理器
        container.register_factory(
            IHistoryManager,
            lambda: HistoryManager(
                storage=FileHistoryStorage(base_path=Path("./history_data"))
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("历史管理服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "history_manager": IHistoryManager,
        }