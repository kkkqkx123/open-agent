"""性能监控器工厂

提供统一的性能监控器创建和管理接口。
"""

from typing import Dict, Any, Optional
from .interfaces import IPerformanceMonitor
from .base_monitor import BasePerformanceMonitor
from .implementations.checkpoint_monitor import CheckpointPerformanceMonitor
from .implementations.llm_monitor import LLMPerformanceMonitor
from .implementations.workflow_monitor import WorkflowPerformanceMonitor
from .implementations.tool_monitor import ToolPerformanceMonitor


class PerformanceMonitorFactory:
    """性能监控器工厂类"""
    
    # 单例实例
    _instance: Optional['PerformanceMonitorFactory'] = None
    
    def __init__(self):
        """初始化工厂"""
        self._monitors: Dict[str, IPerformanceMonitor] = {}
        self._default_config: Dict[str, Any] = {
            "max_history_size": 1000,
            "sampling_rate": 1.0
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
    
    def create_monitor(self, monitor_type: str, **config) -> IPerformanceMonitor:
        """创建性能监控器
        
        Args:
            monitor_type: 监控器类型
            **config: 配置参数
            
        Returns:
            IPerformanceMonitor: 性能监控器实例
            
        Raises:
            ValueError: 当不支持的监控器类型时
        """
        # 合并配置
        final_config = {**self._default_config, **config}
        
        if monitor_type == "base":
            monitor = BasePerformanceMonitor(max_history_size=final_config["max_history_size"])
        elif monitor_type == "checkpoint":
            monitor = CheckpointPerformanceMonitor(max_history_size=final_config["max_history_size"])
        elif monitor_type == "llm":
            monitor = LLMPerformanceMonitor(max_history_size=final_config["max_history_size"])
        elif monitor_type == "workflow":
            monitor = WorkflowPerformanceMonitor(max_history_size=final_config["max_history_size"])
        elif monitor_type == "tool":
            monitor = ToolPerformanceMonitor(max_history_size=final_config["max_history_size"])
        else:
            raise ValueError(f"不支持的监控器类型: {monitor_type}")
        
        # 配置监控器
        monitor.configure(final_config)
        
        # 存储监控器实例
        self._monitors[monitor_type] = monitor
        
        return monitor
    
    def get_monitor(self, monitor_type: str) -> Optional[IPerformanceMonitor]:
        """获取已创建的性能监控器
        
        Args:
            monitor_type: 监控器类型
            
        Returns:
            IPerformanceMonitor: 性能监控器实例，如果不存在则返回None
        """
        return self._monitors.get(monitor_type)
    
    def get_all_monitors(self) -> Dict[str, IPerformanceMonitor]:
        """获取所有已创建的性能监控器
        
        Returns:
            Dict[str, IPerformanceMonitor]: 所有监控器实例
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
        """重置所有监控器"""
        for monitor in self._monitors.values():
            monitor.reset_metrics()