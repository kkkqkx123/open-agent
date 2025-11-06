"""性能监控依赖注入配置

负责将性能监控服务注册到依赖注入容器中。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..container import IDependencyContainer


class MonitoringModule:
    """性能监控模块"""
    
    @staticmethod
    def register_services(container: 'IDependencyContainer') -> None:
        """注册性能监控服务
        
        Args:
            container: 依赖注入容器
        """
        # 注册性能指标日志写入器
        from .logger_writer import PerformanceMetricsLogger
        container.register_factory(
            PerformanceMetricsLogger,
            lambda: PerformanceMetricsLogger(),
            lifetime="singleton"
        )
        
        # 注册轻量级性能监控器（作为默认实现）
        from .lightweight_monitor import LightweightPerformanceMonitor
        container.register_factory(
            LightweightPerformanceMonitor,
            lambda: LightweightPerformanceMonitor(),
            lifetime="singleton"
        )
        
        # 注册具体实现
        from .implementations.checkpoint_monitor import CheckpointPerformanceMonitor
        container.register_factory(
            CheckpointPerformanceMonitor,
            lambda: CheckpointPerformanceMonitor(),
            lifetime="singleton"
        )
        
        from .implementations.llm_monitor import LLMPerformanceMonitor
        container.register_factory(
            LLMPerformanceMonitor,
            lambda: LLMPerformanceMonitor(),
            lifetime="singleton"
        )
        
        from .implementations.workflow_monitor import WorkflowPerformanceMonitor
        container.register_factory(
            WorkflowPerformanceMonitor,
            lambda: WorkflowPerformanceMonitor(),
            lifetime="singleton"
        )
        
        from .implementations.tool_monitor import ToolPerformanceMonitor
        container.register_factory(
            ToolPerformanceMonitor,
            lambda: ToolPerformanceMonitor(),
            lifetime="singleton"
        )
        
        # 注册工厂类
        from .factory import PerformanceMonitorFactory
        container.register_factory(
            PerformanceMonitorFactory,
            lambda: PerformanceMonitorFactory(),
            lifetime="singleton"
        )
        
        # 注册日志清理服务
        from .scheduler import LogCleanupService
        container.register_factory(
            LogCleanupService,
            lambda: LogCleanupService(container.get(PerformanceMonitorFactory)),
            lifetime="singleton"
        )