"""工作流模板模块

提供各种预定义的工作流模板。
"""

from .base import BaseWorkflowTemplate
from .react import ReActWorkflowTemplate, EnhancedReActTemplate
from .plan_execute import PlanExecuteWorkflowTemplate, CollaborativePlanExecuteTemplate
from .registry import WorkflowTemplateRegistry, get_global_template_registry

__all__ = [
    # 基础模板
    "BaseWorkflowTemplate",
    # ReAct模板
    "ReActWorkflowTemplate",
    "EnhancedReActTemplate",
    
    # Plan-Execute模板
    "PlanExecuteWorkflowTemplate",
    "CollaborativePlanExecuteTemplate",
    
    # 模板注册表
    "WorkflowTemplateRegistry",
    "get_global_template_registry"
]