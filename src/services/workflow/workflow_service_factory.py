"""工作流服务工厂

负责创建和配置 workflow 层服务，支持依赖注入。
"""

from typing import List, Optional, Dict, Any

from src.interfaces.container import IDependencyContainer
from src.interfaces.container.core import ServiceLifetime
from src.interfaces.logger import ILogger
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.interfaces.workflow.core import IWorkflowValidator
from src.interfaces.workflow.core import IWorkflowRegistry
from src.core.workflow.coordinator.workflow_coordinator import create_workflow_coordinator
from src.core.workflow.core.builder import IWorkflowBuilder, WorkflowBuilder
from src.core.workflow.execution.executor import WorkflowExecutor
from src.core.workflow.validation import WorkflowValidator
from src.core.workflow.management.lifecycle import WorkflowLifecycleManager
from src.infrastructure.error_management import handle_error, ErrorCategory, ErrorSeverity
from src.interfaces.workflow.exceptions import WorkflowError
# 移除了 create_unified_registry 导入，现在完全依赖依赖注入容器
from src.core.workflow.graph.service import create_graph_service


class WorkflowServiceFactory:
    """工作流服务工厂 - 负责从依赖注入容器获取工作流服务
    
    注意：此类不再负责服务注册，服务注册请使用 WorkflowServiceBindings
    """
    
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
            
            if self._logger:
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
            
            if self._logger:
                self._logger.error(f"创建工作流协调器失败: {e}")
            raise WorkflowError(f"创建工作流协调器失败: {e}") from e
    
    def get_workflow_registry(self) -> IWorkflowRegistry:
        """获取工作流注册表
        
        Returns:
            IWorkflowRegistry: 工作流注册表实例
            
        Raises:
            WorkflowError: 如果注册表未注册到容器
        """
        try:
            if not self._container.has_service(IWorkflowRegistry):
                raise WorkflowError("工作流注册表未注册到依赖注入容器")
            
            registry = self._container.get(IWorkflowRegistry)
            if self._logger:
                self._logger.debug("从依赖注入容器获取工作流注册表成功")
            return registry
        except Exception as e:
            # 使用统一错误处理框架
            error_context = {
                "operation": "get_workflow_registry",
                "factory_class": self.__class__.__name__
            }
            
            handle_error(e, error_context)
            
            if self._logger:
                self._logger.error(f"获取工作流注册表失败: {e}")
            raise WorkflowError(f"获取工作流注册表失败: {e}") from e
    
    def ensure_services_registered(self,
                                 environment: str = "default",
                                 config: Optional[Dict[str, Any]] = None) -> None:
        """确保工作流服务已注册到容器
        
        Args:
            environment: 环境名称
            config: 配置参数
            
        Note:
            此方法仅用于确保服务已注册，推荐使用 WorkflowServiceBindings 直接注册服务
        """
        try:
            # 检查核心服务是否已注册
            required_services = [
                IWorkflowRegistry,
                IWorkflowBuilder,
                IWorkflowExecutor,
                IWorkflowValidator,
                WorkflowLifecycleManager
            ]
            
            missing_services = []
            for service_type in required_services:
                if not self._container.has_service(service_type):
                    missing_services.append(service_type.__name__)
            
            if missing_services:
                if self._logger:
                    self._logger.warning(f"缺少工作流服务: {', '.join(missing_services)}")
                
                # 使用工作流服务绑定注册缺失的服务
                from src.services.container.bindings.workflow_bindings import WorkflowServiceBindings
                
                config = config or {}
                workflow_bindings = WorkflowServiceBindings()
                workflow_bindings.register_services(self._container, config, environment)
                
                if self._logger:
                    self._logger.info(f"工作流服务注册完成，环境: {environment}")
            else:
                if self._logger:
                    self._logger.debug("所有工作流服务已注册")

        except Exception as e:
            if self._logger:
                self._logger.error(f"确保工作流服务注册失败: {e}")
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
                # 核心工作流注册表不包含依赖验证功能
                # 这里可以添加其他验证逻辑
            
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
            if hasattr(registry, 'get_registry_stats'):
                stats["workflow_registry"] = registry.get_registry_stats()
            elif hasattr(registry, 'get_stats'):
                stats["workflow_registry"] = registry.get_stats()
        
        return stats


# 便捷函数
def create_workflow_service_factory(container: IDependencyContainer) -> WorkflowServiceFactory:
    """创建工作流服务工厂实例
    
    Args:
        container: 依赖注入容器（必须已注册工作流服务）
        
    Returns:
        WorkflowServiceFactory: 服务工厂实例
        
    Raises:
        WorkflowError: 如果容器中缺少必需的工作流服务
    """
    return WorkflowServiceFactory(container)


# 导出实现
__all__ = [
    "WorkflowServiceFactory",
    "create_workflow_service_factory",
]