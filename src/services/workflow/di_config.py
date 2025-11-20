"""工作流服务依赖注入配置

配置工作流相关服务的依赖注入，避免循环依赖。
"""

from typing import Dict, Any, Optional
from src.interfaces.workflow.services import (
    IWorkflowBuilderService,
    IWorkflowExecutor,
    IWorkflowFactory,
    IWorkflowManager
)
from .building.builder_service import WorkflowBuilderService
from .building.factory import WorkflowFactory
from .execution_service import WorkflowExecutionService, WorkflowInstanceExecutor
from .function_registry import FunctionRegistry, get_global_function_registry
from ..container import register_service, get_service, ServiceLifetime


def configure_workflow_services() -> None:
    """配置工作流相关服务的依赖注入
    
    注册所有工作流相关的服务到依赖注入容器中。
    """
    # 注册函数注册表
    register_service(
        FunctionRegistry,
        factory=get_global_function_registry,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册构建服务
    register_service(
        IWorkflowBuilderService,
        WorkflowBuilderService,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册执行服务
    register_service(
        IWorkflowExecutor,
        WorkflowExecutionService,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    register_service(
        WorkflowInstanceExecutor,
        WorkflowInstanceExecutor,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册工厂服务
    register_service(
        IWorkflowFactory,
        WorkflowFactory,
        lifetime=ServiceLifetime.SINGLETON
    )


def get_workflow_builder_service() -> IWorkflowBuilderService:
    """获取工作流构建服务
    
    Returns:
        IWorkflowBuilderService: 工作流构建服务实例
    """
    return get_service(IWorkflowBuilderService)  # type: ignore


def get_workflow_execution_service() -> IWorkflowExecutor:
    """获取工作流执行服务
    
    Returns:
        IWorkflowExecutor: 工作流执行服务实例
    """
    return get_service(IWorkflowExecutor)  # type: ignore


def get_workflow_instance_executor() -> WorkflowInstanceExecutor:
    """获取工作流实例执行器
    
    Returns:
        WorkflowInstanceExecutor: 工作流实例执行器实例
    """
    return get_service(WorkflowInstanceExecutor)  # type: ignore


def get_workflow_factory() -> IWorkflowFactory:
    """获取工作流工厂
    
    Returns:
        IWorkflowFactory: 工作流工厂实例
    """
    return get_service(IWorkflowFactory)  # type: ignore


def get_function_registry() -> FunctionRegistry:
    """获取函数注册表
    
    Returns:
        FunctionRegistry: 函数注册表实例
    """
    return get_service(FunctionRegistry)  # type: ignore


# 便捷函数
def create_workflow_instance(config: Dict[str, Any], **kwargs: Any) -> Any:
    """创建工作流实例的便捷函数
    
    Args:
        config: 工作流配置
        **kwargs: 其他参数
        
    Returns:
        工作流实例
    """
    from src.core.workflow.workflow_instance import WorkflowInstance
    from src.core.workflow.config.config import GraphConfig
    
    # 转换配置
    graph_config = GraphConfig.from_dict(config)
    
    # 创建实例
    return WorkflowInstance(graph_config, **kwargs)


def execute_workflow(config: Dict[str, Any], initial_data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
    """执行工作流的便捷函数
    
    Args:
        config: 工作流配置
        initial_data: 初始数据
        **kwargs: 其他参数
        
    Returns:
        执行结果
    """
    # 创建工作流实例
    instance = create_workflow_instance(config, use_services_layer=True)
    
    # 执行工作流
    return instance.run(initial_data, **kwargs)  # type: ignore


async def execute_workflow_async(config: Dict[str, Any], initial_data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
    """异步执行工作流的便捷函数
    
    Args:
        config: 工作流配置
        initial_data: 初始数据
        **kwargs: 其他参数
        
    Returns:
        执行结果
    """
    # 创建工作流实例
    instance = create_workflow_instance(config, use_services_layer=True)
    
    # 异步执行工作流
    return await instance.run_async(initial_data, **kwargs)  # type: ignore


# 初始化配置
def initialize_workflow_services() -> None:
    """初始化工作流服务
    
    在应用启动时调用，配置所有工作流相关服务。
    """
    try:
        configure_workflow_services()
        print("✅ 工作流服务依赖注入配置完成")
    except Exception as e:
        print(f"❌ 工作流服务依赖注入配置失败: {e}")
        raise


if __name__ == "__main__":
    # 测试配置
    initialize_workflow_services()
    
    # 测试服务获取
    builder_service = get_workflow_builder_service()
    execution_service = get_workflow_execution_service()
    factory = get_workflow_factory()
    registry = get_function_registry()
    
    print(f"构建服务: {type(builder_service).__name__}")
    print(f"执行服务: {type(execution_service).__name__}")
    print(f"工厂服务: {type(factory).__name__}")
    print(f"函数注册表: {type(registry).__name__}")