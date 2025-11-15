"""工具服务DI配置

负责注册工具系统相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.infrastructure.tools.manager import IToolManager, ToolManager
from src.infrastructure.tools.registry import IToolRegistry, ToolRegistry
from src.infrastructure.tools.validation.manager import IToolValidator, ToolValidationManager

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
        
        # 注册工具注册表
        container.register(
            IToolRegistry,
            ToolRegistry,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工具管理器
        container.register_factory(
            IToolManager,
            lambda: ToolManager(
                config_loader=container.get(
                    "src.infrastructure.config.loader.file_config_loader.IConfigLoader"
                ) if container.has_service(
                    "src.infrastructure.config.loader.file_config_loader.IConfigLoader"
                ) else None,
                logger=container.get(
                    "src.infrastructure.logger.logger.ILogger"
                ) if container.has_service(
                    "src.infrastructure.logger.logger.ILogger"
                ) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工具验证管理器
        container.register_factory(
            IToolValidator,
            lambda: ToolValidationManager(),
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