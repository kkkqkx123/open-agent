"""
日志服务绑定
"""

from typing import Dict, Any
from src.interfaces.logger import ILogger
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime
from src.services.logger.logger_service import LoggerService

class LoggerServiceBindings:
    """日志服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册日志服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册基础设施层日志记录器
        def infrastructure_logger_factory():
            from src.infrastructure.logger.factory.logger_factory import LoggerFactory
            factory = LoggerFactory()
            return factory.get_logger("infrastructure", config=config.get("logger", {}))
        
        container.register_factory(
            ILogger,
            infrastructure_logger_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册业务层日志服务
        def logger_service_factory():
            from src.services.logger.logger_service import LoggerService
            infra_logger = container.get(ILogger)
            return LoggerService("default", infra_logger, config.get("logger", {}))
        
        container.register_factory(
            LoggerService,
            logger_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )