"""API服务DI配置

负责注册API相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class APIConfigRegistration:
    """API服务注册类
    
    负责注册API相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册API服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册API服务")
        
        # API路由器在FastAPI应用中注册，不在DI容器中注册
        logger.debug("API服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        # API路由器不作为可注册的服务类型返回
        return {}