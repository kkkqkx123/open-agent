"""指标收集Hook

收集节点执行过程中的各种指标数据。
"""

from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.hooks import HookPoint, HookContext, HookExecutionResult
from .base import ConfigurableHook

logger = get_logger(__name__)


class MetricsCollectionHook(ConfigurableHook):
    """指标收集Hook
    
    收集节点执行过程中的各种指标数据，包括性能指标、业务指标和系统指标。
    """
    
    def __init__(self) -> None:
        """初始化指标收集Hook"""
        super().__init__(
            hook_id="metrics_collection",
            name="指标收集Hook",
            description="收集节点执行过程中的各种指标数据，包括性能指标、业务指标和系统指标",
            version="1.0.0"
        )
        
        # 设置默认配置
        self.set_default_config({
            "enable_performance_metrics": True,
            "enable_business_metrics": True,
            "enable_system_metrics": False,
            "metrics_endpoint": None,
            "collection_interval": 60
        })
        
        self._metrics: Dict[str, Any] = {}
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点"""
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录开始指标"""
        if not context.metadata:
            context.metadata = {}
        
        context.metadata["metrics_start_time"] = time.time()
        
        self._log_execution(HookPoint.BEFORE_EXECUTE)
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """收集执行指标"""
        start_time = context.metadata.get("metrics_start_time") if context.metadata else None
        if not start_time:
            return HookExecutionResult(should_continue=True)
        
        execution_time = time.time() - start_time
        
        # 收集性能指标
        if self.get_config_value("enable_performance_metrics"):
            self._collect_performance_metrics(context, execution_time)
        
        # 收集业务指标
        if self.get_config_value("enable_business_metrics"):
            self._collect_business_metrics(context)
        
        # 收集系统指标
        if self.get_config_value("enable_system_metrics"):
            self._collect_system_metrics(context)
        
        self._log_execution(HookPoint.AFTER_EXECUTE)
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """收集错误指标"""
        # 记录错误指标
        error_key = f"errors.{context.node_type}.{context.error.__class__.__name__ if context.error else 'unknown'}"
        self._metrics[error_key] = self._metrics.get(error_key, 0) + 1
        
        self._log_execution(HookPoint.ON_ERROR, error=context.error)
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
        
        if state is None:
            return
        
        # 消息数量
        if hasattr(state, 'messages'):
            message_key = f"business.{context.node_type}.message_count"
            self._metrics[message_key] = len(state.messages)
        
        # 迭代次数
        if hasattr(state, 'iteration_count'):
            iteration_key = f"business.{context.node_type}.iteration_count"
            self._metrics[iteration_key] = state.iteration_count
        
        # 工具调用次数 - 使用类型安全的接口
        messages = state.get_data("messages", []) if hasattr(state, 'get_data') else []
        tool_calls_count = 0
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'has_tool_calls') and callable(last_message.has_tool_calls):
                if last_message.has_tool_calls():
                    tool_calls_count = len(last_message.get_tool_calls())
        
        if tool_calls_count > 0:
            tool_calls_key = f"business.{context.node_type}.tool_calls_count"
            self._metrics[tool_calls_key] = tool_calls_count
    
    def _collect_system_metrics(self, context: HookContext) -> None:
        """收集系统指标"""
        try:
            import psutil
            
            # CPU使用率
            cpu_key = "system.cpu_percent"
            self._metrics[cpu_key] = psutil.cpu_percent()
            
            # 内存使用率
            memory_key = "system.memory_percent"
            self._metrics[memory_key] = psutil.virtual_memory().percent
        except ImportError:
            logger.debug("psutil未安装，跳过系统指标收集")
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取收集的指标
        
        Returns:
            Dict[str, Any]: 指标数据
        """
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """重置指标"""
        self._metrics.clear()
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Hook配置"""
        errors = super().validate_config(config)
        
        # 验证collection_interval
        collection_interval = config.get("collection_interval")
        if collection_interval is not None and (not isinstance(collection_interval, int) or collection_interval < 1):
            errors.append("collection_interval必须是大于0的整数")
        
        return errors