"""性能监控依赖注入配置

负责将性能监控服务注册到依赖注入容器中。
"""

from typing import TYPE_CHECKING

from .interfaces import IPerformanceMonitor
from .base_monitor import BasePerformanceMonitor
from .implementations.checkpoint_monitor import CheckpointPerformanceMonitor
from .implementations.llm_monitor import LLMPerformanceMonitor
from .implementations.workflow_monitor import WorkflowPerformanceMonitor
from .implementations.tool_monitor import ToolPerformanceMonitor

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
        # 注册基础性能监控器（作为默认实现）
        container.register_factory(
            IPerformanceMonitor,
            lambda: BasePerformanceMonitor(),
            lifetime="singleton"
        )
        
        # 注册具体实现
        container.register_factory(
            CheckpointPerformanceMonitor,
            lambda: CheckpointPerformanceMonitor(),
            lifetime="singleton"
        )
        
        container.register_factory(
            LLMPerformanceMonitor,
            lambda: LLMPerformanceMonitor(),
            lifetime="singleton"
        )
        
        container.register_factory(
            WorkflowPerformanceMonitor,
            lambda: WorkflowPerformanceMonitor(),
            lifetime="singleton"
        )
        
        container.register_factory(
            ToolPerformanceMonitor,
            lambda: ToolPerformanceMonitor(),
            lifetime="singleton"
        )