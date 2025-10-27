"""工作流模块

提供工作流管理、创建和执行功能。
"""

from .interfaces import IWorkflowManager
from .factory import IWorkflowFactory
from .manager import WorkflowManager
from .factory import WorkflowFactory
from .builder_adapter import WorkflowBuilderAdapter
from .di_config import WorkflowModule, configure_workflow_container
from src.infrastructure.graph.states import (
    BaseGraphState, WorkflowState,
    ReActState, PlanExecuteState, StateFactory, StateSerializer
)
from src.domain.agent.state import AgentState

__all__ = [
    # 接口
    "IWorkflowManager",
    "IWorkflowFactory",
    
    # 实现类
    "WorkflowManager",
    "WorkflowFactory",
    "WorkflowBuilderAdapter",
    
    # 状态类
    "BaseGraphState",
    "AgentState",
    "WorkflowState",
    "ReActState",
    "PlanExecuteState",
    "StateFactory",
    "StateSerializer",
    
    # 配置
    "WorkflowModule",
    "configure_workflow_container",
]


def setup_workflow_container(
    container,
    environment="default",
    config_loader=None,
    node_registry=None
):
    """设置工作流容器（便捷函数）
    
    Args:
        container: 依赖注入容器
        environment: 环境名称
        config_loader: 配置加载器
        node_registry: 节点注册表
        
    Returns:
        配置好的容器
    """
    configure_workflow_container(
        container=container,
        environment=environment,
        config_loader=config_loader,
        node_registry=node_registry
    )
    return container