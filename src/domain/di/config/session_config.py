"""会话核心DI配置

负责注册会话核心相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.sessions.store import ISessionStore

logger = logging.getLogger(__name__)


class SessionConfigRegistration:
    """会话核心注册类
    
    负责注册会话核心相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册会话核心服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册会话核心服务")
        
        # 注册会话存储接口（如果容器中还没有注册）
        if not container.has_service(ISessionStore):
            # 可以在这里注册默认实现，或者让其他模块负责注册
            pass
        
        logger.debug("会话核心服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "session_store": ISessionStore,
        }