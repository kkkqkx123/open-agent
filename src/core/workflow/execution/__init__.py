"""工作流执行模块 - 新架构

提供工作流和节点执行的核心功能，采用基于职责的分层架构。
"""

# 核心执行层
from .core.workflow_executor import WorkflowExecutor, IWorkflowExecutor
from .core.node_executor import NodeExecutor, INodeExecutor
from .core.execution_context import (
    ExecutionContext, 
    ExecutionResult, 
    NodeResult, 
    BatchJob, 
    BatchExecutionResult,
    ExecutionStatus
)

# 执行策略层
from .strategies.strategy_base import IExecutionStrategy, BaseStrategy
from .strategies.retry_strategy import (
    RetryStrategy,
    RetryStrategyImpl,
    RetryConfig,
    RetryStrategy as RetryStrategyEnum,
    RetryAttempt,
    RetryConfigs
)
from .strategies.batch_strategy import (
    BatchStrategy,
    IBatchStrategy,
    BatchConfig,
    ExecutionMode,
    ExecutionMode as BatchExecutionMode,
    FailureStrategy
)
from .strategies.streaming_strategy import (
    StreamingStrategy,
    IStreamingStrategy,
    StreamingConfig
)
from .strategies.collaboration_strategy import (
    CollaborationStrategy,
    ICollaborationStrategy,
    CollaborationConfig
)

# 执行模式层
from .modes.mode_base import IExecutionMode, BaseMode
from .modes.sync_mode import SyncMode, ISyncMode
from .modes.async_mode import AsyncMode, IAsyncMode
from .modes.hybrid_mode import HybridMode, IHybridMode

# 执行服务层
from .services.execution_manager import (
    ExecutionManager,
    IExecutionManager,
    ExecutionManagerConfig
)
from .services.execution_monitor import (
    ExecutionMonitor,
    IExecutionMonitor,
    Metric,
    MetricType,
    Alert,
    AlertLevel,
    PerformanceReport
)
from .services.execution_scheduler import (
    ExecutionScheduler,
    IExecutionScheduler,
    ExecutionTask,
    TaskPriority,
    TaskStatus,
    SchedulerConfig
)

# 基础组件
from .base.executor_base import BaseExecutor

# 便捷函数
from .core.workflow_executor import WorkflowExecutor as DefaultWorkflowExecutor
from .core.node_executor import NodeExecutor as DefaultNodeExecutor
from .services.execution_manager import ExecutionManager as DefaultExecutionManager

__all__ = [
    # 核心执行层
    "WorkflowExecutor",
    "IWorkflowExecutor",
    "NodeExecutor", 
    "INodeExecutor",
    "ExecutionContext",
    "ExecutionResult",
    "NodeResult",
    "BatchJob",
    "BatchExecutionResult",
    "ExecutionStatus",
    
    # 执行策略层
    "IExecutionStrategy",
    "BaseStrategy",
    "RetryStrategy",
    "RetryStrategyImpl",
    "RetryConfig",
    "RetryStrategyEnum",
    "RetryAttempt",
    "RetryConfigs",
    "BatchStrategy",
    "IBatchStrategy",
    "BatchConfig",
    "ExecutionMode",
    "BatchExecutionMode",
    "FailureStrategy",
    "StreamingStrategy",
    "IStreamingStrategy",
    "StreamingConfig",
    "CollaborationStrategy",
    "ICollaborationStrategy",
    "CollaborationConfig",
    
    # 执行模式层
    "IExecutionMode",
    "BaseMode",
    "SyncMode",
    "ISyncMode",
    "AsyncMode",
    "IAsyncMode", 
    "HybridMode",
    "IHybridMode",
    
    # 执行服务层
    "ExecutionManager",
    "IExecutionManager",
    "ExecutionManagerConfig",
    "ExecutionMonitor",
    "IExecutionMonitor",
    "Metric",
    "MetricType",
    "Alert",
    "AlertLevel",
    "PerformanceReport",
    "ExecutionScheduler",
    "IExecutionScheduler",
    "ExecutionTask",
    "TaskPriority",
    "TaskStatus",
    "SchedulerConfig",
    
    # 基础组件
    "BaseExecutor",
    
    # 默认实现
    "DefaultWorkflowExecutor",
    "DefaultNodeExecutor",
    "DefaultExecutionManager",
]