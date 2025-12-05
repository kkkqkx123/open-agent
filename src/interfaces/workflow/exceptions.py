"""工作流领域异常

定义工作流相关的异常类。
"""
from typing import Optional, Any, Dict, Callable

class WorkflowError(Exception):
    """工作流基础异常"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class WorkflowValidationError(WorkflowError):
    """工作流验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "WORKFLOW_VALIDATION_ERROR")
        self.field = field
        self.value = value


class WorkflowExecutionError(WorkflowError):
    """工作流执行错误"""
    
    def __init__(self, message: str, step_id: Optional[str] = None, execution_id: Optional[str] = None):
        super().__init__(message, "WORKFLOW_EXECUTION_ERROR")
        self.step_id = step_id
        self.execution_id = execution_id


class WorkflowStepError(WorkflowError):
    """工作流步骤错误"""
    
    def __init__(self, message: str, step_id: Optional[str] = None, step_type: Optional[str] = None):
        super().__init__(message, "WORKFLOW_STEP_ERROR")
        self.step_id = step_id
        self.step_type = step_type


class WorkflowTransitionError(WorkflowError):
    """工作流转换错误"""
    
    def __init__(self, message: str, from_step: Optional[str] = None, to_step: Optional[str] = None):
        super().__init__(message, "WORKFLOW_TRANSITION_ERROR")
        self.from_step = from_step
        self.to_step = to_step


class WorkflowRuleError(WorkflowError):
    """工作流规则错误"""
    
    def __init__(self, message: str, rule_id: Optional[str] = None, rule_type: Optional[str] = None):
        super().__init__(message, "WORKFLOW_RULE_ERROR")
        self.rule_id = rule_id
        self.rule_type = rule_type


class WorkflowTimeoutError(WorkflowError):
    """工作流超时错误"""
    
    def __init__(self, message: str, step_id: Optional[str] = None, timeout: Optional[int] = None):
        super().__init__(message, "WORKFLOW_TIMEOUT_ERROR")
        self.step_id = step_id
        self.timeout = timeout


class WorkflowStateError(WorkflowError):
    """工作流状态错误"""
    
    def __init__(self, message: str, current_state: Optional[str] = None, expected_state: Optional[str] = None):
        super().__init__(message, "WORKFLOW_STATE_ERROR")
        self.current_state = current_state
        self.expected_state = expected_state


class WorkflowConfigError(WorkflowError):
    """工作流配置错误"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None):
        super().__init__(message, "WORKFLOW_CONFIG_ERROR")
        self.config_key = config_key
        self.config_value = config_value


class WorkflowDependencyError(WorkflowError):
    """工作流依赖错误"""
    
    def __init__(self, message: str, dependency_type: Optional[str] = None, dependency_name: Optional[str] = None):
        super().__init__(message, "WORKFLOW_DEPENDENCY_ERROR")
        self.dependency_type = dependency_type
        self.dependency_name = dependency_name


class WorkflowPermissionError(WorkflowError):
    """工作流权限错误"""
    
    def __init__(self, message: str, user_id: Optional[str] = None, required_permission: Optional[str] = None):
        super().__init__(message, "WORKFLOW_PERMISSION_ERROR")
        self.user_id = user_id
        self.required_permission = required_permission


class WorkflowConcurrencyError(WorkflowError):
    """工作流并发错误"""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, conflict_type: Optional[str] = None):
        super().__init__(message, "WORKFLOW_CONCURRENCY_ERROR")
        self.workflow_id = workflow_id
        self.conflict_type = conflict_type


class WorkflowResourceError(WorkflowError):
    """工作流资源错误"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(message, "WORKFLOW_RESOURCE_ERROR")
        self.resource_type = resource_type
        self.resource_id = resource_id


class WorkflowIntegrationError(WorkflowError):
    """工作流集成错误"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, endpoint: Optional[str] = None):
        super().__init__(message, "WORKFLOW_INTEGRATION_ERROR")
        self.service_name = service_name
        self.endpoint = endpoint


class WorkflowTemplateError(WorkflowError):
    """工作流模板错误"""
    
    def __init__(self, message: str, template_id: Optional[str] = None, template_name: Optional[str] = None):
        super().__init__(message, "WORKFLOW_TEMPLATE_ERROR")
        self.template_id = template_id
        self.template_name = template_name


class WorkflowVersionError(WorkflowError):
    """工作流版本错误"""
    
    def __init__(self, message: str, current_version: Optional[str] = None, target_version: Optional[str] = None):
        super().__init__(message, "WORKFLOW_VERSION_ERROR")
        self.current_version = current_version
        self.target_version = target_version


# 异常映射字典，用于错误代码到异常类的映射
WORKFLOW_EXCEPTION_MAP = {
    "WORKFLOW_VALIDATION_ERROR": WorkflowValidationError,
    "WORKFLOW_EXECUTION_ERROR": WorkflowExecutionError,
    "WORKFLOW_STEP_ERROR": WorkflowStepError,
    "WORKFLOW_TRANSITION_ERROR": WorkflowTransitionError,
    "WORKFLOW_RULE_ERROR": WorkflowRuleError,
    "WORKFLOW_TIMEOUT_ERROR": WorkflowTimeoutError,
    "WORKFLOW_STATE_ERROR": WorkflowStateError,
    "WORKFLOW_CONFIG_ERROR": WorkflowConfigError,
    "WORKFLOW_DEPENDENCY_ERROR": WorkflowDependencyError,
    "WORKFLOW_PERMISSION_ERROR": WorkflowPermissionError,
    "WORKFLOW_CONCURRENCY_ERROR": WorkflowConcurrencyError,
    "WORKFLOW_RESOURCE_ERROR": WorkflowResourceError,
    "WORKFLOW_INTEGRATION_ERROR": WorkflowIntegrationError,
    "WORKFLOW_TEMPLATE_ERROR": WorkflowTemplateError,
    "WORKFLOW_VERSION_ERROR": WorkflowVersionError,
}


def create_workflow_exception(error_code: str, message: str, **kwargs: Any) -> WorkflowError:
    """创建工作流异常
    
    Args:
        error_code: 错误代码
        message: 错误消息
        **kwargs: 其他参数
        
    Returns:
        对应的异常实例
    """
    exception_class = WORKFLOW_EXCEPTION_MAP.get(error_code, WorkflowError)
    # For WorkflowError, we pass error_code and details separately
    if exception_class == WorkflowError:
        return exception_class(message, error_code, kwargs)  # type: ignore
    # For specific exception classes, we pass the kwargs as named parameters
    else:
        return exception_class(message, **kwargs)  # type: ignore


def handle_workflow_exception(func: Callable) -> Callable:
    """工作流异常处理装饰器
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except WorkflowError:
            # 重新抛出工作流异常
            raise
        except Exception as e:
            # 将其他异常包装为工作流异常
            raise WorkflowError(f"工作流操作失败: {str(e)}", "WORKFLOW_UNKNOWN_ERROR")
    
    return wrapper


# 导出所有异常
__all__ = [
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
    "WORKFLOW_EXCEPTION_MAP",
    "create_workflow_exception",
    "handle_workflow_exception",
]