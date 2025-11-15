"""测试环境DI配置

负责注册测试环境特定服务。
"""

import logging
from typing import Dict, Type
from unittest.mock import Mock

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class TestConfigRegistration:
    """测试环境服务注册类
    
    负责注册测试环境特定的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册测试环境服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册测试环境特定服务")
        
        # 测试环境可以注册Mock实现、测试工具等
        # 这里可以根据需要添加测试环境特定的服务
        
        # 示例：注册Mock会话路由器
        try:
            from ..routers.session_router import SessionRouter
            mock_session_router = Mock(spec=SessionRouter)
            container.register_instance(SessionRouter, mock_session_router, environment="test")
        except ImportError:
            pass
        
        logger.debug("测试环境特定服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            # 测试环境特定服务类型
        }