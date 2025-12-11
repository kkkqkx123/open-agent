"""性能监控Hook

监控节点执行过程中的性能指标。
"""

from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.hooks import HookPoint, HookContext, HookExecutionResult
from .base import ConfigurableHook

logger = get_logger(__name__)


class PerformanceMonitoringHook(ConfigurableHook):
    """性能监控Hook
    
    监控节点执行过程中的性能指标，包括执行时间、超时检测等。
    """
    
    def __init__(self):
        """初始化性能监控Hook"""
        super().__init__(
            hook_id="performance_monitoring",
            name="性能监控Hook",
            description="监控节点执行过程中的性能指标，包括执行时间、超时检测等",
            version="1.0.0"
        )
        
        # 设置默认配置
        self.set_default_config({
            "timeout_threshold": 10.0,
            "log_slow_executions": True,
            "metrics_collection": True,
            "slow_execution_threshold": 5.0,
            "enable_profiling": False
        })
        
        self._execution_service = None
        self._performance_stats: Dict[str, Dict[str, Any]] = {}
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点"""
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录开始时间"""
        # 在上下文中记录开始时间
        if not context.metadata:
            context.metadata = {}
        context.metadata["performance_start_time"] = time.time()
        
        if self.get_config_value("enable_profiling"):
            context.metadata["performance_profiling_enabled"] = True
        
        self._log_execution(HookPoint.BEFORE_EXECUTE)
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """计算执行时间并记录"""
        start_time = context.metadata.get("performance_start_time") if context.metadata else None
        if not start_time:
            return HookExecutionResult(should_continue=True)
        
        execution_time = time.time() - start_time
        
        # 更新性能统计
        if self._execution_service and self.get_config_value("metrics_collection"):
            self._execution_service.update_performance_stats(
                context.node_type, 
                execution_time, 
                success=True
            )
        
        # 记录慢执行
        if self.get_config_value("log_slow_executions"):
            slow_threshold = self.get_config_value("slow_execution_threshold", 5.0)
            if execution_time > slow_threshold:
                logger.warning(
                    f"节点 {context.node_type} 执行较慢: {execution_time:.2f}s "
                    f"(阈值: {slow_threshold}s)"
                )
        
        # 检查超时
        timeout_threshold = self.get_config_value("timeout_threshold", 10.0)
        if execution_time > timeout_threshold:
            logger.error(
                f"节点 {context.node_type} 执行超时: {execution_time:.2f}s "
                f"(阈值: {timeout_threshold}s)"
            )
            
            return HookExecutionResult(
                should_continue=False,
                force_next_node="timeout_handler",
                metadata={
                    "timeout_detected": True,
                    "execution_time": execution_time,
                    "timeout_threshold": timeout_threshold
                }
            )
        
        self._log_execution(HookPoint.AFTER_EXECUTE)
        return HookExecutionResult(
            should_continue=True,
            metadata={"execution_time": execution_time}
        )
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """记录错误执行时间"""
        start_time = context.metadata.get("performance_start_time") if context.metadata else None
        if start_time:
            execution_time = time.time() - start_time
            
            if self._execution_service and self.get_config_value("metrics_collection"):
                self._execution_service.update_performance_stats(
                    context.node_type, 
                    execution_time, 
                    success=False
                )
        
        self._log_execution(HookPoint.ON_ERROR, error=context.error)
        return HookExecutionResult(should_continue=True)
    
    def set_execution_service(self, service: Any) -> None:
        """设置执行服务

        Args:
            service: 执行服务实例
        """
        self._execution_service = service
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 性能统计信息
        """
        return self._performance_stats.copy()
    
    def update_performance_stats(
        self, 
        node_type: str, 
        execution_time: float, 
        success: bool = True
    ) -> None:
        """更新性能统计
        
        Args:
            node_type: 节点类型
            execution_time: 执行时间
            success: 是否成功
        """
        if node_type not in self._performance_stats:
            self._performance_stats[node_type] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "min_execution_time": float('inf'),
                "max_execution_time": 0.0,
                "avg_execution_time": 0.0
            }
        
        stats = self._performance_stats[node_type]
        stats["total_executions"] += 1
        stats["total_execution_time"] += execution_time
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        stats["min_execution_time"] = min(stats["min_execution_time"], execution_time)
        stats["max_execution_time"] = max(stats["max_execution_time"], execution_time)
        stats["avg_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Hook配置"""
        errors = super().validate_config(config)
        
        # 验证timeout_threshold
        timeout_threshold = config.get("timeout_threshold")
        if timeout_threshold is not None and (not isinstance(timeout_threshold, (int, float)) or timeout_threshold <= 0):
            errors.append("timeout_threshold必须是大于0的数字")
        
        # 验证slow_execution_threshold
        slow_threshold = config.get("slow_execution_threshold")
        if slow_threshold is not None and (not isinstance(slow_threshold, (int, float)) or slow_threshold <= 0):
            errors.append("slow_execution_threshold必须是大于0的数字")
        
        return errors