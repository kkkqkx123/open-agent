"""基础设施层模块

实现IServiceModule接口，提供基础设施层服务的注册。
"""

import logging
from typing import Dict, Any, Type, List

from src.di.interfaces import IServiceModule
from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class InfrastructureModule(IServiceModule):
    """基础设施模块
    
    负责注册基础设施层相关服务，如配置系统、日志系统、存储系统等。
    """
    
    def __init__(self):
        """初始化基础设施模块"""
        self.registered_services: Dict[str, Type] = {}
        
        # 定义基础设施层服务映射
        self.service_mappings = {
            # 配置系统
            "config_loader": "src.infrastructure.config.loader.file_config_loader.IConfigLoader",
            "config_merger": "src.infrastructure.config.processor.merger.IConfigMerger",
            "config_validator": "src.infrastructure.config.processor.validator.IConfigValidator",
            "config_system": "src.infrastructure.config.config_system.IConfigSystem",
            
            # 日志系统
            "logger": "src.infrastructure.logger.logger.ILogger",
            "log_cleanup_service": "src.infrastructure.monitoring.scheduler.LogCleanupService",
            
            # 存储系统
            "checkpoint_store": "src.infrastructure.checkpoint.store.ICheckpointStore",
            "session_store": "src.domain.sessions.store.ISessionStore",
            "thread_metadata_store": "src.infrastructure.threads.metadata_store.IThreadMetadataStore",
            
            # LLM客户端
            "llm_client": "src.infrastructure.llm.client.ILLMClient",
            "llm_config_manager": "src.infrastructure.llm.config_manager.LLMConfigManager",
            
            # 工具系统
            "tool_registry": "src.infrastructure.tools.registry.IToolRegistry",
            "tool_manager": "src.core.tools.interfaces.IToolManager",
            "tool_validator": "src.services.tools.validation.manager.IToolValidator",
            "mcp_client": "src.infrastructure.tools.mcp.IMCPClient",
            
            # 监控系统
            "performance_monitor": "src.infrastructure.monitoring.performance_monitor.IPerformanceMonitor",
            
            # 图和工作流基础设施
            "node_registry": "src.infrastructure.graph.registry.NodeRegistry",
            "state_factory": "src.infrastructure.graph.states.StateFactory",
            "state_serializer": "src.infrastructure.graph.states.StateSerializer",
            "graph_builder": "src.infrastructure.graph.builder.UnifiedGraphBuilder",
        }
    
    def register_services(self, container: IDependencyContainer) -> None:
        """注册基础服务
        
        Args:
            container: 依赖注入容器
        """
        logger.info("注册基础设施层基础服务")
        
        # 注册配置系统
        self._register_config_services(container)
        
        # 注册日志系统
        self._register_logging_services(container)
        
        # 注册存储系统
        self._register_storage_services(container)
        
        # 注册LLM客户端
        self._register_llm_services(container)
        
        # 注册工具系统
        self._register_tool_services(container)
        
        # 注册监控系统
        self._register_monitoring_services(container)
        
        # 注册图和工作流基础设施
        self._register_graph_services(container)
        
        logger.debug("基础设施层基础服务注册完成")
    
    def register_environment_services(self, 
                                   container: IDependencyContainer, 
                                   environment: str) -> None:
        """注册环境特定服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"注册基础设施层{environment}环境特定服务")
        
        if environment == "development":
            self._register_development_services(container)
        elif environment == "test":
            self._register_test_services(container)
        elif environment == "production":
            self._register_production_services(container)
        
        logger.debug(f"基础设施层{environment}环境特定服务注册完成")
    
    def get_module_name(self) -> str:
        """获取模块名称
        
        Returns:
            模块名称
        """
        return "infrastructure"
    
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
        # 基础设施层不依赖其他模块
        return []
    
    def _register_config_services(self, container: IDependencyContainer) -> None:
        """注册配置服务"""
        try:
            from .config.config_loader import ConfigLoaderRegistration
            ConfigLoaderRegistration.register_services(container)
            self.registered_services.update(ConfigLoaderRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"配置服务注册失败: {e}")
    
    def _register_logging_services(self, container: IDependencyContainer) -> None:
        """注册日志服务"""
        try:
            from .config.logging_config import LoggingConfigRegistration
            LoggingConfigRegistration.register_services(container)
            self.registered_services.update(LoggingConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"日志服务注册失败: {e}")
    
    def _register_storage_services(self, container: IDependencyContainer) -> None:
        """注册存储服务"""
        try:
            from .config.storage_config import StorageConfigRegistration
            StorageConfigRegistration.register_services(container)
            self.registered_services.update(StorageConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"存储服务注册失败: {e}")
    
    def _register_llm_services(self, container: IDependencyContainer) -> None:
        """注册LLM服务"""
        try:
            from .config.llm_config import LLMConfigRegistration
            LLMConfigRegistration.register_services(container)
            self.registered_services.update(LLMConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"LLM服务注册失败: {e}")
    
    def _register_tool_services(self, container: IDependencyContainer) -> None:
        """注册工具服务"""
        try:
            from .config.tools_config import ToolsConfigRegistration
            ToolsConfigRegistration.register_services(container)
            self.registered_services.update(ToolsConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"工具服务注册失败: {e}")
    
    def _register_monitoring_services(self, container: IDependencyContainer) -> None:
        """注册监控服务"""
        try:
            from .config.monitoring_config import MonitoringConfigRegistration
            MonitoringConfigRegistration.register_services(container)
            self.registered_services.update(MonitoringConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"监控服务注册失败: {e}")
    
    def _register_graph_services(self, container: IDependencyContainer) -> None:
        """注册图和工作流服务"""
        try:
            from .config.graph_config import GraphConfigRegistration
            GraphConfigRegistration.register_services(container)
            self.registered_services.update(GraphConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"图服务注册失败: {e}")
    
    def _register_development_services(self, container: IDependencyContainer) -> None:
        """注册开发环境服务"""
        # 开发环境特定服务，如调试工具、热重载等
        try:
            from .config.development_config import DevelopmentConfigRegistration
            DevelopmentConfigRegistration.register_services(container)
            self.registered_services.update(DevelopmentConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"开发环境服务注册失败: {e}")
    
    def _register_test_services(self, container: IDependencyContainer) -> None:
        """注册测试环境服务"""
        # 测试环境特定服务，如Mock实现、测试工具等
        try:
            from .config.test_config import TestConfigRegistration
            TestConfigRegistration.register_services(container)
            self.registered_services.update(TestConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"测试环境服务注册失败: {e}")
    
    def _register_production_services(self, container: IDependencyContainer) -> None:
        """注册生产环境服务"""
        # 生产环境特定服务，如性能优化、安全增强等
        try:
            from .config.production_config import ProductionConfigRegistration
            ProductionConfigRegistration.register_services(container)
            self.registered_services.update(ProductionConfigRegistration.get_service_types())
        except ImportError as e:
            logger.warning(f"生产环境服务注册失败: {e}")