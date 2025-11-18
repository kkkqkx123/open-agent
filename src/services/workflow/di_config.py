"""工作流服务依赖注入配置

配置工作流服务的依赖注入。
"""

from typing import Dict, Any, Optional
from src.services.container import ServiceLifetime, container
from src.core.workflow.interfaces import IWorkflow, IWorkflowExecutor, IWorkflowState, ExecutionContext
from src.core.workflow.entities import Workflow, WorkflowExecution, NodeExecution, WorkflowState, ExecutionResult, WorkflowMetadata
from .orchestrator import WorkflowOrchestrator
from .executor import WorkflowExecutorService
from .registry import WorkflowRegistry


def register_workflow_services() -> None:
    """注册工作流服务
    
    注册所有工作流相关服务到依赖注入容器。
    """
    # 注册工作流编排器
    container.register(
        WorkflowOrchestrator,
        factory=lambda c: WorkflowOrchestrator(
            executor=c.get(WorkflowExecutorService),
            registry=c.get(WorkflowRegistry)
        ),
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册工作流执行器服务
    container.register(
        WorkflowExecutorService,
        factory=lambda c: WorkflowExecutorService(
            executor=c.get(IWorkflowExecutor) if c.is_registered(IWorkflowExecutor) else None
        ),
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册工作流注册表
    container.register(
        WorkflowRegistry,
        factory=lambda c: WorkflowRegistry(),
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册工作流构建器工厂
    from ..core.workflow.graph.builder import UnifiedGraphBuilder
    container.register(
        UnifiedGraphBuilder,
        factory=lambda c: UnifiedGraphBuilder(
            node_registry=c.get("node_registry") if c.is_registered("node_registry") else None,
            function_registry=c.get("function_registry") if c.is_registered("function_registry") else None,
            enable_function_fallback=c.get("config", {}).get("enable_function_fallback", True),
            enable_iteration_management=c.get("config", {}).get("enable_iteration_management", True)
        ),
        lifetime=ServiceLifetime.SINGLETON
    )


def configure_workflow_services(config: Dict[str, Any]) -> None:
    """配置工作流服务
    
    Args:
        config: 配置字典
    """
    # 配置工作流执行器
    executor_service = container.get(WorkflowExecutorService)
    if executor_service and hasattr(executor_service, 'configure'):
        executor_service.configure(config.get("executor", {}))
    
    # 配置工作流编排器
    orchestrator = container.get(WorkflowOrchestrator)
    if orchestrator and hasattr(orchestrator, 'configure'):
        orchestrator.configure(config.get("orchestrator", {}))
    
    # 配置工作流注册表
    registry = container.get(WorkflowRegistry)
    if registry and hasattr(registry, 'configure'):
        registry.configure(config.get("registry", {}))