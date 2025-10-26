"""工作流系统模块

基于LangGraph的增强工作流系统，支持ReAct等工作流模式。
提供统一的工作流创建接口、模板系统、Agent集成和改进的状态管理。
新版本WorkflowBuilder支持：
- 配置驱动的构建过程
- 工作流模板系统
- Agent节点自动注册
- 多种配置输入格式
- 向后兼容的API
"""

from .manager import IWorkflowManager, WorkflowManager
from .state import WorkflowState, AgentState
from .interfaces import IWorkflowBuilder
from .builder_adapter import WorkflowBuilderAdapter
from .factory import (
    IWorkflowFactory,
    UnifiedWorkflowFactory,
    get_global_factory,
    create_workflow_from_config,
    create_simple_workflow,
    create_react_workflow,
    create_plan_execute_workflow
)
from .auto_discovery import auto_register_nodes, register_builtin_nodes
from .visualization import IWorkflowVisualizer, create_visualizer

# 自动注册预定义节点
try:
    # 初始化时自动注册内置节点
    register_builtin_nodes()
except ImportError as e:
    # 如果节点模块不存在，记录警告但不中断导入
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"无法导入节点模块: {e}")

__all__ = [
    # 核心接口
    "IWorkflowManager",
    "WorkflowManager",
    "IWorkflowFactory",
    "UnifiedWorkflowFactory",
    
    # 状态
    "WorkflowState",
    "AgentState",  # 向后兼容
    
    # 构建器
    "IWorkflowBuilder",
    "WorkflowBuilderAdapter",  # 向后兼容别名
    
    # 工厂接口
    "get_global_factory",
    "create_workflow_from_config",
    "create_simple_workflow",
    "create_react_workflow",
    "create_plan_execute_workflow",
    
    # 注册功能
    "auto_register_nodes",
    "register_builtin_nodes",
    
    # 可视化
    "IWorkflowVisualizer",
    "create_visualizer",
]