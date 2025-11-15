"""工具核心DI配置

负责注册工具核心相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.infrastructure.tools.interfaces import IToolManager
from src.domain.tools.interfaces import IToolExecutor, IToolRegistry
from src.infrastructure.tools.manager import ToolManager
from src.infrastructure.tools.executor import AsyncToolExecutor
from src.infrastructure.logger.logger import ILogger
from src.infrastructure.config.interfaces import IConfigLoader

logger = logging.getLogger(__name__)


class ToolConfigRegistration:
    """工具核心注册类
    
    负责注册工具核心相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册工具核心服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册工具核心服务")
        
        # 注册工具执行器
        container.register_factory(
            IToolExecutor,
            lambda: AsyncToolExecutor(
                tool_manager=container.get(IToolManager),
                logger=container.get(ILogger)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工具管理器
        container.register_factory(
            IToolManager,
            lambda: ToolManager(
                config_loader=container.get(IConfigLoader),
                logger=container.get(ILogger)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("工具核心服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "tool_executor": IToolExecutor,
            "tool_manager": IToolManager,
        }