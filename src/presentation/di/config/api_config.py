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
        
        # 注册会话路由器
        try:
            from ..routers.session_router import SessionRouter
            container.register(
                SessionRouter,
                SessionRouter,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"会话路由器注册失败: {e}")
        
        # 注册线程路由器
        try:
            from ..routers.thread_router import ThreadRouter
            container.register(
                ThreadRouter,
                ThreadRouter,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"线程路由器注册失败: {e}")
        
        # 注册工作流路由器
        try:
            from ..routers.workflow_router import WorkflowRouter
            container.register(
                WorkflowRouter,
                WorkflowRouter,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"工作流路由器注册失败: {e}")
        
        logger.debug("API服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "session_router": "SessionRouter",
            "thread_router": "ThreadRouter",
            "workflow_router": "WorkflowRouter",
        }