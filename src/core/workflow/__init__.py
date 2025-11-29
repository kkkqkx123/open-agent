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

# 核心数据模型
from .workflow import Workflow

# 核心功能模块
from .core.validator import WorkflowValidator
from .core.builder import WorkflowBuilder
from .core.registry import WorkflowRegistry

# 加载模块
from .loading.loader import WorkflowLoader

# 管理模块
from .management.lifecycle import WorkflowLifecycleManager

# 执行模块
from .execution.executor import WorkflowExecutor
from .execution.services.execution_manager import ExecutionManager
from .execution.services.execution_monitor import ExecutionMonitor
from .execution.services.execution_scheduler import ExecutionScheduler

# 配置模块
from .config.config import (
    GraphConfig,
    NodeConfig,
    EdgeConfig,
    WorkflowConfig,
    StateFieldConfig,
    GraphStateConfig,
    EdgeType
)

# 便捷函数
def create_workflow(config: GraphConfig) -> Workflow:
    """创建工作流实例
    
    Args:
        config: 工作流配置
        
    Returns:
        Workflow: 工作流实例
    """
    return Workflow(config)


def create_workflow_loader() -> WorkflowLoader:
    """创建工作流加载器
    
    Returns:
        WorkflowLoader: 工作流加载器实例
    """
    return WorkflowLoader()


def create_workflow_executor() -> WorkflowExecutor:
    """创建统一工作流执行器
    
    Returns:
        WorkflowExecutor: 统一工作流执行器实例
    """
    return WorkflowExecutor()


def create_workflow_validator() -> WorkflowValidator:
    """创建工作流验证器
    
    Returns:
        WorkflowValidator: 工作流验证器实例
    """
    return WorkflowValidator()


def create_workflow_builder() -> WorkflowBuilder:
    """创建工作流构建器
    
    Returns:
        WorkflowBuilder: 工作流构建器实例
    """
    return WorkflowBuilder()


def create_workflow_registry() -> WorkflowRegistry:
    """创建工作流注册表
    
    Returns:
        WorkflowRegistry: 工作流注册表实例
    """
    return WorkflowRegistry()


def create_lifecycle_manager(config: GraphConfig) -> WorkflowLifecycleManager:
    """创建生命周期管理器
    
    Args:
        config: 图配置
        
    Returns:
        WorkflowLifecycleManager: 生命周期管理器实例
    """
    return WorkflowLifecycleManager(config)


# 版本信息
__version__ = "2.0.0"
__author__ = "Workflow Team"
__description__ = "重构后的工作流核心模块，采用扁平化架构设计"

# 导出列表
__all__ = [
    # 核心数据模型
    "Workflow",
    
    # 核心功能模块
    "WorkflowValidator",
    "WorkflowBuilder", 
    "WorkflowRegistry",
    
    # 加载模块
    "WorkflowLoader",
    
    # 管理模块
    "WorkflowLifecycleManager",
    
    # 执行模块
    "WorkflowExecutor",
    "ExecutionManager",
    "ExecutionMonitor",
    "ExecutionScheduler",
    
    # 配置模块
    "GraphConfig",
    "NodeConfig",
    "EdgeConfig",
    "WorkflowConfig",
    "StateFieldConfig",
    "GraphStateConfig",
    "EdgeType",
    
    # 便捷函数
    "create_workflow",
    "create_workflow_loader",
    "create_workflow_executor",
    "create_workflow_validator",
    "create_workflow_builder",
    "create_workflow_registry",
    "create_lifecycle_manager",
    
    # 版本信息
    "__version__",
    "__author__",
    "__description__",
]