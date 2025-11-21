"""工作流执行模块 - 新架构

提供工作流和节点执行的核心功能，采用基于职责的分层架构。
"""

# 核心执行层
from .core import (
    WorkflowExecutor,
    IWorkflowExecutor,
    NodeExecutor,
    INodeExecutor,
    ExecutionContext,
    ExecutionResult,
    NodeResult,
    BatchJob,
    BatchExecutionResult,
    ExecutionStatus
)

# 执行策略层
from .strategies import (
    IExecutionStrategy,
    BaseStrategy,
    RetryStrategy,
    IRetryStrategy,
    RetryConfig,
    RetryStrategy as RetryStrategyEnum,
    RetryAttempt,
    RetryConfigs,
    BatchStrategy,
    IBatchStrategy,
    BatchConfig,
    ExecutionMode as BatchExecutionMode,
    FailureStrategy,
    StreamingStrategy,
    IStreamingStrategy,
    StreamingConfig,
    CollaborationStrategy,
    ICollaborationStrategy,
    CollaborationConfig
)

# 执行模式层
from .modes import (
    IExecutionMode,
    BaseMode,
    SyncMode,
    ISyncMode,
    AsyncMode,
    IAsyncMode,
    HybridMode,
    IHybridMode
)

# 执行服务层
from .services import (
    ExecutionManager,
    IExecutionManager,
    ExecutionManagerConfig,
    ExecutionMonitor,
    IExecutionMonitor,
    Metric,
    MetricType,
    Alert,
    AlertLevel,
    PerformanceReport,
    ExecutionScheduler,
    IExecutionScheduler,
    ExecutionTask,
    TaskPriority,
    TaskStatus,
    SchedulerConfig
)

# 基础组件（保持向后兼容）
from .base.executor_base import BaseExecutor as LegacyBaseExecutor

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
    "IRetryStrategy", 
    "RetryConfig",
    "RetryStrategyEnum",
    "RetryAttempt",
    "RetryConfigs",
    "BatchStrategy",
    "IBatchStrategy",
    "BatchConfig",
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
    
    # 向后兼容
    "LegacyBaseExecutor",
    
    # 默认实现
    "DefaultWorkflowExecutor",
    "DefaultNodeExecutor",
    "DefaultExecutionManager",
]