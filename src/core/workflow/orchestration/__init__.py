"""工作流协调模块

提供工作流的协调和管理功能。
"""

# 新的协调器
from .workflow_instance_coordinator import (
    WorkflowInstanceCoordinator,
)
from .workflow_registry_coordinator import (
    IWorkflowRegistryCoordinator,
    WorkflowRegistryCoordinator,
)

__all__ = [
    # 协调器
    "WorkflowInstanceCoordinator",
    "IWorkflowRegistryCoordinator",
    "WorkflowRegistryCoordinator",
]