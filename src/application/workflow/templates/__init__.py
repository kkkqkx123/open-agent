"""Workflow模板模块

提供各种预定义的工作流模板。
"""

from .react_template import ReActWorkflowTemplate, EnhancedReActTemplate
from .plan_execute_template import PlanExecuteWorkflowTemplate, CollaborativePlanExecuteTemplate
from .registry import WorkflowTemplateRegistry, get_global_template_registry

__all__ = [
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