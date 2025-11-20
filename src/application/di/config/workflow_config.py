"""工作流管理DI配置

负责注册工作流管理相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.application.workflow.manager import IWorkflowManager, WorkflowManager
from src.application.workflow.factory import IWorkflowFactory, WorkflowFactory
from src.infrastructure.config.loader.file_config_loader import IConfigLoader
from services.workflow.configuration.config_manager import IWorkflowConfigManager
from src.interfaces.workflow.core import IWorkflowVisualizer
from services.workflow.registry.registry_service import IWorkflowRegistryService

logger = logging.getLogger(__name__)


class WorkflowConfigRegistration:
    """工作流管理注册类
    
    负责注册工作流管理相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册工作流管理服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册工作流管理服务")
        
        # 注册工作流工厂
        container.register_factory(
            IWorkflowFactory,
            lambda: WorkflowFactory(
                container=container,
                config_loader=container.get(IConfigLoader) if container.has_service(IConfigLoader) else None  # type: ignore[arg-type]
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流管理器
        container.register_factory(
            IWorkflowManager,
            lambda: WorkflowManager(
                config_manager=container.get(IWorkflowConfigManager),
                visualizer=container.get(IWorkflowVisualizer),
                registry=container.get(IWorkflowRegistryService),
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("工作流管理服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "workflow_factory": IWorkflowFactory,
            "workflow_manager": IWorkflowManager,
        }