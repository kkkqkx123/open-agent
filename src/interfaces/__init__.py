"""接口层统一导出模块

这个模块提供了所有接口的统一导出，确保接口定义的集中化管理。
"""

# 工作流相关接口
from .workflow import (
    IWorkflow,
    IWorkflowBuilder,
    IWorkflowTemplate,
    IWorkflowTemplateRegistry,
    IWorkflowVisualizer
)
from .workflow.execution import (
    INodeExecutor,
    IExecutionStrategy,
    IExecutionObserver,
    IStreamingExecutor
)
from .workflow.plugins import (
    IPlugin,
    IHookPlugin,
    IStartPlugin,
    IEndPlugin,
    PluginType,
    PluginStatus,
    HookPoint,
    PluginMetadata,
    PluginContext,
    HookContext,
    HookExecutionResult
)
from .workflow.services import (
    IWorkflowManager,
    IWorkflowFactory,
    IWorkflowExecutor,
    IWorkflowOrchestrator,
    IWorkflowRegistry,
    IWorkflowBuilderService
)

# 状态相关接口
from .state import (
    IState,
    IStateManager,
    IWorkflowState,
    IStateLifecycleManager,
    IStateHistoryManager,
    IStateSnapshotManager,
    IStateSerializer,
    IStateFactory,
    IStateManager,
    StateSnapshot,
    StateHistoryEntry,
    StateConflict,
    ConflictType,
    ConflictResolutionStrategy,
    StateStatistics,
    IStorageBackend,
    IStorageAdapterFactory,
    IStorageMigration,
    IAsyncStateStorageAdapter,
    IAsyncStorageAdapterFactory,
    IAsyncStorageMigration,
    IStorageCache,
    IStorageMetrics
)

# LLM相关接口
from .llm import (
    ILLMClient,
    ILLMCallHook,
    ILLMClientFactory,
    ITaskGroupManager,
    IFallbackManager,
    IPollingPoolManager,
    IClientFactory,
    ILLMManager
)

# 工具相关接口
from .tool.base import (
    ITool,
    IToolRegistry,
    IToolFormatter,
    IToolExecutor,
    IToolManager,
    IToolFactory,
    ToolCall,
    ToolResult
)

# 工具配置相关接口
from .tool.config import (
    ToolConfig,
    NativeToolConfig,
    RestToolConfig,
    MCPToolConfig,
    ToolSetConfig
)

# 工具状态管理相关接口
from .tool.state_manager import (
    IToolStateManager,
    StateType,
    StateEntry
)

# 历史相关接口
from .history import (
    IHistoryManager,
    ICostCalculator
)

# 检查点相关接口
from .checkpoint import (
    ICheckpointStore,
    ICheckpointSerializer,
    ICheckpointManager,
    ICheckpointPolicy
)

# Repository接口
from .repository import (
    IStateRepository,
    IHistoryRepository,
    ISnapshotRepository,
    ICheckpointRepository
)

# 容器相关接口
from .container import (
    IDependencyContainer,
    ILifecycleAware,
    IServiceTracker,
    IServiceCache,
    IPerformanceMonitor,
    IDependencyAnalyzer,
    IScopeManager,
    ServiceStatus
)

# 存储相关接口
from .storage import (
    IUnifiedStorage,
    IStorageFactory,
)

# 提示词相关接口
from .prompts import (
    IPromptRegistry,
    IPromptLoader,
    IPromptInjector,
    PromptMeta,
    PromptConfig,
)

# 通用相关接口
from .common import (
    IConfigLoader,
    IConfigInheritanceHandler,
    ISerializable,
    ICacheable,
    ITimestamped,
    IStorage,
    ILogger,
    LogLevel,
    # 抽象数据类型
    AbstractSessionStatus,
    AbstractSessionData,
    AbstractThreadData,
    AbstractThreadBranchData,
    AbstractThreadSnapshotData
)

# 导出所有接口的__all__列表
__all__ = [
    # 工作流接口
    "IWorkflow",
    "IWorkflowExecutor",
    "IWorkflowBuilder",
    "IWorkflowTemplate",
    "IWorkflowTemplateRegistry",
    "IWorkflowVisualizer",
    
    # 工作流执行接口
    "INodeExecutor",
    "IExecutionStrategy",
    "IExecutionObserver",
    "IStreamingExecutor",
    
    # 工作流插件接口
    "IPlugin",
    "IHookPlugin",
    "IStartPlugin",
    "IEndPlugin",
    "PluginType",
    "PluginStatus",
    "HookPoint",
    "PluginMetadata",
    "PluginContext",
    "HookContext",
    "HookExecutionResult",
    
    # 工作流服务接口
    "IWorkflowManager",
    "IWorkflowFactory",
    "IWorkflowExecutor",
    "IWorkflowOrchestrator",
    "IWorkflowRegistry",
    "IWorkflowBuilderService",
    
    # 状态接口
    "IState",
    "IStateManager",
    "IWorkflowState",
    "IStateLifecycleManager",
    "IStateHistoryManager",
    "IStateSnapshotManager",
    "IStateSerializer",
    "IStateFactory",
    "IStateManager",
    "StateSnapshot",
    "StateHistoryEntry",
    "StateConflict",
    "ConflictType",
    "ConflictResolutionStrategy",
    "StateStatistics",
    "IStorageBackend",
    "IStorageAdapterFactory",
    "IStorageMigration",
    "IAsyncStateStorageAdapter",
    "IAsyncStorageAdapterFactory",
    "IAsyncStorageMigration",
    "IStorageCache",
    "IStorageMetrics",
    
    # LLM接口
    "ILLMClient",
    "ILLMCallHook",
    "ILLMClientFactory",
    "ITaskGroupManager",
    "IFallbackManager",
    "IPollingPoolManager",
    "IClientFactory",
    "ILLMManager",
    
    # 工具接口
    "ITool",
    "IToolRegistry",
    "IToolFormatter",
    "IToolExecutor",
    "IToolManager",
    "IToolFactory",
    "ToolCall",
    "ToolResult",
    
    # 工具配置接口
    "ToolConfig",
    "NativeToolConfig",
    "RestToolConfig",
    "MCPToolConfig",
    "ToolSetConfig",
    
    # 工具状态管理接口
    "IToolStateManager",
    "StateType",
    "StateEntry",
    
    # 历史接口
    "IHistoryManager",
    "ICostCalculator",
    
    # 检查点接口
    "ICheckpointStore",
    "ICheckpointSerializer",
    "ICheckpointManager",
    "ICheckpointPolicy",
    
    # Repository接口
    "IStateRepository",
    "IHistoryRepository",
    "ISnapshotRepository",
    "ICheckpointRepository",
    
    # 容器接口
    "IDependencyContainer",
    "ILifecycleAware",
    "IServiceTracker",
    "IServiceCache",
    "IPerformanceMonitor",
    "IDependencyAnalyzer",
    "IScopeManager",
    "ServiceStatus",
    
    # 存储接口
    "IUnifiedStorage",
    "IStorageFactory",
    
    # 提示词接口
    "IPromptRegistry",
    "IPromptLoader",
    "IPromptInjector",
    "PromptMeta",
    "PromptConfig",
    
    # 通用接口
    "IConfigLoader",
    "IConfigInheritanceHandler",
    "ISerializable",
    "ICacheable",
    "ITimestamped",
    "IStorage",
    "ILogger",
    "LogLevel",
    
    # 抽象数据类型
    "AbstractSessionStatus",
    "AbstractSessionData",
    "AbstractThreadData",
    "AbstractThreadBranchData",
    "AbstractThreadSnapshotData",
]