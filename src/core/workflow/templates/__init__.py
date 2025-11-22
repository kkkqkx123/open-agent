"""工作流模板模块

提供各种预定义的工作流模板。
"""

from .base import BaseWorkflowTemplate
from .react import ReActWorkflowTemplate, EnhancedReActTemplate
from .plan_execute import PlanExecuteWorkflowTemplate, CollaborativePlanExecuteTemplate
from .prompt_agent import PromptAgentTemplate, SimplePromptAgentTemplate
from .prompt_integration import PromptIntegratedTemplate
from .registry import WorkflowTemplateRegistry, get_global_template_registry

__all__ = [
    # 基础模板
    "BaseWorkflowTemplate",
    "PromptIntegratedTemplate",
    
    # ReAct模板
    "ReActWorkflowTemplate",
    "EnhancedReActTemplate",
    
    # Plan-Execute模板
    "PlanExecuteWorkflowTemplate",
    "CollaborativePlanExecuteTemplate",
    
    # 提示词代理模板
    "PromptAgentTemplate",
    "SimplePromptAgentTemplate",
    
    # 模板注册表
    "WorkflowTemplateRegistry",
    "get_global_template_registry"
]