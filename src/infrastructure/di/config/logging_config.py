"""日志服务DI配置

负责注册日志系统相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.infrastructure.logger import ILogger, StructuredFileLogger

logger = logging.getLogger(__name__)


class LoggingConfigRegistration:
    """日志服务注册类
    
    负责注册日志系统相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册日志服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册日志系统服务")
        
        # 注册结构化文件日志记录器
        container.register_factory(
            ILogger,
            lambda: StructuredFileLogger(),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("日志系统服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "logger": ILogger,
        }