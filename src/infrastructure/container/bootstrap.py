"""
容器引导器
"""

from typing import Dict, Any
from .dependency_container import DependencyContainer
from src.interfaces.container.core import IDependencyContainer

class ContainerBootstrap:
    """容器引导器 - 管理初始化顺序"""
    
    @staticmethod
    def create_container(config: Dict[str, Any]) -> IDependencyContainer:
        """创建并初始化容器"""
        container = DependencyContainer()
        
        # 注册基础设施服务
        ContainerBootstrap._register_infrastructure_services(container, config)
        
        # 注册业务服务
        ContainerBootstrap._register_business_services(container, config)
        
        return container
    
    @staticmethod
    def _register_infrastructure_services(container: IDependencyContainer, config: Dict[str, Any]):
        """注册基础设施服务"""
        # 注册日志服务
        from src.services.container.bindings.logger_bindings import LoggerServiceBindings
        logger_bindings = LoggerServiceBindings()
        logger_bindings.register_services(container, config)
        
        # 注册配置服务
        from src.services.container.bindings.config_bindings import ConfigServiceBindings
        config_bindings = ConfigServiceBindings()
        config_bindings.register_services(container, config)
    
    @staticmethod
    def _register_business_services(container: IDependencyContainer, config: Dict[str, Any]):
        """注册业务服务"""
        # 注册工作流服务
        from src.services.container.bindings.workflow_bindings import WorkflowServiceBindings
        workflow_bindings = WorkflowServiceBindings()
        workflow_bindings.register_services(container, config)
        
        # 注册存储服务
        from src.services.container.bindings.storage_bindings import StorageServiceBindings
        storage_bindings = StorageServiceBindings()
        storage_bindings.register_services(container, config)
        
        # 注册LLM服务
        from src.services.container.bindings.llm_bindings import LLMServiceBindings
        llm_bindings = LLMServiceBindings()
        llm_bindings.register_services(container, config)
        
        # 注册会话服务
        from src.services.container.bindings.session_bindings import SessionServiceBindings
        session_bindings = SessionServiceBindings()
        session_bindings.register_services(container, config)
        
        # 注册线程服务
        from src.services.container.bindings.thread_bindings import ThreadServiceBindings
        thread_bindings = ThreadServiceBindings()
        thread_bindings.register_services(container, config)
        
        # 注册提示词服务
        from src.services.container.bindings.prompts_bindings import PromptsServiceBindings
        prompts_bindings = PromptsServiceBindings()
        prompts_bindings.register_services(container, config)
        
        # 注册历史服务
        from src.services.container.bindings.history_bindings import HistoryServiceBindings
        history_bindings = HistoryServiceBindings()
        history_bindings.register_services(container, config)
        
        # 注册验证服务
        from src.services.container.bindings.validation_bindings import ValidationServiceBindings
        validation_bindings = ValidationServiceBindings()
        validation_bindings.register_services(container, config)