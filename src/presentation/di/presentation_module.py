"""表示层模块

实现IServiceModule接口，提供表示层服务的注册。
"""

import logging
from typing import Dict, Any, Type, List

from src.di.interfaces import IServiceModule
from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class PresentationModule(IServiceModule):
    """表示模块
    
    负责注册表示层相关服务，如API服务、UI服务、CLI命令等。
    """
    
    def __init__(self):
        """初始化表示模块"""
        self.registered_services: Dict[str, Type] = {}
        
        # 定义表示层服务映射
        self.service_mappings = {
            # API服务
            "session_router": "src.presentation.api.routers.SessionRouter",
            "thread_router": "src.presentation.api.routers.ThreadRouter",
            "workflow_router": "src.presentation.api.routers.WorkflowRouter",
            
            # TUI组件
            "session_component": "src.presentation.tui.components.SessionComponent",
            "thread_component": "src.presentation.tui.components.ThreadComponent",
            "workflow_component": "src.presentation.tui.components.WorkflowComponent",
            
            # CLI命令
            "run_command": "src.presentation.cli.commands.RunCommand",
            "config_command": "src.presentation.cli.commands.ConfigCommand",
        }
    
    def register_services(self, container: IDependencyContainer) -> None:
        """注册基础服务
        
        Args:
            container: 依赖注入容器
        """
        logger.info("注册表示层基础服务")
        
        # 注册API服务
        self._register_api_services(container)
        
        # 注册TUI组件
        self._register_tui_services(container)
        
        # 注册CLI命令
        self._register_cli_services(container)
        
        logger.debug("表示层基础服务注册完成")
    
    def register_environment_services(self, 
                                   container: IDependencyContainer, 
                                   environment: str) -> None:
        """注册环境特定服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"注册表示层{environment}环境特定服务")
        
        if environment == "development":
            self._register_development_services(container)
        elif environment == "test":
            self._register_test_services(container)
        elif environment == "production":
            self._register_production_services(container)
        
        logger.debug(f"表示层{environment}环境特定服务注册完成")
    
    def get_module_name(self) -> str:
        """获取模块名称
        
        Returns:
            模块名称
        """
        return "presentation"
    
    def get_registered_services(self) -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return self.registered_services.copy()
    
    def get_dependencies(self) -> List[str]:
        """获取模块依赖
        
        Returns:
            依赖的模块名称列表
        """
        # 表示层依赖应用层、领域层和基础设施层
        return ["application", "domain", "infrastructure"]
    
    def _register_api_services(self, container: IDependencyContainer) -> None:
        """注册API服务"""
        try:
            from .config.api_config import APIConfigRegistration
            APIConfigRegistration.register_services(container)
            self.registered_services.update(APIConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"API服务注册失败: {e}")
    
    def _register_tui_services(self, container: IDependencyContainer) -> None:
        """注册TUI服务"""
        try:
            from .config.tui_config import TUIConfigRegistration
            TUIConfigRegistration.register_services(container)
            self.registered_services.update(TUIConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"TUI服务注册失败: {e}")
    
    def _register_cli_services(self, container: IDependencyContainer) -> None:
        """注册CLI服务"""
        try:
            from .config.cli_config import CLIConfigRegistration
            CLIConfigRegistration.register_services(container)
            self.registered_services.update(CLIConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"CLI服务注册失败: {e}")
    
    def _register_development_services(self, container: IDependencyContainer) -> None:
        """注册开发环境服务"""
        try:
            from .config.development_config import DevelopmentConfigRegistration
            DevelopmentConfigRegistration.register_services(container)
            self.registered_services.update(DevelopmentConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"开发环境服务注册失败: {e}")
    
    def _register_test_services(self, container: IDependencyContainer) -> None:
        """注册测试环境服务"""
        try:
            from .config.test_config import TestConfigRegistration
            TestConfigRegistration.register_services(container)
            self.registered_services.update(TestConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"测试环境服务注册失败: {e}")
    
    def _register_production_services(self, container: IDependencyContainer) -> None:
        """注册生产环境服务"""
        try:
            from .config.production_config import ProductionConfigRegistration
            ProductionConfigRegistration.register_services(container)
            self.registered_services.update(ProductionConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"生产环境服务注册失败: {e}")