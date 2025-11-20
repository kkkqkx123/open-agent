"""工具服务DI配置

负责注册工具系统相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.interfaces.tools_core import IToolManager
from src.core.tools.manager import ToolManager
from src.services.tools.validation.interfaces import IToolValidator
from src.services.tools.validation.manager import ToolValidationManager
from src.infrastructure.config.loader.file_config_loader import IConfigLoader
from src.infrastructure.logger.logger import ILogger
from src.interfaces.tools_core import IToolRegistry

logger = logging.getLogger(__name__)


class ToolsConfigRegistration:
    """工具服务注册类
    
    负责注册工具系统相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册工具服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册工具系统服务")
        
        # 注册工具管理器（同时实现IToolRegistry接口）
        container.register_factory(
            IToolManager,
            lambda: ToolManager(
                config_loader=container.get(IConfigLoader) if container.has_service(IConfigLoader) else None,
                logger=container.get(ILogger) if container.has_service(ILogger) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册IToolRegistry，指向ToolManager实例
        def get_tool_registry() -> IToolRegistry:
            return container.get(IToolManager)  # type: ignore
        
        container.register_factory(
            IToolRegistry,
            get_tool_registry,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工具验证管理器
        container.register_factory(
            IToolValidator,
            lambda: ToolValidationManager(
                config_loader=container.get(IConfigLoader) if container.has_service(IConfigLoader) else None,
                logger=container.get(ILogger) if container.has_service(ILogger) else None,
                tool_manager=container.get(IToolManager) if container.has_service(IToolManager) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("工具系统服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "tool_registry": IToolRegistry,
            "tool_manager": IToolManager,
            "tool_validator": IToolValidator,
        }