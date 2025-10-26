"""工作流领域模块

提供业务工作流的领域实体、值对象、服务和异常定义。
"""

# 实体
from .entities import (
    BusinessWorkflow,
    WorkflowExecution,
    WorkflowStatus,
    StepType,
)

# 值对象
from .value_objects import (
    WorkflowStep,
    WorkflowTransition,
    WorkflowRule,
    WorkflowTemplate,
    TransitionType,
    RuleType,
    RuleOperator,
)

# 异常
from .exceptions import (
    WorkflowError,
    WorkflowValidationError,
    WorkflowExecutionError,
    WorkflowStepError,
    WorkflowTransitionError,
    WorkflowRuleError,
    WorkflowTimeoutError,
    WorkflowStateError,
    WorkflowConfigError,
    WorkflowDependencyError,
    WorkflowPermissionError,
    WorkflowConcurrencyError,
    WorkflowResourceError,
    WorkflowIntegrationError,
    WorkflowTemplateError,
    WorkflowVersionError,
    create_workflow_exception,
    handle_workflow_exception,
)

__all__ = [
    # 实体
    "BusinessWorkflow",
    "WorkflowExecution",
    "WorkflowStatus",
    "StepType",
    
    # 值对象
    "WorkflowStep",
    "WorkflowTransition",
    "WorkflowRule",
    "WorkflowTemplate",
    "TransitionType",
    "RuleType",
    "RuleOperator",
    
    # 异常
    "WorkflowError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    "WorkflowStepError",
    "WorkflowTransitionError",
    "WorkflowRuleError",
    "WorkflowTimeoutError",
    "WorkflowStateError",
    "WorkflowConfigError",
    "WorkflowDependencyError",
    "WorkflowPermissionError",
    "WorkflowConcurrencyError",
    "WorkflowResourceError",
    "WorkflowIntegrationError",
    "WorkflowTemplateError",
    "WorkflowVersionError",
    "create_workflow_exception",
    "handle_workflow_exception",
]