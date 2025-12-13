"""
日志服务绑定
"""

from typing import Dict, Any
from src.interfaces.logger import ILogger, ILoggerFactory
from src.interfaces.container.core import ServiceLifetime

class LoggerServiceBindings:
    """日志服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册日志服务"""
        # 注册日志工厂
        def logger_factory():
            from src.infrastructure.logger.factory.logger_factory import LoggerFactory
            return LoggerFactory()
        
        container.register_factory(
            ILoggerFactory,
            logger_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册日志服务
        def logger_service():
            logger_factory_instance = container.get(ILoggerFactory)
            return logger_factory_instance.create_logger("application")
        
        container.register_factory(
            ILogger,
            logger_service,
            lifetime=ServiceLifetime.SINGLETON
        )