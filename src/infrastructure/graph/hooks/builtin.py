"""内置Hook实现

提供常用的Hook实现，包括死循环检测、性能监控、错误恢复等。
"""

import logging
import time
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime

from .interfaces import INodeHook, HookContext, HookExecutionResult, HookPoint
from .config import HookType

logger = logging.getLogger(__name__)


class DeadLoopDetectionHook(INodeHook):
    """死循环检测Hook"""
    
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        super().__init__(hook_config)
        self.max_iterations = hook_config.get("max_iterations", 20)
        self.fallback_node = hook_config.get("fallback_node", "dead_loop_check")
        self.log_level = hook_config.get("log_level", "WARNING")
        self.check_interval = hook_config.get("check_interval", 1)
        self.reset_on_success = hook_config.get("reset_on_success", True)
    
    @property
    def hook_type(self) -> str:
        return HookType.DEAD_LOOP_DETECTION
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行前检查死循环"""
        # 获取Hook管理器中的执行计数
        hook_manager = getattr(context, 'hook_manager', None)
        if not hook_manager:
            return HookExecutionResult(should_continue=True)
        
        execution_count = hook_manager.get_execution_count(context.node_type)
        
        # 每隔一定间隔检查一次
        if execution_count % self.check_interval == 0 and execution_count > 0:
            if execution_count >= self.max_iterations:
                log_message = (
                    f"节点 {context.node_type} 可能陷入死循环，"
                    f"执行次数: {execution_count}, 最大允许: {self.max_iterations}"
                )
                
                if self.log_level == "WARNING":
                    logger.warning(log_message)
                elif self.log_level == "ERROR":
                    logger.error(log_message)
                else:
                    logger.info(log_message)
                
                # 强制切换到回退节点
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node=self.fallback_node,
                    metadata={
                        "dead_loop_detected": True,
                        "execution_count": execution_count,
                        "max_iterations": self.max_iterations
                    }
                )
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行后更新计数"""
        hook_manager = getattr(context, 'hook_manager', None)
        if hook_manager:
            hook_manager.increment_execution_count(context.node_type)
        
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误时不重置计数"""
        return HookExecutionResult(should_continue=True)
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]


class PerformanceMonitoringHook(INodeHook):
    """性能监控Hook"""
    
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        super().__init__(hook_config)
        self.timeout_threshold = hook_config.get("timeout_threshold", 10.0)
        self.log_slow_executions = hook_config.get("log_slow_executions", True)
        self.metrics_collection = hook_config.get("metrics_collection", True)
        self.slow_execution_threshold = hook_config.get("slow_execution_threshold", 5.0)
        self.enable_profiling = hook_config.get("enable_profiling", False)
    
    @property
    def hook_type(self) -> str:
        return HookType.PERFORMANCE_MONITORING
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录开始时间"""
        # 在上下文中记录开始时间
        if not context.metadata:
            context.metadata = {}
        context.metadata["performance_start_time"] = time.time()
        
        if self.enable_profiling:
            context.metadata["performance_profiling_enabled"] = True
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """计算执行时间并记录"""
        start_time = context.metadata.get("performance_start_time")
        if not start_time:
            return HookExecutionResult(should_continue=True)
        
        execution_time = time.time() - start_time
        
        # 更新性能统计
        hook_manager = getattr(context, 'hook_manager', None)
        if hook_manager and self.metrics_collection:
            hook_manager.update_performance_stats(
                context.node_type, 
                execution_time, 
                success=True
            )
        
        # 记录慢执行
        if self.log_slow_executions and execution_time > self.slow_execution_threshold:
            logger.warning(
                f"节点 {context.node_type} 执行较慢: {execution_time:.2f}s "
                f"(阈值: {self.slow_execution_threshold}s)"
            )
        
        # 检查超时
        if execution_time > self.timeout_threshold:
            logger.error(
                f"节点 {context.node_type} 执行超时: {execution_time:.2f}s "
                f"(阈值: {self.timeout_threshold}s)"
            )
            
            return HookExecutionResult(
                should_continue=False,
                force_next_node="timeout_handler",
                metadata={
                    "timeout_detected": True,
                    "execution_time": execution_time,
                    "timeout_threshold": self.timeout_threshold
                }
            )
        
        return HookExecutionResult(
            should_continue=True,
            metadata={"execution_time": execution_time}
        )
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """记录错误执行时间"""
        start_time = context.metadata.get("performance_start_time")
        if start_time:
            execution_time = time.time() - start_time
            
            hook_manager = getattr(context, 'hook_manager', None)
            if hook_manager and self.metrics_collection:
                hook_manager.update_performance_stats(
                    context.node_type, 
                    execution_time, 
                    success=False
                )
        
        return HookExecutionResult(should_continue=True)
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]


class ErrorRecoveryHook(INodeHook):
    """错误恢复Hook"""
    
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        super().__init__(hook_config)
        self.max_retries = hook_config.get("max_retries", 3)
        self.fallback_node = hook_config.get("fallback_node", "error_handler")
        self.retry_delay = hook_config.get("retry_delay", 1.0)
        self.exponential_backoff = hook_config.get("exponential_backoff", True)
        self.retry_on_exceptions = hook_config.get("retry_on_exceptions", ["Exception"])
    
    @property
    def hook_type(self) -> str:
        return HookType.ERROR_RECOVERY
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """检查重试次数"""
        if not context.metadata:
            context.metadata = {}
        
        retry_count = context.metadata.get("retry_count", 0)
        
        if retry_count >= self.max_retries:
            logger.error(
                f"节点 {context.node_type} 重试次数已达上限: {retry_count}/{self.max_retries}"
            )
            return HookExecutionResult(
                should_continue=False,
                force_next_node=self.fallback_node,
                metadata={
                    "max_retries_exceeded": True,
                    "retry_count": retry_count
                }
            )
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """成功执行后重置重试计数"""
        if context.metadata and "retry_count" in context.metadata:
            context.metadata["retry_count"] = 0
        
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理和重试逻辑"""
        if not context.metadata:
            context.metadata = {}
        
        error = context.error
        if not error:
            return HookExecutionResult(should_continue=True)
        
        # 检查是否是需要重试的异常类型
        should_retry = any(
            error.__class__.__name__ in exception_types 
            for exception_types in self.retry_on_exceptions
            if isinstance(exception_types, list)
        ) or any(
            error.__class__.__name__ == exception_type
            for exception_type in self.retry_on_exceptions
            if isinstance(exception_type, str)
        )
        
        if not should_retry:
            logger.error(f"节点 {context.node_type} 发生不可重试错误: {error}")
            return HookExecutionResult(
                should_continue=False,
                force_next_node=self.fallback_node,
                metadata={"unrecoverable_error": True, "error": str(error)}
            )
        
        # 增加重试计数
        retry_count = context.metadata.get("retry_count", 0) + 1
        context.metadata["retry_count"] = retry_count
        
        if retry_count >= self.max_retries:
            logger.error(
                f"节点 {context.node_type} 重试次数已达上限: {retry_count}/{self.max_retries}"
            )
            return HookExecutionResult(
                should_continue=False,
                force_next_node=self.fallback_node,
                metadata={
                    "max_retries_exceeded": True,
                    "retry_count": retry_count,
                    "last_error": str(error)
                }
            )
        
        # 计算延迟时间
        if self.exponential_backoff:
            delay = self.retry_delay * (2 ** (retry_count - 1))
        else:
            delay = self.retry_delay
        
        logger.warning(
            f"节点 {context.node_type} 第 {retry_count} 次重试，"
            f"延迟 {delay:.1f}s，错误: {error}"
        )
        
        # 等待延迟时间
        time.sleep(delay)
        
        return HookExecutionResult(
            should_continue=True,
            metadata={
                "retry_scheduled": True,
                "retry_count": retry_count,
                "retry_delay": delay
            }
        )
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]


class LoggingHook(INodeHook):
    """日志Hook"""
    
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        super().__init__(hook_config)
        self.log_level = hook_config.get("log_level", "INFO")
        self.structured_logging = hook_config.get("structured_logging", True)
        self.log_execution_time = hook_config.get("log_execution_time", True)
        self.log_state_changes = hook_config.get("log_state_changes", False)
        self.log_format = hook_config.get("log_format", "json")
    
    @property
    def hook_type(self) -> str:
        return HookType.LOGGING
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行开始日志"""
        log_data = {
            "event": "node_execution_started",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.log_state_changes:
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data)
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行完成日志"""
        log_data = {
            "event": "node_execution_completed",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.log_execution_time and context.metadata:
            execution_time = context.metadata.get("execution_time")
            if execution_time:
                log_data["execution_time"] = execution_time
        
        if context.execution_result and context.execution_result.next_node:
            log_data["next_node"] = context.execution_result.next_node
        
        if self.log_state_changes:
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data)
        
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """记录错误日志"""
        log_data = {
            "event": "node_execution_error",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(context.error) if context.error else "Unknown error",
            "error_type": context.error.__class__.__name__ if context.error else "Unknown"
        }
        
        if self.log_state_changes:
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data, level="ERROR")
        
        return HookExecutionResult(should_continue=True)
    
    def _get_state_summary(self, state) -> Dict[str, Any]:
        """获取状态摘要"""
        try:
            summary = {
                "message_count": len(getattr(state, 'messages', [])),
                "iteration_count": getattr(state, 'iteration_count', 0),
                "has_errors": bool(getattr(state, 'errors', []))
            }
            
            if hasattr(state, 'context') and state.context:
                summary["context_keys"] = list(state.context.keys())
            
            return summary
        except Exception:
            return {"error": "Failed to summarize state"}
    
    def _log(self, log_data: Dict[str, Any], level: Optional[str] = None) -> None:
        """记录日志"""
        log_level = level or self.log_level
        
        if self.structured_logging:
            if self.log_format == "json":
                import json
                message = json.dumps(log_data, ensure_ascii=False)
            else:
                message = " | ".join([f"{k}={v}" for k, v in log_data.items()])
        else:
            message = f"{log_data.get('event', 'unknown')} - {log_data.get('node_type', 'unknown')}"
        
        if log_level == "DEBUG":
            logger.debug(message)
        elif log_level == "INFO":
            logger.info(message)
        elif log_level == "WARNING":
            logger.warning(message)
        elif log_level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]


class MetricsCollectionHook(INodeHook):
    """指标收集Hook"""
    
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        super().__init__(hook_config)
        self.enable_performance_metrics = hook_config.get("enable_performance_metrics", True)
        self.enable_business_metrics = hook_config.get("enable_business_metrics", True)
        self.enable_system_metrics = hook_config.get("enable_system_metrics", False)
        self.metrics_endpoint = hook_config.get("metrics_endpoint")
        self.collection_interval = hook_config.get("collection_interval", 60)
        
        # 指标存储
        self._metrics: Dict[str, Any] = {}
    
    @property
    def hook_type(self) -> str:
        return HookType.METRICS_COLLECTION
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录开始指标"""
        if not context.metadata:
            context.metadata = {}
        
        context.metadata["metrics_start_time"] = time.time()
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """收集执行指标"""
        start_time = context.metadata.get("metrics_start_time")
        if not start_time:
            return HookExecutionResult(should_continue=True)
        
        execution_time = time.time() - start_time
        
        # 收集性能指标
        if self.enable_performance_metrics:
            self._collect_performance_metrics(context, execution_time)
        
        # 收集业务指标
        if self.enable_business_metrics:
            self._collect_business_metrics(context)
        
        # 收集系统指标
        if self.enable_system_metrics:
            self._collect_system_metrics(context)
        
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """收集错误指标"""
        # 记录错误指标
        error_key = f"errors.{context.node_type}.{context.error.__class__.__name__ if context.error else 'unknown'}"
        self._metrics[error_key] = self._metrics.get(error_key, 0) + 1
        
        return HookExecutionResult(should_continue=True)
    
    def _collect_performance_metrics(self, context: HookContext, execution_time: float) -> None:
        """收集性能指标"""
        node_type = context.node_type
        
        # 执行时间指标
        time_key = f"performance.{node_type}.execution_time"
        if time_key not in self._metrics:
            self._metrics[time_key] = []
        self._metrics[time_key].append(execution_time)
        
        # 执行计数
        count_key = f"performance.{node_type}.execution_count"
        self._metrics[count_key] = self._metrics.get(count_key, 0) + 1
    
    def _collect_business_metrics(self, context: HookContext) -> None:
        """收集业务指标"""
        state = context.state
        
        # 消息数量
        if hasattr(state, 'messages'):
            message_key = f"business.{context.node_type}.message_count"
            self._metrics[message_key] = len(state.messages)
        
        # 迭代次数
        if hasattr(state, 'iteration_count'):
            iteration_key = f"business.{context.node_type}.iteration_count"
            self._metrics[iteration_key] = state.iteration_count
        
        # 工具调用次数
        if hasattr(state, 'tool_calls'):
            tool_calls_key = f"business.{context.node_type}.tool_calls_count"
            self._metrics[tool_calls_key] = len(state.tool_calls)
    
    def _collect_system_metrics(self, context: HookContext) -> None:
        """收集系统指标"""
        import psutil
        
        # CPU使用率
        cpu_key = "system.cpu_percent"
        self._metrics[cpu_key] = psutil.cpu_percent()
        
        # 内存使用率
        memory_key = "system.memory_percent"
        self._metrics[memory_key] = psutil.virtual_memory().percent
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取收集的指标"""
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """重置指标"""
        self._metrics.clear()
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]


# Hook工厂函数
def create_builtin_hook(hook_config: Dict[str, Any]) -> Optional[INodeHook]:
    """创建内置Hook实例
    
    Args:
        hook_config: Hook配置
        
    Returns:
        Optional[INodeHook]: Hook实例
    """
    hook_type = hook_config.get("type")
    if not hook_type:
        return None
    
    hook_classes = {
        HookType.DEAD_LOOP_DETECTION: DeadLoopDetectionHook,
        HookType.PERFORMANCE_MONITORING: PerformanceMonitoringHook,
        HookType.ERROR_RECOVERY: ErrorRecoveryHook,
        HookType.LOGGING: LoggingHook,
        HookType.METRICS_COLLECTION: MetricsCollectionHook,
    }
    
    hook_class = hook_classes.get(hook_type)
    if not hook_class:
        return None
    
    return hook_class(hook_config)