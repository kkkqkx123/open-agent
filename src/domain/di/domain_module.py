"""领域层模块

实现IServiceModule接口，提供领域层服务的注册。
"""

import logging
from typing import Dict, Any, Type, List

from src.di.interfaces import IServiceModule
from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class DomainModule(IServiceModule):
    """领域模块
    
    负责注册领域层相关服务，如状态管理、工作流核心、线程核心等。
    """
    
    def __init__(self):
        """初始化领域模块"""
        self.registered_services: Dict[str, Type] = {}
        
        # 定义领域层服务映射
        self.service_mappings = {
            # 状态管理
            "state_manager": "src.domain.state.interfaces.IStateManager",
            "state_collaboration_manager": "src.domain.state.interfaces.IStateCollaborationManager",
            
            # 工作流核心
            "workflow_config_manager": "src.domain.workflow.interfaces.IWorkflowConfigManager",
            "workflow_visualizer": "src.domain.workflow.interfaces.IWorkflowVisualizer",
            "workflow_registry": "src.domain.workflow.interfaces.IWorkflowRegistry",
            
            # 线程核心
            "thread_manager": "src.domain.threads.interfaces.IThreadManager",
            "thread_repository": "src.domain.threads.repository.IThreadRepository",
            
            # 工具核心
            "tool_manager": "src.domain.tools.interfaces.IToolManager",
            "tool_executor": "src.domain.tools.interfaces.IToolExecutor",
            
            # 提示词管理
            "prompt_template_manager": "src.domain.prompts.interfaces.IPromptTemplateManager",
            "prompt_injector": "src.domain.prompts.interfaces.IPromptInjector",
            
            # 会话核心
            "session_repository": "src.domain.sessions.repository.ISessionRepository",
            
            # 检查点核心
            "checkpoint_repository": "src.domain.checkpoint.repository.ICheckpointRepository",
            
            # 历史核心
            "history_repository": "src.domain.history.repository.IHistoryRepository",
        }
    
    def register_services(self, container: IDependencyContainer) -> None:
        """注册基础服务
        
        Args:
            container: 依赖注入容器
        """
        logger.info("注册领域层基础服务")
        
        # 注册状态管理
        self._register_state_services(container)
        
        # 注册工作流核心
        self._register_workflow_services(container)
        
        # 注册线程核心
        self._register_thread_services(container)
        
        # 注册工具核心
        self._register_tool_services(container)
        
        # 注册提示词管理
        self._register_prompt_services(container)
        
        # 注册会话核心
        self._register_session_services(container)
        
        # 注册检查点核心
        self._register_checkpoint_services(container)
        
        # 注册历史核心
        self._register_history_services(container)
        
        logger.debug("领域层基础服务注册完成")
    
    def register_environment_services(self, 
                                   container: IDependencyContainer, 
                                   environment: str) -> None:
        """注册环境特定服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"注册领域层{environment}环境特定服务")
        
        if environment == "development":
            self._register_development_services(container)
        elif environment == "test":
            self._register_test_services(container)
        elif environment == "production":
            self._register_production_services(container)
        
        logger.debug(f"领域层{environment}环境特定服务注册完成")
    
    def get_module_name(self) -> str:
        """获取模块名称
        
        Returns:
            模块名称
        """
        return "domain"
    
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
        # 领域层依赖基础设施层
        return ["infrastructure"]
    
    def _register_state_services(self, container: IDependencyContainer) -> None:
        """注册状态管理服务"""
        try:
            from .config.state_config import StateConfigRegistration
            StateConfigRegistration.register_services(container)
            self.registered_services.update(StateConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"状态管理服务注册失败: {e}")
    
    def _register_workflow_services(self, container: IDependencyContainer) -> None:
        """注册工作流核心服务"""
        try:
            from .config.workflow_config import WorkflowConfigRegistration
            WorkflowConfigRegistration.register_services(container)
            self.registered_services.update(WorkflowConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"工作流核心服务注册失败: {e}")
    
    def _register_thread_services(self, container: IDependencyContainer) -> None:
        """注册线程核心服务"""
        try:
            from .config.thread_config import ThreadConfigRegistration
            ThreadConfigRegistration.register_services(container)
            self.registered_services.update(ThreadConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"线程核心服务注册失败: {e}")
    
    def _register_tool_services(self, container: IDependencyContainer) -> None:
        """注册工具核心服务"""
        try:
            from .config.tool_config import ToolConfigRegistration
            ToolConfigRegistration.register_services(container)
            self.registered_services.update(ToolConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"工具核心服务注册失败: {e}")
    
    def _register_prompt_services(self, container: IDependencyContainer) -> None:
        """注册提示词管理服务"""
        try:
            from .config.prompt_config import PromptConfigRegistration
            PromptConfigRegistration.register_services(container)
            self.registered_services.update(PromptConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"提示词管理服务注册失败: {e}")
    
    def _register_session_services(self, container: IDependencyContainer) -> None:
        """注册会话核心服务"""
        try:
            from .config.session_config import SessionConfigRegistration
            SessionConfigRegistration.register_services(container)
            self.registered_services.update(SessionConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"会话核心服务注册失败: {e}")
    
    def _register_checkpoint_services(self, container: IDependencyContainer) -> None:
        """注册检查点核心服务"""
        try:
            from .config.checkpoint_config import CheckpointConfigRegistration
            CheckpointConfigRegistration.register_services(container)
            self.registered_services.update(CheckpointConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"检查点核心服务注册失败: {e}")
    
    def _register_history_services(self, container: IDependencyContainer) -> None:
        """注册历史核心服务"""
        try:
            from .config.history_config import HistoryConfigRegistration
            HistoryConfigRegistration.register_services(container)
            self.registered_services.update(HistoryConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"历史核心服务注册失败: {e}")
    
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