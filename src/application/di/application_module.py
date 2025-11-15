"""应用层模块

实现IServiceModule接口，提供应用层服务的注册。
"""

import logging
from typing import Dict, Any, Type, List

from src.di.interfaces import IServiceModule
from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class ApplicationModule(IServiceModule):
    """应用模块
    
    负责注册应用层相关服务，如会话管理、工作流管理、线程服务等。
    """
    
    def __init__(self):
        """初始化应用模块"""
        self.registered_services: Dict[str, Type] = {}
        
        # 定义应用层服务映射
        self.service_mappings = {
            # 会话管理
            "session_manager": "src.application.sessions.manager.ISessionManager",
            "git_manager": "src.application.sessions.git_manager.IGitManager",
            
            # 工作流管理
            "workflow_manager": "src.application.workflow.manager.IWorkflowManager",
            "workflow_factory": "src.application.workflow.factory.IWorkflowFactory",
            
            # 线程服务
            "thread_service": "src.application.threads.interfaces.IThreadService",
            
            # 回放管理
            "replay_manager": "src.application.replay.manager.IReplayManager",
            
            # 检查点管理
            "checkpoint_manager": "src.application.checkpoint.manager.ICheckpointManager",
            
            # 历史管理
            "history_manager": "src.application.history.manager.IHistoryManager",
        }
    
    def register_services(self, container: IDependencyContainer) -> None:
        """注册基础服务
        
        Args:
            container: 依赖注入容器
        """
        logger.info("注册应用层基础服务")
        
        # 注册会话管理
        self._register_session_services(container)
        
        # 注册工作流管理
        self._register_workflow_services(container)
        
        # 注册线程服务
        self._register_thread_services(container)
        
        # 注册回放管理
        self._register_replay_services(container)
        
        # 注册检查点管理
        self._register_checkpoint_services(container)
        
        # 注册历史管理
        self._register_history_services(container)
        
        logger.debug("应用层基础服务注册完成")
    
    def register_environment_services(self, 
                                   container: IDependencyContainer, 
                                   environment: str) -> None:
        """注册环境特定服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"注册应用层{environment}环境特定服务")
        
        if environment == "development":
            self._register_development_services(container)
        elif environment == "test":
            self._register_test_services(container)
        elif environment == "production":
            self._register_production_services(container)
        
        logger.debug(f"应用层{environment}环境特定服务注册完成")
    
    def get_module_name(self) -> str:
        """获取模块名称
        
        Returns:
            模块名称
        """
        return "application"
    
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
        # 应用层依赖领域层和基础设施层
        return ["domain", "infrastructure"]
    
    def _register_session_services(self, container: IDependencyContainer) -> None:
        """注册会话管理服务"""
        try:
            from .config.session_config import SessionConfigRegistration
            SessionConfigRegistration.register_services(container)
            self.registered_services.update(SessionConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"会话管理服务注册失败: {e}")
    
    def _register_workflow_services(self, container: IDependencyContainer) -> None:
        """注册工作流管理服务"""
        try:
            from .config.workflow_config import WorkflowConfigRegistration
            WorkflowConfigRegistration.register_services(container)
            self.registered_services.update(WorkflowConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"工作流管理服务注册失败: {e}")
    
    def _register_thread_services(self, container: IDependencyContainer) -> None:
        """注册线程服务"""
        try:
            from .config.thread_config import ThreadConfigRegistration
            ThreadConfigRegistration.register_services(container)
            self.registered_services.update(ThreadConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"线程服务注册失败: {e}")
    
    def _register_replay_services(self, container: IDependencyContainer) -> None:
        """注册回放管理服务"""
        try:
            from .config.replay_config import ReplayConfigRegistration
            ReplayConfigRegistration.register_services(container)
            self.registered_services.update(ReplayConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"回放管理服务注册失败: {e}")
    
    def _register_checkpoint_services(self, container: IDependencyContainer) -> None:
        """注册检查点管理服务"""
        try:
            from .config.checkpoint_config import CheckpointConfigRegistration
            CheckpointConfigRegistration.register_services(container)
            self.registered_services.update(CheckpointConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"检查点管理服务注册失败: {e}")
    
    def _register_history_services(self, container: IDependencyContainer) -> None:
        """注册历史管理服务"""
        try:
            from .config.history_config import HistoryConfigRegistration
            HistoryConfigRegistration.register_services(container)
            self.registered_services.update(HistoryConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"历史管理服务注册失败: {e}")
    
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