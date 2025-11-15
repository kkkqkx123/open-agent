"""TUI服务DI配置

负责注册TUI相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class TUIConfigRegistration:
    """TUI服务注册类
    
    负责注册TUI相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册TUI服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册TUI服务")
        
        # 注册会话组件
        try:
            from ..components.session_component import SessionComponent
            container.register(
                SessionComponent,
                SessionComponent,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"会话组件注册失败: {e}")
        
        # 注册线程组件
        try:
            from ..components.thread_component import ThreadComponent
            container.register(
                ThreadComponent,
                ThreadComponent,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"线程组件注册失败: {e}")
        
        # 注册工作流组件
        try:
            from ..components.workflow_component import WorkflowComponent
            container.register(
                WorkflowComponent,
                WorkflowComponent,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"工作流组件注册失败: {e}")
        
        logger.debug("TUI服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "session_component": "SessionComponent",
            "thread_component": "ThreadComponent",
            "workflow_component": "WorkflowComponent",
        }