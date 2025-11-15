"""开发环境DI配置

负责注册开发环境特定服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class DevelopmentConfigRegistration:
    """开发环境服务注册类
    
    负责注册开发环境特定的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册开发环境服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册开发环境特定服务")
        
        # 开发环境可以注册调试工具、热重载服务等
        # 这里可以根据需要添加开发环境特定的服务
        
        logger.debug("开发环境特定服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            # 开发环境特定服务类型
        }