"""指标收集插件

收集节点执行过程中的各种指标数据。
"""

from src.services.logger.injection import get_logger
import time
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.plugins import IHookPlugin, PluginMetadata, PluginContext, HookContext, HookPoint, HookExecutionResult, PluginType


logger = get_logger(__name__)


class MetricsCollectionPlugin(IHookPlugin):
    """指标收集插件
    
    收集节点执行过程中的各种指标数据，包括性能指标、业务指标和系统指标。
    """
    
    def __init__(self):
        """初始化指标收集插件"""
        self._config = {}
        self._metrics: Dict[str, Any] = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="metrics_collection",
            version="1.0.0",
            description="收集节点执行过程中的各种指标数据，包括性能指标、业务指标和系统指标",
            author="system",
            plugin_type=PluginType.HOOK,
            supported_hook_points=[HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR],
            config_schema={
                "type": "object",
                "properties": {
                    "enable_performance_metrics": {
                        "type": "boolean",
                        "description": "是否启用性能指标收集",
                        "default": True
                    },
                    "enable_business_metrics": {
                        "type": "boolean",
                        "description": "是否启用业务指标收集",
                        "default": True
                    },
                    "enable_system_metrics": {
                        "type": "boolean",
                        "description": "是否启用系统指标收集",
                        "default": False
                    },
                    "metrics_endpoint": {
                        "type": "string",
                        "description": "指标推送端点",
                        "default": None
                    },
                    "collection_interval": {
                        "type": "integer",
                        "description": "收集间隔（秒）",
                        "default": 60,
                        "minimum": 1
                    }
                },
                "required": []
            }
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        self._config = {
            "enable_performance_metrics": config.get("enable_performance_metrics", True),
            "enable_business_metrics": config.get("enable_business_metrics", True),
            "enable_system_metrics": config.get("enable_system_metrics", False),
            "metrics_endpoint": config.get("metrics_endpoint"),
            "collection_interval": config.get("collection_interval", 60)
        }
        
        logger.debug("指标收集插件初始化完成")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑（Hook插件通常不使用此方法）
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        return state
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录开始指标"""
        if not context.metadata:
            context.metadata = {}
        
        context.metadata["metrics_start_time"] = time.time()
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """收集执行指标"""
        start_time = context.metadata.get("metrics_start_time") if context.metadata else None
        if not start_time:
            return HookExecutionResult(should_continue=True)
        
        execution_time = time.time() - start_time
        
        # 收集性能指标
        if self._config["enable_performance_metrics"]:
            self._collect_performance_metrics(context, execution_time)
        
        # 收集业务指标
        if self._config["enable_business_metrics"]:
            self._collect_business_metrics(context)
        
        # 收集系统指标
        if self._config["enable_system_metrics"]:
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
        
        # 工具调用次数
        if hasattr(state, 'tool_calls'):
            tool_calls_key = f"business.{context.node_type}.tool_calls_count"
            self._metrics[tool_calls_key] = len(getattr(state, 'tool_calls', []))
    
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
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        self._metrics.clear()
        return True
    
    def set_execution_service(self, service) -> None:
        """设置执行服务
        
        Args:
            service: Hook执行服务实例
        """
        pass  # MetricsCollection插件不需要执行服务