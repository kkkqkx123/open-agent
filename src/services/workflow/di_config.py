"""工作流服务依赖注入配置

配置工作流服务的依赖注入。
"""

from typing import Dict, Any, Optional
from src.services.container import ServiceLifetime, container
from src.core.workflow.interfaces import IWorkflow, IWorkflowExecutor, IWorkflowState, ExecutionContext
from src.core.workflow.entities import Workflow, WorkflowExecution, NodeExecution, WorkflowState, ExecutionResult, WorkflowMetadata
from .orchestrator import WorkflowOrchestrator
from .execution.executor import WorkflowExecutorService
from .registry import WorkflowRegistry

# 新架构服务
from .loader_service import UniversalLoaderService
from .workflow_instance import WorkflowInstance
from .runner import WorkflowRunner
from .retry_executor import RetryExecutor, RetryConfig
from .batch_executor import BatchExecutor, BatchExecutionConfig
from ..monitoring.execution_stats import ExecutionStatsCollector


def register_workflow_services() -> None:
    """注册工作流服务
    
    注册所有工作流相关服务到依赖注入容器。
    """
    # 注册工作流编排器
    container.register(
        WorkflowOrchestrator,
        WorkflowOrchestrator,
        lifetime="singleton"
    )
    
    # 注册工作流执行器服务
    container.register(
        WorkflowExecutorService,
        WorkflowExecutorService,
        lifetime="singleton"
    )
    
    # 注册工作流注册表
    container.register(
        WorkflowRegistry,
        WorkflowRegistry,
        lifetime="singleton"
    )
    
    # 注册工作流构建器工厂
    from .builder import UnifiedGraphBuilder
    container.register(
        UnifiedGraphBuilder,
        UnifiedGraphBuilder,
        lifetime="singleton"
    )
    
    # === 新架构服务注册 ===
    
    # 注册统一加载器服务
    container.register(
        UniversalLoaderService,
        UniversalLoaderService,
        lifetime="singleton"
    )
    
    # 注册工作流运行器
    container.register(
        WorkflowRunner,
        WorkflowRunner,
        lifetime="transient"
    )
    
    # 注册重试执行器
    container.register(
        RetryExecutor,
        RetryExecutor,
        lifetime="transient"
    )
    
    # 注册批量执行器
    container.register(
        BatchExecutor,
        BatchExecutor,
        lifetime="transient"
    )
    
    # 注册执行统计收集器
    container.register(
        ExecutionStatsCollector,
        ExecutionStatsCollector,
        lifetime="singleton"
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
    
    # === 新架构服务配置 ===
    
    # 配置重试执行器
    if "retry" in config:
        retry_config = RetryConfig(
            max_retries=config["retry"].get("max_retries", 3),
            strategy=config["retry"].get("strategy", "exponential_backoff"),
            base_delay=config["retry"].get("base_delay", 1.0),
            max_delay=config["retry"].get("max_delay", 60.0),
            multiplier=config["retry"].get("multiplier", 2.0),
            jitter=config["retry"].get("jitter", True)
        )
        container.register_instance(type(retry_config), retry_config)
    
    # 配置批量执行器
    if "batch_execution" in config:
        batch_config = BatchExecutionConfig(
            mode=config["batch_execution"].get("mode", "thread_pool"),
            max_workers=config["batch_execution"].get("max_workers", 3),
            failure_strategy=config["batch_execution"].get("failure_strategy", "continue_on_failure"),
            timeout=config["batch_execution"].get("timeout"),
            chunk_size=config["batch_execution"].get("chunk_size", 1)
        )
        container.register_instance(type(batch_config), batch_config)
    
    # 配置执行统计收集器
    stats_collector = container.get(ExecutionStatsCollector)
    if stats_collector and hasattr(stats_collector, 'configure'):
        stats_collector.configure(config.get("execution_stats", {}))


def register_new_architecture_services() -> None:
    """注册新架构服务（独立函数，用于逐步迁移）
    
    只注册新架构的服务，不包含旧架构的服务。
    """
    # 注册统一加载器服务
    container.register(
        UniversalLoaderService,
        UniversalLoaderService,
        lifetime="singleton"
    )
    
    # 注册工作流运行器
    container.register(
        WorkflowRunner,
        WorkflowRunner,
        lifetime="transient"
    )
    
    # 注册重试执行器
    container.register(
        RetryExecutor,
        RetryExecutor,
        lifetime="transient"
    )
    
    # 注册批量执行器
    container.register(
        BatchExecutor,
        BatchExecutor,
        lifetime="transient"
    )
    
    # 注册执行统计收集器
    container.register(
        ExecutionStatsCollector,
        ExecutionStatsCollector,
        lifetime="singleton"
    )


def get_new_architecture_services() -> Dict[str, Any]:
    """获取新架构服务实例
    
    Returns:
        Dict[str, Any]: 新架构服务实例字典
    """
    return {
        "loader_service": container.get(UniversalLoaderService),
        "runner": container.get(WorkflowRunner),
        "retry_executor": container.get(RetryExecutor),
        "batch_executor": container.get(BatchExecutor),
        "execution_stats": container.get(ExecutionStatsCollector)
    }