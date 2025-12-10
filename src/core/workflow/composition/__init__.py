"""工作流组合和拼接核心实现模块

提供工作流组合和拼接的核心功能实现，包括：
- 组合管理器
- 策略引擎
- 数据映射器
- 组合编排器
"""

from .manager import WorkflowCompositionManager
from .strategies import (
    SequentialStrategy,
    ParallelStrategy,
    ConditionalStrategy,
    LoopStrategy,
    CompositionStrategyEngine,
)
from .data_mapper import DataMapper
from .orchestrator import WorkflowCompositionOrchestrator

__all__ = [
    "WorkflowCompositionManager",
    "SequentialStrategy",
    "ParallelStrategy", 
    "ConditionalStrategy",
    "LoopStrategy",
    "CompositionStrategyEngine",
    "DataMapper",
    "WorkflowCompositionOrchestrator",
]