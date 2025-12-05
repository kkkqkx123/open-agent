"""工作流服务工厂

负责创建和配置 workflow 层服务，支持依赖注入。
"""

from typing import List, Optional, Dict, Any

from src.interfaces.container import IDependencyContainer
from src.interfaces.container.core import ServiceLifetime
from src.interfaces.logger import ILogger
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.builders import IWorkflowBuilder
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.interfaces.workflow.core import IWorkflowValidator
from src.interfaces.workflow.registry import IWorkflowRegistry
from src.core.workflow.coordinator import create_workflow_coordinator
from src.core.workflow.core.builder import WorkflowBuilder
from src.core.workflow.execution.executor import WorkflowExecutor
from src.core.workflow.validation import WorkflowValidator
from src.core.workflow.management.lifecycle import WorkflowLifecycleManager
from src.core.common.error_management import handle_error, ErrorCategory, ErrorSeverity
from src.core.common.exceptions.workflow import WorkflowError
from src.core.workflow.registry import create_workflow_registry
from src.core.workflow.graph.service import create_graph_service


class WorkflowServiceFactory:
    """工作流服务工厂 - 负责创建和配置 workflow 层服务"""
    
    def __init__(self, container: IDependencyContainer, logger: Optional[ILogger] = None):
        """初始化服务工厂
        
        Args:
            container: 依赖注入容器
            logger: 日志记录器
        """
        self._container = container
        self._logger = logger
    
    def create_workflow_coordinator(self) -> IWorkflowCoordinator:
        """创建工作流协调器
        
        Returns:
            IWorkflowCoordinator: 工作流协调器实例
        """
        try:
            # 从容器获取所有依赖
            builder = self._container.get(IWorkflowBuilder)
            executor = self._container.get(IWorkflowExecutor)
            validator = self._container.get(IWorkflowValidator)
            lifecycle_manager = self._container.get(WorkflowLifecycleManager)
            
            # 尝试获取图服务（可选）
            graph_service = None
            if self._container.has_service(create_graph_service.__class__):
                graph_service = self._container.get(create_graph_service.__class__)
            
            # 创建协调器
            coordinator = create_workflow_coordinator(
                builder=builder,
                executor=executor,
                validator=validator,
                lifecycle_manager=lifecycle_manager,
                graph_service=graph_service
            )
            
            self._logger.debug("工作流协调器创建成功")
            return coordinator
            
        except Exception as e:
            # 使用统一错误处理框架
            error_context = {
                "operation": "create_workflow_coordinator",
                "factory_class": self.__class__.__name__,
                "container_services": [
                    "IWorkflowBuilder",
                    "IWorkflowExecutor",
                    "IWorkflowValidator",
                    "WorkflowLifecycleManager"
                ]
            }
            
            handle_error(e, error_context)
            
            self._logger.error(f"创建工作流协调器失败: {e}")
            raise WorkflowError(f"创建工作流协调器失败: {e}") from e
    
    def create_workflow_registry(self) -> IWorkflowRegistry:
        """创建工作流注册表
        
        Returns:
            IWorkflowRegistry: 工作流注册表实例
        """
        try:
            registry = create_workflow_registry()
            self._logger.debug("工作流注册表创建成功")
            return registry
        except Exception as e:
            # 使用统一错误处理框架
            error_context = {
                "operation": "create_workflow_registry",
                "factory_class": self.__class__.__name__
            }
            
            handle_error(e, error_context)
            
            self._logger.error(f"创建工作流注册表失败: {e}")
            raise WorkflowError(f"创建工作流注册表失败: {e}") from e
    
    def register_workflow_services(self, 
                                 environment: str = "default",
                                 config: Optional[Dict[str, Any]] = None) -> None:
        """注册所有 workflow 相关服务到容器
        
        Args:
            environment: 环境名称
            config: 配置参数
        """
        try:
            config = config or {}
            
            # 注册工作流注册表
            self._container.register_factory(
                IWorkflowRegistry,
                self.create_workflow_registry,
                environment=environment,
                lifetime=ServiceLifetime.SINGLETON
            )
            
            # 注册核心服务
            self._container.register(
                IWorkflowBuilder,
                WorkflowBuilder,
                environment=environment,
                lifetime=ServiceLifetime.TRANSIENT
            )
            
            self._container.register(
                IWorkflowExecutor,
                WorkflowExecutor,
                environment=environment,
                lifetime=ServiceLifetime.SINGLETON
            )
            
            self._container.register(
                IWorkflowValidator,
                WorkflowValidator,
                environment=environment,
                lifetime=ServiceLifetime.SINGLETON
            )
            
            self._container.register(
                WorkflowLifecycleManager,
                WorkflowLifecycleManager,
                environment=environment,
                lifetime=ServiceLifetime.SCOPED
            )
            
            # 注册图服务
            self._container.register_factory(
                create_graph_service.__class__,
                lambda: create_graph_service(self._container.get(IWorkflowRegistry)),
                environment=environment,
                lifetime=ServiceLifetime.SINGLETON
            )
            
            # 注册协调器
            self._container.register_factory(
                IWorkflowCoordinator,
                self.create_workflow_coordinator,
                environment=environment,
                lifetime=ServiceLifetime.TRANSIENT
            )
            
            if self._logger:
                self._logger.info(f"工作流服务注册完成，环境: {environment}")

        except Exception as e:
            if self._logger:
                self._logger.error(f"注册工作流服务失败: {e}")
            raise
    
    def validate_service_configuration(self) -> List[str]:
        """验证服务配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        try:
            # 验证容器配置
            container_validation = self._container.validate_configuration()
            if not container_validation.is_valid:
                errors.extend(container_validation.errors)
            
            # 验证必需的服务是否已注册
            required_services = [
                IWorkflowRegistry,
                IWorkflowBuilder,
                IWorkflowExecutor,
                IWorkflowValidator,
                WorkflowLifecycleManager
            ]
            
            for service_type in required_services:
                if not self._container.has_service(service_type):
                    errors.append(f"缺少必需的服务: {service_type.__name__}")
            
            # 验证工作流注册表依赖
            if self._container.has_service(IWorkflowRegistry):
                registry = self._container.get(IWorkflowRegistry)
                dependency_errors = registry.validate_dependencies()
                errors.extend(dependency_errors)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"验证服务配置时发生错误: {e}")
            errors.append(f"服务配置验证失败: {str(e)}")
        
        return errors
    
    def get_service_configuration_stats(self) -> Dict[str, Any]:
        """获取服务配置统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "registered_services": self._container.get_registration_count(),
            "container_valid": self._container.validate_configuration().is_valid,
        }
        
        # 添加工作流注册表统计
        if self._container.has_service(IWorkflowRegistry):
            registry = self._container.get(IWorkflowRegistry)
            stats["workflow_registry"] = registry.get_registry_stats()
        
        return stats


# 便捷函数
def create_workflow_service_factory(container: IDependencyContainer) -> WorkflowServiceFactory:
    """创建工作流服务工厂实例
    
    Args:
        container: 依赖注入容器
        
    Returns:
        WorkflowServiceFactory: 服务工厂实例
    """
    return WorkflowServiceFactory(container)


# 导出实现
__all__ = [
    "WorkflowServiceFactory",
    "create_workflow_service_factory",
]