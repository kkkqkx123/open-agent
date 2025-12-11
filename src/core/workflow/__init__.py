"""工作流核心模块

重构后的工作流模块，采用扁平化架构设计：
- 核心数据模型：纯数据容器，不包含业务逻辑
- 核心功能模块：验证、构建、注册等专门功能
- 加载模块：简化的配置加载功能
- 管理模块：生命周期管理
- 执行模块：统一的执行逻辑

新架构特点：
- 职责单一：每个模块都有明确的单一职责
- 松耦合：模块间依赖最小化
- 高内聚：相关功能集中在专门模块中
- 易扩展：接口驱动的设计便于扩展
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.interfaces.workflow.execution import IWorkflowExecutor
    from src.interfaces.workflow.core import IWorkflowValidator
    from src.interfaces.workflow.coordinator import IWorkflowCoordinator

# 核心数据模型
from .workflow import Workflow

# 核心功能模块
from .core.builder import WorkflowBuilder
from .core.registry import WorkflowRegistry  # 具体实现，通过依赖注入使用
from src.interfaces.workflow.core import IWorkflowRegistry  # 接口，推荐使用

# 协调器模块
from .coordinator import WorkflowCoordinator, create_workflow_coordinator

# 验证和管理模块
from .validation import WorkflowManager, WorkflowValidator, get_workflow_manager, get_workflow_validator

# 加载模块 - 暂时注释掉，因为模块不存在
# from .loading.loader import WorkflowLoader

# 管理模块
from .management.lifecycle import WorkflowLifecycleManager

# 执行模块
from .execution.executor import WorkflowExecutor, execute_workflow, execute_workflow_async
from .execution.services.execution_manager import ExecutionManager
from .execution.services.execution_monitor import ExecutionMonitor
from .execution.services.execution_scheduler import ExecutionScheduler

# 图实体模块
from .graph_entities import (
    Graph,
    Node,
    Edge,
    StateField,
    GraphState,
    EdgeType
)

# 图服务模块
from .graph import (
    IGraphService,
    GraphService,
    create_graph_service,
)

from .graph.extensions import (
    ITrigger,
    IPlugin,
    TriggerFactory,
    PluginManager
)

# 便捷函数
def create_workflow(graph: Graph) -> Workflow:
    """创建工作流实例
    
    Args:
        graph: 工作流图实体
        
    Returns:
        Workflow: 工作流实例
    """
    return Workflow(graph)


def create_workflow_manager() -> WorkflowManager:
    """创建工作流管理器
    
    Returns:
        WorkflowManager: 工作流管理器实例
    """
    return get_workflow_manager()


def create_workflow_validator() -> WorkflowValidator:
    """创建工作流验证器
    
    Returns:
        WorkflowValidator: 工作流验证器实例
    """
    return get_workflow_validator()


# def create_workflow_loader() -> WorkflowLoader:
#     """创建工作流加载器
#
#     Returns:
#         WorkflowLoader: 工作流加载器实例
#     """
#     return WorkflowLoader()


def create_workflow_executor() -> WorkflowExecutor:
    """创建统一工作流执行器
    
    Returns:
        WorkflowExecutor: 统一工作流执行器实例
    """
    return WorkflowExecutor()


def create_workflow_builder() -> WorkflowBuilder:
    """创建工作流构建器
    
    Returns:
        WorkflowBuilder: 工作流构建器实例
    """
    return WorkflowBuilder()


# 已弃用：请使用 WorkflowServiceBindings 注册工作流服务
def create_workflow_registry() -> WorkflowRegistry:
    """创建工作流注册表
    
    .. deprecated::
        请使用 WorkflowServiceBindings 注册工作流服务到依赖注入容器
    
    Returns:
        WorkflowRegistry: 工作流注册表实例
    """
    import warnings
    warnings.warn(
        "create_workflow_registry() 已弃用，请使用 WorkflowServiceBindings 注册工作流服务",
        DeprecationWarning,
        stacklevel=2
    )
    return WorkflowRegistry()


def create_workflow_coordinator_simple(builder: WorkflowBuilder,
                                     executor: "IWorkflowExecutor",
                                     validator: "IWorkflowValidator",
                                     lifecycle_manager: Any) -> "WorkflowCoordinator":
    """创建工作流协调器（简化版本）
    
    Args:
        builder: 工作流构建器
        executor: 工作流执行器
        validator: 工作流验证器
        lifecycle_manager: 生命周期管理器
        
    Returns:
        WorkflowCoordinator: 工作流协调器实例
    """
    return create_workflow_coordinator(
        builder=builder,
        executor=executor,
        validator=validator,
        lifecycle_manager=lifecycle_manager
    )


def create_lifecycle_manager(graph: Graph) -> WorkflowLifecycleManager:
    """创建生命周期管理器
    
    Args:
        graph: 图实体
        
    Returns:
        WorkflowLifecycleManager: 生命周期管理器实例
    """
    return WorkflowLifecycleManager(graph)


# 版本信息
__version__ = "2.0.0"
__author__ = "Workflow Team"
__description__ = "重构后的工作流核心模块，采用扁平化架构设计"

# 导出列表
__all__ = [
    # 核心数据模型
    "Workflow",
    
    # 核心功能模块
    "WorkflowBuilder",
    "WorkflowRegistry",  # 具体实现
    "IWorkflowRegistry",  # 接口，推荐使用
    
    # 协调器模块
    "WorkflowCoordinator",
    "create_workflow_coordinator",
    "create_workflow_coordinator_simple",
    
    # 验证和管理模块
    "WorkflowManager",
    "WorkflowValidator",
    "get_workflow_manager",
    "get_workflow_validator",
    
    # 加载模块 - 暂时注释掉，因为模块不存在
    # "WorkflowLoader",
    
    # 管理模块
    "WorkflowLifecycleManager",
    
    # 执行模块
    "WorkflowExecutor",
    "execute_workflow",
    "execute_workflow_async",
    "ExecutionManager",
    "ExecutionMonitor",
    "ExecutionScheduler",
    
    # 图实体模块
    "Graph",
    "Node",
    "Edge",
    "StateField",
    "GraphState",
    "EdgeType",
    
    # 图服务模块
    "IGraphService",
    "GraphService",
    "create_graph_service",
    
    # 注册表模块
    "WorkflowRegistry",  # 具体实现
    "IWorkflowRegistry",  # 接口，推荐使用
    "create_workflow_registry",  # 已弃用
    "ITrigger",
    "IPlugin",
    "TriggerFactory",
    "PluginManager",
    
    # 便捷函数
    "create_workflow",
    "create_workflow_manager",
    "create_workflow_validator",
    # "create_workflow_loader",
    "create_workflow_executor",
    "create_workflow_builder",
    "create_workflow_registry",
    "create_lifecycle_manager",
    
    # 版本信息
    "__version__",
    "__author__",
    "__description__",
]