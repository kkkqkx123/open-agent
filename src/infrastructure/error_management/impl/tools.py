"""
工具模块错误处理器

提供统一的工具错误处理和恢复策略，集成到统一错误处理框架中。
"""

from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Callable, Optional, Any, List
from enum import Enum

from src.infrastructure.error_management import (
    BaseErrorHandler, ErrorCategory, ErrorSeverity,
    ErrorHandlingRegistry, operation_with_retry
)
from src.interfaces.tool.exceptions import ToolError, ToolExecutionError, ToolRegistrationError
from src.interfaces.tool.base import ToolCall, ToolResult

logger = get_logger(__name__)


class ToolErrorType(Enum):
    """工具错误类型"""
    VALIDATION = "validation"           # 参数验证错误
    EXECUTION = "execution"             # 执行错误
    TIMEOUT = "timeout"                 # 超时错误
    PERMISSION = "permission"           # 权限错误
    RESOURCE = "resource"               # 资源错误
    CONFIGURATION = "configuration"     # 配置错误
    NETWORK = "network"                 # 网络错误
    UNKNOWN = "unknown"                 # 未知错误


class ToolErrorHandler(BaseErrorHandler):
    """工具错误处理器"""
    
    def __init__(self):
        super().__init__(ErrorCategory.TOOL, ErrorSeverity.MEDIUM)
        self._retry_strategies: Dict[ToolErrorType, Callable] = {}
        self._fallback_strategies: Dict[ToolErrorType, Callable] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认的错误处理策略"""
        # 注册重试策略
        self._retry_strategies[ToolErrorType.TIMEOUT] = self._retry_timeout
        self._retry_strategies[ToolErrorType.NETWORK] = self._retry_network
        self._retry_strategies[ToolErrorType.RESOURCE] = self._retry_resource
        
        # 注册降级策略
        self._fallback_strategies[ToolErrorType.EXECUTION] = self._fallback_execution
        self._fallback_strategies[ToolErrorType.PERMISSION] = self._fallback_permission
    
    def can_handle(self, error: Exception) -> bool:
        """判断是否可以处理该错误"""
        return isinstance(error, ToolError)
    
    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """处理工具错误"""
        if not isinstance(error, ToolError):
            logger.warning(f"非工具错误，无法处理: {type(error).__name__}")
            return
        
        if context is None:
            context = {}
        error_type = self._classify_error(error, context)
        
        logger.error(
            f"工具错误处理: {error_type.value}",
            extra={
                "error_message": str(error),
                "error_type": error_type.value,
                "context": context,
                "tool_name": context.get("tool_name"),
                "error_code": getattr(error, "error_code", None)
            }
        )
        
        # 尝试恢复
        recovery_result = self._attempt_recovery(error, error_type, context)
        if recovery_result:
            logger.info(f"工具错误已恢复: {error_type.value}")
        else:
            logger.warning(f"工具错误无法恢复: {error_type.value}")
    
    def _classify_error(self, error: ToolError, context: Dict[str, Any]) -> ToolErrorType:
        """分类工具错误"""
        error_message = str(error).lower()
        
        # 根据错误消息分类
        if "timeout" in error_message or "超时" in error_message:
            return ToolErrorType.TIMEOUT
        elif "permission" in error_message or "权限" in error_message:
            return ToolErrorType.PERMISSION
        elif "network" in error_message or "网络" in error_message or "connection" in error_message:
            return ToolErrorType.NETWORK
        elif "validation" in error_message or "验证" in error_message or "invalid" in error_message:
            return ToolErrorType.VALIDATION
        elif "resource" in error_message or "资源" in error_message:
            return ToolErrorType.RESOURCE
        elif "config" in error_message or "配置" in error_message:
            return ToolErrorType.CONFIGURATION
        elif isinstance(error, ToolExecutionError):
            return ToolErrorType.EXECUTION
        else:
            return ToolErrorType.UNKNOWN
    
    def _attempt_recovery(
        self, 
        error: ToolError, 
        error_type: ToolErrorType, 
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """尝试错误恢复"""
        # 首先尝试重试策略
        if error_type in self._retry_strategies:
            try:
                return self._retry_strategies[error_type](error, context)
            except Exception as e:
                logger.warning(f"重试策略失败: {e}")
        
        # 然后尝试降级策略
        if error_type in self._fallback_strategies:
            try:
                return self._fallback_strategies[error_type](error, context)
            except Exception as e:
                logger.warning(f"降级策略失败: {e}")
        
        return None
    
    def _retry_timeout(self, error: ToolError, context: Dict[str, Any]) -> Optional[Any]:
        """超时错误重试策略"""
        tool_call = context.get("tool_call")
        if not tool_call:
            return None
        
        # 增加超时时间重试
        original_timeout = tool_call.timeout or 30
        new_timeout = original_timeout * 1.5
        
        logger.info(f"超时重试: {original_timeout}s -> {new_timeout}s")
        
        # 这里应该调用实际的工具执行逻辑
        # 由于我们在错误处理器中，只能返回建议
        return {
            "action": "retry",
            "new_timeout": new_timeout,
            "reason": "timeout_recovery"
        }
    
    def _retry_network(self, error: ToolError, context: Dict[str, Any]) -> Optional[Any]:
        """网络错误重试策略"""
        logger.info("网络错误重试: 使用指数退避")
        
        return {
            "action": "retry",
            "backoff_strategy": "exponential",
            "max_retries": 3,
            "reason": "network_recovery"
        }
    
    def _retry_resource(self, error: ToolError, context: Dict[str, Any]) -> Optional[Any]:
        """资源错误重试策略"""
        logger.info("资源错误重试: 延迟后重试")
        
        return {
            "action": "retry",
            "delay": 2.0,  # 2秒延迟
            "max_retries": 2,
            "reason": "resource_recovery"
        }
    
    def _fallback_execution(self, error: ToolError, context: Dict[str, Any]) -> Optional[Any]:
        """执行错误降级策略"""
        tool_name = context.get("tool_name", "unknown")
        
        logger.warning(f"工具执行错误降级: {tool_name}")
        
        # 返回一个默认的错误结果
        return ToolResult(
            success=False,
            error=f"工具 {tool_name} 执行失败，已启用降级模式",
            tool_name=tool_name,
            metadata={"fallback": True, "original_error": str(error)}
        )
    
    def _fallback_permission(self, error: ToolError, context: Dict[str, Any]) -> Optional[Any]:
        """权限错误降级策略"""
        tool_name = context.get("tool_name", "unknown")
        
        logger.warning(f"工具权限错误降级: {tool_name}")
        
        # 返回权限不足的提示
        return ToolResult(
            success=False,
            error=f"工具 {tool_name} 需要额外权限，请联系管理员",
            tool_name=tool_name,
            metadata={"permission_error": True, "original_error": str(error)}
        )


class ToolExecutionValidator:
    """工具执行验证器"""
    
    @staticmethod
    def validate_tool_call(tool_call: ToolCall) -> List[str]:
        """验证工具调用"""
        errors = []
        
        if not tool_call.name:
            errors.append("工具名称不能为空")
        
        if not isinstance(tool_call.arguments, dict):
            errors.append("工具参数必须是字典类型")
        
        if tool_call.timeout and tool_call.timeout <= 0:
            errors.append("超时时间必须大于0")
        
        return errors
    
    @staticmethod
    def validate_tool_result(result: ToolResult) -> List[str]:
        """验证工具结果"""
        errors = []
        
        if result.success is None:
            errors.append("执行结果必须指定成功状态")
        
        if not result.success and not result.error:
            errors.append("失败结果必须包含错误信息")
        
        if result.execution_time is not None and result.execution_time < 0:
            errors.append("执行时间不能为负数")
        
        return errors


class ToolErrorRecoveryManager:
    """工具错误恢复管理器"""
    
    def __init__(self, error_handler: ToolErrorHandler):
        self.error_handler = error_handler
        self._recovery_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def attempt_recovery(
        self, 
        error: ToolError, 
        tool_call: ToolCall, 
        executor_func: Callable
    ) -> ToolResult:
        """尝试错误恢复并重新执行"""
        tool_name = tool_call.name
        context = {
            "tool_name": tool_name,
            "tool_call": tool_call,
            "timestamp": time.time()
        }
        
        # 记录错误
        self._record_error(tool_name, error, context)
        
        # 处理错误
        self.error_handler.handle(error, context)
        
        # 检查是否有恢复建议
        recovery_suggestion = self.error_handler._attempt_recovery(
            error, 
            self.error_handler._classify_error(error, context), 
            context
        )
        
        if recovery_suggestion and recovery_suggestion.get("action") == "retry":
            return self._retry_execution(tool_call, executor_func, recovery_suggestion)
        
        # 无法恢复，返回错误结果
        return ToolResult(
            success=False,
            error=str(error),
            tool_name=tool_name,
            metadata={"recovery_attempted": True, "recovery_failed": True}
        )
    
    def _retry_execution(
        self,
        tool_call: ToolCall,
        executor_func: Callable,
        recovery_suggestion: Dict[str, Any]
    ) -> ToolResult:
        """重试执行"""
        try:
            # 根据恢复建议调整参数
            if recovery_suggestion.get("new_timeout"):
                tool_call.timeout = recovery_suggestion["new_timeout"]
            
            # 使用统一框架的重试机制
            max_retries = recovery_suggestion.get("max_retries", 3)
            backoff_factor = recovery_suggestion.get("backoff_factor", 2.0)
            
            def execute_tool():
                return executor_func(tool_call)
            
            # 定义可重试的异常类型
            retryable_exceptions = (
                TimeoutError,
                ConnectionError,
                OSError,
                ToolExecutionError
            )
            
            # 使用统一框架的重试函数
            result = operation_with_retry(
                execute_tool,
                max_retries=max_retries,
                retryable_exceptions=retryable_exceptions,
                context={
                    "tool_name": tool_call.name,
                    "tool_call": tool_call,
                    "recovery_suggestion": recovery_suggestion
                }
            )
            
            # 记录成功恢复
            self._record_recovery(tool_call.name, "success", recovery_suggestion)
            
            return result
            
        except Exception as e:
            # 记录恢复失败
            self._record_recovery(tool_call.name, "failed", recovery_suggestion)
            
            return ToolResult(
                success=False,
                error=f"重试失败: {str(e)}",
                tool_name=tool_call.name,
                metadata={"recovery_attempted": True, "retry_failed": True}
            )
    
    def _record_error(self, tool_name: str, error: ToolError, context: Dict[str, Any]) -> None:
        """记录错误"""
        if tool_name not in self._recovery_history:
            self._recovery_history[tool_name] = []
        
        self._recovery_history[tool_name].append({
            "timestamp": time.time(),
            "type": "error",
            "error": str(error),
            "context": context
        })
    
    def _record_recovery(self, tool_name: str, status: str, suggestion: Dict[str, Any]) -> None:
        """记录恢复结果"""
        if tool_name not in self._recovery_history:
            self._recovery_history[tool_name] = []
        
        self._recovery_history[tool_name].append({
            "timestamp": time.time(),
            "type": "recovery",
            "status": status,
            "suggestion": suggestion
        })
    
    def get_recovery_history(self, tool_name: str) -> List[Dict[str, Any]]:
        """获取恢复历史"""
        return self._recovery_history.get(tool_name, [])


# 注册工具错误处理器到全局注册表
def register_tool_error_handler():
    """注册工具错误处理器到全局注册表"""
    registry = ErrorHandlingRegistry()
    tool_handler = ToolErrorHandler()
    
    # 注册处理器
    registry.register_handler(ToolError, tool_handler)
    registry.register_handler(ToolExecutionError, tool_handler)
    registry.register_handler(ToolRegistrationError, tool_handler)
    
    logger.info("工具错误处理器已注册到全局注册表")


# 便捷函数
def handle_tool_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """处理工具错误的便捷函数"""
    registry = ErrorHandlingRegistry()
    registry.handle_error(error, context if context is not None else {})


def create_tool_error_context(tool_call: Optional[ToolCall], **kwargs) -> Dict[str, Any]:
    """创建工具错误上下文"""
    context: Dict[str, Any] = {
        "timestamp": time.time()
    }
    
    if tool_call:
        context.update({
            "tool_name": tool_call.name,
            "tool_arguments": tool_call.arguments,
            "tool_timeout": tool_call.timeout
        })
    
    context.update(kwargs)
    return context