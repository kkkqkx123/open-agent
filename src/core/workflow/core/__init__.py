"""工作流核心模块

提供工作流的核心功能，包括数据模型、验证、构建和注册。
"""

from .validator import (
    IWorkflowValidator,
    WorkflowValidator,
    ValidationSeverity,
    ValidationIssue,
    validate_workflow_config
)
from .builder import (
    IWorkflowBuilder,
    WorkflowBuilder
)
from .registry import (
    IWorkflowRegistry,
    WorkflowRegistry,
    get_global_registry,
    register_workflow,
    get_workflow,
    list_workflows
)

__all__ = [
    # 验证器
    "IWorkflowValidator",
    "WorkflowValidator",
    "ValidationSeverity",
    "ValidationIssue",
    "validate_workflow_config",
    
    # 构建器
    "IWorkflowBuilder",
    "WorkflowBuilder",
    
    # 注册表
    "IWorkflowRegistry",
    "WorkflowRegistry",
    "get_global_registry",
    "register_workflow",
    "get_workflow",
    "list_workflows",
]