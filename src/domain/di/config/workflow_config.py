"""工作流核心DI配置

负责注册工作流核心相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.workflow.interfaces import (
    IWorkflowConfigManager, 
    IWorkflowVisualizer, 
    IWorkflowRegistry
)
from src.domain.workflow.config_manager import WorkflowConfigManager
from src.domain.workflow.visualizer import WorkflowVisualizer
from src.domain.workflow.registry import WorkflowRegistry
from src.infrastructure.config.interfaces import IConfigLoader

logger = logging.getLogger(__name__)


class WorkflowConfigRegistration:
    """工作流核心注册类
    
    负责注册工作流核心相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册工作流核心服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册工作流核心服务")
        
        # 注册工作流配置管理器
        container.register_factory(
            IWorkflowConfigManager,
            lambda: WorkflowConfigManager(
                config_loader=container.get(
                    IConfigLoader
                ) if container.has_service(
                    IConfigLoader
                ) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流可视化器
        container.register(
            IWorkflowVisualizer,
            WorkflowVisualizer,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流注册表
        container.register(
            IWorkflowRegistry,
            WorkflowRegistry,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("工作流核心服务注册完成")