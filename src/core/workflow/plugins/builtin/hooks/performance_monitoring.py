"""性能监控插件

监控节点执行过程中的性能指标。
已更新：使用新的Hook插件接口。
"""

import logging
import time
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.plugins import IHookPlugin, PluginMetadata, PluginContext, HookContext, HookPoint, HookExecutionResult, PluginType


logger = logging.getLogger(__name__)


class PerformanceMonitoringPlugin(IHookPlugin):
    """性能监控插件
    
    监控节点执行过程中的性能指标，包括执行时间、超时检测等。
    """
    
    def __init__(self):
        """初始化性能监控插件"""
        self._config = {}
        self._execution_service = None
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="performance_monitoring",
            version="1.0.0",
            description="监控节点执行过程中的性能指标，包括执行时间、超时检测等",
            author="system",
            plugin_type=PluginType.HOOK,
            config_schema={
                "type": "object",
                "properties": {
                    "timeout_threshold": {
                        "type": "number",
                        "description": "超时阈值（秒）",
                        "default": 10.0,
                        "minimum": 1.0
                    },
                    "log_slow_executions": {
                        "type": "boolean",
                        "description": "是否记录慢执行",
                        "default": True
                    },
                    "metrics_collection": {
                        "type": "boolean",
                        "description": "是否收集指标",
                        "default": True
                    },
                    "slow_execution_threshold": {
                        "type": "number",
                        "description": "慢执行阈值（秒）",
                        "default": 5.0,
                        "minimum": 0.1
                    },
                    "enable_profiling": {
                        "type": "boolean",
                        "description": "是否启用性能分析",
                        "default": False
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
            "timeout_threshold": config.get("timeout_threshold", 10.0),
            "log_slow_executions": config.get("log_slow_executions", True),
            "metrics_collection": config.get("metrics_collection", True),
            "slow_execution_threshold": config.get("slow_execution_threshold", 5.0),
            "enable_profiling": config.get("enable_profiling", False)
        }
        
        logger.debug("性能监控插件初始化完成")
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
        """记录开始时间"""
        # 在上下文中记录开始时间
        if not context.metadata:
            context.metadata = {}
        context.metadata["performance_start_time"] = time.time()
        
        if self._config["enable_profiling"]:
            context.metadata["performance_profiling_enabled"] = True
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """计算执行时间并记录"""
        start_time = context.metadata.get("performance_start_time") if context.metadata else None
        if not start_time:
            return HookExecutionResult(should_continue=True)
        
        execution_time = time.time() - start_time
        
        # 更新性能统计
        if self._execution_service and self._config["metrics_collection"]:
            self._execution_service.update_performance_stats(
                context.node_type, 
                execution_time, 
                success=True
            )
        
        # 记录慢执行
        if self._config["log_slow_executions"] and execution_time > self._config["slow_execution_threshold"]:
            logger.warning(
                f"节点 {context.node_type} 执行较慢: {execution_time:.2f}s "
                f"(阈值: {self._config['slow_execution_threshold']}s)"
            )
        
        # 检查超时
        if execution_time > self._config["timeout_threshold"]:
            logger.error(
                f"节点 {context.node_type} 执行超时: {execution_time:.2f}s "
                f"(阈值: {self._config['timeout_threshold']}s)"
            )
            
            return HookExecutionResult(
                should_continue=False,
                force_next_node="timeout_handler",
                metadata={
                    "timeout_detected": True,
                    "execution_time": execution_time,
                    "timeout_threshold": self._config["timeout_threshold"]
                }
            )
        
        return HookExecutionResult(
            should_continue=True,
            metadata={"execution_time": execution_time}
        )
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """记录错误执行时间"""
        start_time = context.metadata.get("performance_start_time") if context.metadata else None
        if start_time:
            execution_time = time.time() - start_time
            
            if self._execution_service and self._config["metrics_collection"]:
                self._execution_service.update_performance_stats(
                    context.node_type, 
                    execution_time, 
                    success=False
                )
        
        return HookExecutionResult(should_continue=True)
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        return True
    
    def set_execution_service(self, service) -> None:
        """设置执行服务
        
        Args:
            service: Hook执行服务实例
        """
        self._execution_service = service
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点

        Returns:
            List[HookPoint]: 支持的Hook执行点列表
        """
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]