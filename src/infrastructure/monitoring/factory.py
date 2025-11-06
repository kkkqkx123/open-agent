"""性能监控器工厂

提供统一的性能监控器创建和管理接口，采用零内存存储架构。
"""

from typing import Dict, Any, Optional

from .logger_writer import PerformanceMetricsLogger
from .lightweight_monitor import LightweightPerformanceMonitor
from .implementations.checkpoint_monitor import CheckpointPerformanceMonitor
from .implementations.llm_monitor import LLMPerformanceMonitor
from .implementations.workflow_monitor import WorkflowPerformanceMonitor
from .implementations.tool_monitor import ToolPerformanceMonitor


class PerformanceMonitorFactory:
    """性能监控器工厂类 - 零内存存储版本"""
    
    # 单例实例
    _instance: Optional['PerformanceMonitorFactory'] = None
    
    def __init__(self):
        """初始化工厂"""
        self._monitors: Dict[str, LightweightPerformanceMonitor] = {}
        self._default_config: Dict[str, Any] = {
            "enabled": True
        }
    
    @classmethod
    def get_instance(cls) -> 'PerformanceMonitorFactory':
        """获取工厂单例实例
        
        Returns:
            PerformanceMonitorFactory: 工厂实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def create_monitor(self, monitor_type: str, **config) -> LightweightPerformanceMonitor:
        """创建性能监控器
        
        Args:
            monitor_type: 监控器类型
            **config: 配置参数
            
        Returns:
            LightweightPerformanceMonitor: 性能监控器实例
            
        Raises:
            ValueError: 当不支持的监控器类型时
        """
        # 合并配置
        final_config = {**self._default_config, **config}
        
        # 创建专用的日志写入器
        logger_name = f"{monitor_type}_metrics"
        logger = PerformanceMetricsLogger(logger_name)
        
        if monitor_type == "base":
            monitor = LightweightPerformanceMonitor(logger)
        elif monitor_type == "checkpoint":
            monitor = CheckpointPerformanceMonitor(logger)
        elif monitor_type == "llm":
            monitor = LLMPerformanceMonitor(logger)
        elif monitor_type == "workflow":
            monitor = WorkflowPerformanceMonitor(logger)
        elif monitor_type == "tool":
            monitor = ToolPerformanceMonitor(logger)
        else:
            raise ValueError(f"不支持的监控器类型: {monitor_type}")
        
        # 配置监控器
        monitor.configure(final_config)
        
        # 存储监控器实例
        self._monitors[monitor_type] = monitor
        
        return monitor
    
    def get_monitor(self, monitor_type: str) -> Optional[LightweightPerformanceMonitor]:
        """获取已创建的性能监控器
        
        Args:
            monitor_type: 监控器类型
            
        Returns:
            LightweightPerformanceMonitor: 性能监控器实例，如果不存在则返回None
        """
        return self._monitors.get(monitor_type)
    
    def get_all_monitors(self) -> Dict[str, LightweightPerformanceMonitor]:
        """获取所有已创建的性能监控器
        
        Returns:
            Dict[str, LightweightPerformanceMonitor]: 所有监控器实例
        """
        return self._monitors.copy()
    
    def configure_monitor(self, monitor_type: str, config: Dict[str, Any]) -> None:
        """配置特定类型的监控器
        
        Args:
            monitor_type: 监控器类型
            config: 配置字典
        """
        monitor = self._monitors.get(monitor_type)
        if monitor:
            monitor.configure(config)
    
    def reset_all_monitors(self) -> None:
        """重置所有监控器
        
        在零内存存储模式下，此方法不执行任何操作。
        """
        pass