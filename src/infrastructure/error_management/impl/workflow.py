"""
增强的工作流错误处理器

提供统一的工作流错误处理和恢复策略，集成到统一错误处理框架中。
"""

import time
from typing import Dict, Callable, Optional, Any, List
from enum import Enum

from src.infrastructure.error_management import (
    BaseErrorHandler, ErrorCategory, ErrorSeverity,
    ErrorHandlingRegistry, operation_with_retry, operation_with_fallback
)
from src.interfaces.workflow.exceptions import (
    WorkflowError, WorkflowValidationError, WorkflowExecutionError,
    WorkflowStepError, WorkflowTimeoutError, WorkflowStateError,
    WorkflowConfigError, WorkflowDependencyError
)

class WorkflowErrorType(Enum):
    """工作流错误类型"""
    VALIDATION = "validation"         # 验证错误
    EXECUTION = "execution"           # 执行错误
    STEP = "step"                     # 步骤错误
    TIMEOUT = "timeout"               # 超时错误
    STATE = "state"                   # 状态错误
    CONFIG = "config"                 # 配置错误
    DEPENDENCY = "dependency"         # 依赖错误
    PERMISSION = "permission"         # 权限错误
    RESOURCE = "resource"             # 资源错误
    CONCURRENCY = "concurrency"       # 并发错误
    INTEGRATION = "integration"       # 集成错误
    TRANSITION = "transition"         # 转换错误
    UNKNOWN = "unknown"               # 未知错误


class WorkflowErrorHandler(BaseErrorHandler):
    """增强的工作流错误处理器"""

    def __init__(self) -> None:
        super().__init__(ErrorCategory.WORKFLOW, ErrorSeverity.HIGH)
        self._retry_strategies: Dict[WorkflowErrorType, Callable] = {}
        self._fallback_strategies: Dict[WorkflowErrorType, Callable] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """注册默认的错误处理策略"""
        # 注册重试策略
        self._retry_strategies[WorkflowErrorType.TIMEOUT] = self._retry_timeout
        self._retry_strategies[WorkflowErrorType.RESOURCE] = self._retry_resource
        self._retry_strategies[WorkflowErrorType.DEPENDENCY] = self._retry_dependency
        self._retry_strategies[WorkflowErrorType.INTEGRATION] = self._retry_integration

        # 注册降级策略
        self._retry_strategies[WorkflowErrorType.EXECUTION] = self._fallback_execution
        self._fallback_strategies[WorkflowErrorType.STEP] = self._fallback_step
        self._fallback_strategies[WorkflowErrorType.STATE] = self._fallback_state
        self._fallback_strategies[WorkflowErrorType.CONFIG] = self._fallback_config
    
    def can_handle(self, error: Exception) -> bool:
        """判断是否可以处理该错误"""
        return isinstance(error, WorkflowError)
    
    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """处理工作流错误"""
        if not isinstance(error, WorkflowError):
            # Non-workflow error, cannot handle
            return

        context = context or {}
        error_type = self._classify_error(error, context)

        # 尝试恢复
        self._attempt_recovery(error, error_type, context)
    
    def _classify_error(self, error: WorkflowError, context: Dict[str, Any]) -> WorkflowErrorType:
        """分类工作流错误"""
        # 根据异常类型分类
        if isinstance(error, WorkflowValidationError):
            return WorkflowErrorType.VALIDATION
        elif isinstance(error, WorkflowExecutionError):
            return WorkflowErrorType.EXECUTION
        elif isinstance(error, WorkflowStepError):
            return WorkflowErrorType.STEP
        elif isinstance(error, WorkflowTimeoutError):
            return WorkflowErrorType.TIMEOUT
        elif isinstance(error, WorkflowStateError):
            return WorkflowErrorType.STATE
        elif isinstance(error, WorkflowConfigError):
            return WorkflowErrorType.CONFIG
        elif isinstance(error, WorkflowDependencyError):
            return WorkflowErrorType.DEPENDENCY
        
        # 根据错误消息分类
        error_message = str(error).lower()
        
        if "permission" in error_message or "权限" in error_message:
            return WorkflowErrorType.PERMISSION
        elif "resource" in error_message or "资源" in error_message:
            return WorkflowErrorType.RESOURCE
        elif "concurrency" in error_message or "并发" in error_message:
            return WorkflowErrorType.CONCURRENCY
        elif "integration" in error_message or "集成" in error_message:
            return WorkflowErrorType.INTEGRATION
        elif "transition" in error_message or "转换" in error_message:
            return WorkflowErrorType.TRANSITION
        else:
            return WorkflowErrorType.UNKNOWN
    
    def _attempt_recovery(
        self,
        error: WorkflowError,
        error_type: WorkflowErrorType,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """尝试错误恢复"""
        # 首先尝试重试策略
        if error_type in self._retry_strategies:
            try:
                return self._retry_strategies[error_type](error, context)
            except Exception:
                # 静默失败，不记录日志
                pass

        # 然后尝试降级策略
        if error_type in self._fallback_strategies:
            try:
                return self._fallback_strategies[error_type](error, context)
            except Exception:
                # 静默失败，不记录日志
                pass

        return None
    
    def _retry_timeout(self, error: WorkflowTimeoutError, context: Dict[str, Any]) -> Optional[Any]:
        """超时错误重试策略"""
        step_id = getattr(error, 'step_id', None) or context.get('step_id')
        timeout = getattr(error, 'timeout', None)

        # 增加超时时间重试
        new_timeout = timeout * 1.5 if timeout else 60

        return {
            "action": "retry",
            "strategy": "increase_timeout",
            "new_timeout": new_timeout,
            "step_id": step_id,
            "reason": "timeout_recovery"
        }

    def _retry_resource(self, error: WorkflowError, context: Dict[str, Any]) -> Optional[Any]:
        """资源错误重试策略"""
        return {
            "action": "retry",
            "strategy": "delayed_retry",
            "delay": 5.0,  # 5秒延迟
            "max_retries": 3,
            "reason": "resource_recovery"
        }

    def _retry_dependency(self, error: WorkflowDependencyError, context: Dict[str, Any]) -> Optional[Any]:
        """依赖错误重试策略"""
        dependency_name = getattr(error, 'dependency_name', None)

        return {
            "action": "retry",
            "strategy": "dependency_check",
            "dependency_name": dependency_name,
            "reason": "dependency_recovery"
        }

    def _retry_integration(self, error: WorkflowError, context: Dict[str, Any]) -> Optional[Any]:
        """集成错误重试策略"""
        return {
            "action": "retry",
            "strategy": "exponential_backoff",
            "max_retries": 3,
            "backoff_factor": 2.0,
            "reason": "integration_recovery"
        }

    def _fallback_execution(self, error: WorkflowExecutionError, context: Dict[str, Any]) -> Optional[Any]:
        """执行错误降级策略"""
        execution_id = getattr(error, 'execution_id', None)
        step_id = getattr(error, 'step_id', None)

        return {
            "action": "fallback",
            "strategy": "skip_step",
            "execution_id": execution_id,
            "step_id": step_id,
            "reason": "execution_fallback"
        }

    def _fallback_step(self, error: WorkflowStepError, context: Dict[str, Any]) -> Optional[Any]:
        """步骤错误降级策略"""
        step_id = getattr(error, 'step_id', None)
        step_type = getattr(error, 'step_type', None)

        return {
            "action": "fallback",
            "strategy": "alternative_step",
            "step_id": step_id,
            "step_type": step_type,
            "reason": "step_fallback"
        }

    def _fallback_state(self, error: WorkflowStateError, context: Dict[str, Any]) -> Optional[Any]:
        """状态错误降级策略"""
        current_state = getattr(error, 'current_state', None)
        expected_state = getattr(error, 'expected_state', None)

        return {
            "action": "fallback",
            "strategy": "state_reset",
            "current_state": current_state,
            "expected_state": expected_state,
            "reason": "state_fallback"
        }

    def _fallback_config(self, error: WorkflowConfigError, context: Dict[str, Any]) -> Optional[Any]:
        """配置错误降级策略"""
        config_key = getattr(error, 'config_key', None)

        return {
            "action": "fallback",
            "strategy": "default_config",
            "config_key": config_key,
            "reason": "config_fallback"
        }


class WorkflowErrorRecoveryManager:
    """工作流错误恢复管理器"""

    def __init__(self, error_handler: WorkflowErrorHandler):
        self.error_handler = error_handler
        self._recovery_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def attempt_recovery(
        self,
        error: WorkflowError,
        context: Dict[str, Any],
        recovery_func: Optional[Callable] = None
    ) -> Optional[Any]:
        """尝试错误恢复"""
        workflow_id = context.get("workflow_id", "unknown")

        # 记录错误
        self._record_error(workflow_id, error, context)

        # 处理错误 (no return value now)
        self.error_handler.handle(error, context)

        # Since handle() no longer returns a value, we need to classify the error separately
        error_type = self.error_handler._classify_error(error, context)
        recovery_suggestion = self.error_handler._attempt_recovery(error, error_type, context)

        if recovery_suggestion and recovery_func:
            try:
                # 执行恢复函数
                result = recovery_func(recovery_suggestion)

                # 记录成功恢复
                self._record_recovery(workflow_id, "success", recovery_suggestion)

                return result

            except Exception:
                # 记录恢复失败
                self._record_recovery(workflow_id, "failed", recovery_suggestion)

        return recovery_suggestion
    
    def _record_error(self, workflow_id: str, error: WorkflowError, context: Dict[str, Any]) -> None:
        """记录错误"""
        if workflow_id not in self._recovery_history:
            self._recovery_history[workflow_id] = []
        
        self._recovery_history[workflow_id].append({
            "timestamp": time.time(),
            "type": "error",
            "error": str(error),
            "error_code": getattr(error, "error_code", None),
            "context": context
        })
    
    def _record_recovery(self, workflow_id: str, status: str, suggestion: Dict[str, Any]) -> None:
        """记录恢复结果"""
        if workflow_id not in self._recovery_history:
            self._recovery_history[workflow_id] = []
        
        self._recovery_history[workflow_id].append({
            "timestamp": time.time(),
            "type": "recovery",
            "status": status,
            "suggestion": suggestion
        })
    
    def get_recovery_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取恢复历史"""
        return self._recovery_history.get(workflow_id, [])


class WorkflowValidator:
    """工作流验证器"""
    
    @staticmethod
    def validate_workflow_config(config: Dict[str, Any]) -> List[str]:
        """验证工作流配置"""
        errors = []
        
        if not isinstance(config, dict):
            errors.append("工作流配置必须是字典类型")
            return errors
        
        # 检查必需字段
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"工作流配置缺少必需字段: {field}")
        
        # 检查节点配置
        if "nodes" in config:
            nodes = config["nodes"]
            if not isinstance(nodes, dict):
                errors.append("节点配置必须是字典类型")
            else:
                for node_id, node_config in nodes.items():
                    if not isinstance(node_config, dict):
                        errors.append(f"节点 {node_id} 配置必须是字典类型")
                        continue
                    
                    if "function_name" not in node_config:
                        errors.append(f"节点 {node_id} 缺少 function_name")
        
        # 检查边配置
        if "edges" in config:
            edges = config["edges"]
            if not isinstance(edges, list):
                errors.append("边配置必须是列表类型")
        
        return errors
    
    @staticmethod
    def validate_workflow_state(state: Dict[str, Any]) -> List[str]:
        """验证工作流状态"""
        errors = []
        
        if not isinstance(state, dict):
            errors.append("工作流状态必须是字典类型")
            return errors
        
        # 检查状态字段
        if "current_step" in state:
            current_step = state["current_step"]
            if not isinstance(current_step, str):
                errors.append("当前步骤必须是字符串类型")
        
        # 检查步骤历史
        if "step_history" in state:
            step_history = state["step_history"]
            if not isinstance(step_history, list):
                errors.append("步骤历史必须是列表类型")
        
        return errors


# 这些函数 are 工具函数 that can be used by service layer for registration
def get_workflow_error_handler() -> WorkflowErrorHandler:
    """获取工作流错误处理器实例"""
    return WorkflowErrorHandler()


# 便捷函数
def register_workflow_error_handler() -> None:
    """注册工作流错误处理器到统一错误处理框架"""
    from src.infrastructure.error_management import register_error_handler
    
    handler = WorkflowErrorHandler()
    
    # 注册所有工作流相关异常
    workflow_exceptions = [
        WorkflowError,
        WorkflowValidationError,
        WorkflowExecutionError,
        WorkflowStepError,
        WorkflowTimeoutError,
        WorkflowStateError,
        WorkflowConfigError,
        WorkflowDependencyError
    ]
    
    for exception_type in workflow_exceptions:
        register_error_handler(exception_type, handler)


def handle_workflow_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """处理工作流错误的便捷函数"""
    registry = ErrorHandlingRegistry()
    registry.handle_error(error, context or {})


def create_workflow_error_context(
    workflow_id: Optional[str] = None,
    step_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """创建工作流错误上下文"""
    context: Dict[str, Any] = {
        "timestamp": time.time()
    }
    
    if workflow_id:
        context["workflow_id"] = workflow_id
    
    if step_id:
        context["step_id"] = step_id
    
    if execution_id:
        context["execution_id"] = execution_id
    
    context.update(kwargs)
    return context