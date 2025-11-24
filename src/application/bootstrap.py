"""应用程序启动配置

负责初始化整个系统的依赖注入容器和服务注册。
"""

import os
from typing import Optional

from src.infrastructure.container import DependencyContainer, get_global_container
from src.interfaces.common import IConfigLoader
from src.core.config.config_loader import FileConfigLoader
from src.infrastructure.graph.registry import NodeRegistry, get_global_registry
from src.services.logger import get_logger
from .workflow import setup_workflow_container

logger = get_logger(__name__)


class ApplicationBootstrap:
    """应用程序启动配置类"""
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        """初始化启动配置
        
        Args:
            container: 依赖注入容器，如果为None则使用全局容器
        """
        self.container = container or get_global_container()
        self._initialized = False
    
    def initialize(
        self,
        environment: Optional[str] = None,
        config_path: Optional[str] = None
    ) -> DependencyContainer:
        """初始化应用程序
        
        Args:
            environment: 环境名称，如果为None则从环境变量获取
            config_path: 配置文件路径
            
        Returns:
            DependencyContainer: 初始化后的容器
        """
        if self._initialized:
            logger.warning("应用程序已经初始化")
            return self.container
        
        # 确定环境
        if environment is None:
            environment = os.getenv("APP_ENV", "development")
        
        logger.info(f"初始化应用程序，环境: {environment}")
        
        try:
            # 初始化基础设施服务
            self._initialize_infrastructure_services(environment, config_path)
            
            # 初始化工作流服务
            self._initialize_workflow_services(environment)
            
            # 初始化其他模块服务
            self._initialize_other_services(environment)
            
            self._initialized = True
            logger.info("应用程序初始化完成")
            
            return self.container
            
        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            raise
    
    def _initialize_infrastructure_services(
        self,
        environment: str,
        config_path: Optional[str]
    ) -> None:
        """初始化基础设施服务
        
        Args:
            environment: 环境名称
            config_path: 配置文件路径
        """
        # 注册配置加载器
        if config_path:
            config_loader = FileConfigLoader(config_path)
        else:
            config_loader = FileConfigLoader()
        
        self.container.register_instance(IConfigLoader, config_loader)
        
        # 注册节点注册表
        node_registry = get_global_registry()
        self.container.register_instance(NodeRegistry, node_registry)
        
        logger.debug("基础设施服务初始化完成")
    
    def _initialize_workflow_services(self, environment: str) -> None:
        """初始化工作流服务
        
        Args:
            environment: 环境名称
        """
        # 获取依赖
        config_loader = self.container.get(IConfigLoader)
        node_registry = self.container.get(NodeRegistry)
        
        # 配置工作流容器
        setup_workflow_container(
            container=self.container,
            environment=environment,
            config_loader=config_loader,
            node_registry=node_registry
        )
        
        logger.debug("工作流服务初始化完成")
    
    def _initialize_other_services(self, environment: str) -> None:
        """初始化其他模块服务
        
        Args:
            environment: 环境名称
        """
        # 这里可以初始化其他模块的服务
        # 例如：日志服务、缓存服务、数据库服务等
        
        logger.debug("其他服务初始化完成")
    
    def is_initialized(self) -> bool:
        """检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized
    
    def shutdown(self) -> None:
        """关闭应用程序"""
        if not self._initialized:
            return
        
        try:
            # 释放容器资源
            self.container.dispose()
            self._initialized = False
            logger.info("应用程序已关闭")
        except Exception as e:
            logger.error(f"关闭应用程序时出错: {e}")


def create_application(
    environment: Optional[str] = None,
    config_path: Optional[str] = None,
    container: Optional[DependencyContainer] = None
) -> DependencyContainer:
    """创建应用程序实例（便捷函数）
    
    Args:
        environment: 环境名称
        config_path: 配置文件路径
        container: 依赖注入容器
        
    Returns:
        DependencyContainer: 初始化后的容器
    """
    bootstrap = ApplicationBootstrap(container)
    return bootstrap.initialize(environment, config_path)


def get_workflow_manager(container: Optional[DependencyContainer] = None):
    """获取工作流管理器（便捷函数）
    
    Args:
        container: 依赖注入容器
        
    Returns:
        工作流管理器实例
    """
    if container is None:
        container = get_global_container()
    
    from .workflow.di_config import get_workflow_manager
    return get_workflow_manager(container)


def get_workflow_factory(container: Optional[DependencyContainer] = None):
    """获取工作流工厂（便捷函数）
    
    Args:
        container: 依赖注入容器
        
    Returns:
        工作流工厂实例
    """
    if container is None:
        container = get_global_container()
    
    from .workflow.di_config import get_workflow_factory
    return get_workflow_factory(container)