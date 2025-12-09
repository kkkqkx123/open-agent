"""接口层统一导出模块

这个模块提供了所有接口的统一导出，确保接口定义的集中化管理。
"""

# 缓存相关接口
from .cache import (
    ICacheManager,
    ICacheAdapter,
    ICacheProvider,
    ICacheKeyGenerator,
    ICacheEntry,
    ICacheStatistics,
    ICacheFactory
)

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
    IStartPlugin,
    IEndPlugin,
    PluginType,
    PluginStatus,
    PluginMetadata,
    PluginContext,
    PluginExecutionResult
)
from .workflow.services import (
    IWorkflowManager,
    IWorkflowFactory,
    IWorkflowExecutor,
    IWorkflowRegistryCoordinator,
    IWorkflowBuilderService
)
from .workflow.core import IWorkflowRegistry

# 状态相关接口（仅导出接口，不导出具体实现）
from .state import (
    IState,
    IStateManager,
    IWorkflowState,
    IStateLifecycleManager,
    IStateHistoryManager,
    IStateSnapshotManager,
    IStateSerializer,
    IStateFactory,
    IStorageBackend,
    IStorageAdapterFactory,
    IStorageMigration,
    IStorageCache,
    IStorageMetrics
)

# 注意：具体实现（StateSnapshot等）应该从src.core.state导入，而不是从接口层

# LLM相关接口
from .llm import (
    ILLMClient,
    ILLMCallHook,
    ILLMClientFactory,
    ITaskGroupManager,
    IFallbackManager,
    IPollingPoolManager,
    IClientFactory,
    ILLMManager,
    IProviderConverter
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

# 检查点相关接口（已合并到threads模块）
from .threads.checkpoint import (
    CheckpointError,
    CheckpointValidationError,
    CheckpointNotFoundError,
    CheckpointStorageError,
    CheckpointConflictError,
    CheckpointTimeoutError,
    CheckpointQuotaExceededError,
    CheckpointCorruptionError,
    CheckpointVersionError,
    CheckpointConfigurationError,
    CheckpointHookError,
    CheckpointCacheError,
    CheckpointResourceError,
)

# Thread检查点相关接口
from .threads.checkpoint import (
    IThreadCheckpointStorage,
    IThreadCheckpointManager,
    IThreadCheckpointSerializer,
    IThreadCheckpointPolicy
)

# Repository接口
from .repository import (
    IStateRepository,
    IHistoryRepository,
    ISnapshotRepository,
    ICheckpointRepository,
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryOperationError,
    RepositoryConnectionError,
    RepositoryTransactionError,
    RepositoryValidationError,
    RepositoryTimeoutError,
)

# 容器相关接口
from .container import (
    IDependencyContainer,
    ILifecycleAware,
    ILifecycleManager,
    IServiceRegistry,
    IServiceResolver,
    IServiceTracker,
    IPerformanceMonitor,
    IDependencyAnalyzer,
    IServiceCache,
    IScopeManager,
    ServiceRegistration,
    DependencyChain,
    ServiceStatus
)

# 存储相关接口
from .storage import (
    IStorage,
    IStorageFactory,
    IStorageProvider,
    ISessionStorage,
    IThreadStorage,
    IStorageMonitoring,
    IStorageMetrics,
    IStorageAlerting,
    IStorageMigration,
    ISchemaMigration,
    IDataTransformer,
    IMigrationPlanner,
    IStorageTransaction,
    IDistributedTransaction,
    ITransactionRecovery,
    ITransactionManager,
    IConsistencyManager,
    # 异常类型
    StorageError,
    StorageConnectionError,
    StorageOperationError,
    StorageValidationError,
    StorageNotFoundError,
    StorageTimeoutError,
    StorageCapacityError,
    StorageIntegrityError,
    StorageConfigurationError,
    StorageMigrationError,
    StorageTransactionError,
    StoragePermissionError,
    StorageSerializationError,
    StorageCompressionError,
    StorageEncryptionError,
    StorageIndexError,
    StorageBackupError,
    StorageLockError,
    StorageQueryError,
    StorageHealthError,
    StorageConsistencyError,
    StorageDistributedTransactionError
)

# 导入提示词相关接口
from .prompts import (
    IPromptLoader,
    IPromptInjector,
    PromptMeta,
    PromptConfig,
    IPromptRegistry,
    IPromptCache,
    IPromptType,
    IPromptReferenceResolver,
)
# 日志相关接口
from .logger import (
    ILogger,
    IBaseHandler,
    ILogRedactor,
    ILoggerFactory,
    LogLevel,
)
from .common_domain import (
    ISerializable,
    ITimestamped,
    # 抽象数据类型
    AbstractSessionStatus,
    AbstractSessionData,
    # 通用数据传输对象
    ValidationResult,
    BaseContext,
    ExecutionContext,
    WorkflowExecutionContext
)
from .common_types import (
    BaseStatus,
    BasePriority,
    BaseNumericPriority,
    OperationResult,
    PagedResult
)

# 消息相关接口
from .messages import (
    IBaseMessage,
    IMessageConverter,
    IMessageFactory,
    IMessageSerializer,
    IMessageValidator
)

# UI消息相关接口
from .ui import (
    IUIMessage,
    IUIMessageRenderer,
    IUIMessageAdapter,
    IUIMessageManager,
    IUIMessageController
)

# 配置相关接口
from .configuration import (
    ConfigValidationResult,
    ValidationSeverity,
    IConfigValidator,
    IConfigManager
)

# 文件系统相关接口
from .filesystem import (
    IFileWatcher,
    IFileWatcherFactory,
    FileWatcherError,
    FileWatchPathError,
    FileWatchCallbackError,
)

# 导出所有接口的__all__列表
__all__ = [
    # 缓存接口
    "ICacheManager",
    "ICacheAdapter",
    "ICacheProvider",
    "ICacheKeyGenerator",
    "ICacheEntry",
    "ICacheStatistics",
    "ICacheFactory",
    
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
    "IStartPlugin",
    "IEndPlugin",
    "PluginType",
    "PluginStatus",
    "PluginMetadata",
    "PluginContext",
    "PluginExecutionResult",
    
    # 工作流服务接口
    "IWorkflowManager",
    "IWorkflowFactory",
    "IWorkflowExecutor",
    "IWorkflowRegistry",
    "IWorkflowRegistryCoordinator",
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
    "IStorageBackend",
    "IStorageAdapterFactory",
    "IStorageMigration",
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
    "IProviderConverter",
    
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
    
    # 检查点接口（已合并到threads模块）
    "CheckpointError",
    "CheckpointValidationError",
    "CheckpointNotFoundError",
    "CheckpointStorageError",
    "CheckpointConflictError",
    "CheckpointTimeoutError",
    "CheckpointQuotaExceededError",
    "CheckpointCorruptionError",
    "CheckpointVersionError",
    "CheckpointConfigurationError",
    "CheckpointHookError",
    "CheckpointCacheError",
    "CheckpointResourceError",
    
    # Thread检查点接口
    "IThreadCheckpointStorage",
    "IThreadCheckpointManager",
    "IThreadCheckpointSerializer",
    "IThreadCheckpointPolicy",
    
    # Repository接口
    "IStateRepository",
    "IHistoryRepository",
    "ISnapshotRepository",
    "ICheckpointRepository",
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
    "RepositoryValidationError",
    "RepositoryTimeoutError",
    
    # 容器接口
    "IDependencyContainer",
    "ILifecycleAware",
    "ILifecycleManager",
    "IServiceRegistry",
    "IServiceResolver",
    "IServiceTracker",
    "IPerformanceMonitor",
    "IDependencyAnalyzer",
    "IServiceCache",
    "IScopeManager",
    "ServiceRegistration",
    "DependencyChain",
    "ServiceStatus",
    
    # 存储接口
    "IStorage",
    "IStorageFactory",
    "IStorageProvider",
    "ISessionStorage",
    "IThreadStorage",
    "IStorageMonitoring",
    "IStorageMetrics",
    "IStorageAlerting",
    "IStorageMigration",
    "ISchemaMigration",
    "IDataTransformer",
    "IMigrationPlanner",
    "IStorageTransaction",
    "IDistributedTransaction",
    "ITransactionRecovery",
    "ITransactionManager",
    "IConsistencyManager",
    
    # 存储异常类型
    "StorageError",
    "StorageConnectionError",
    "StorageOperationError",
    "StorageValidationError",
    "StorageNotFoundError",
    "StorageTimeoutError",
    "StorageCapacityError",
    "StorageIntegrityError",
    "StorageConfigurationError",
    "StorageMigrationError",
    "StorageTransactionError",
    "StoragePermissionError",
    "StorageSerializationError",
    "StorageCompressionError",
    "StorageEncryptionError",
    "StorageIndexError",
    "StorageBackupError",
    "StorageLockError",
    "StorageQueryError",
    "StorageHealthError",
    "StorageConsistencyError",
    "StorageDistributedTransactionError",
    
    # 提示词接口
    "IPromptRegistry",
    "IPromptLoader",
    "IPromptInjector",
    "IPromptCache",
    "IPromptType",
    "IPromptReferenceResolver",
    "PromptMeta",
    "PromptConfig",
    
    # 通用接口
    "ISerializable",
    "ITimestamped",
    "IStorage",
    "ILogger",
    "IBaseHandler",
    "ILogRedactor",
    "ILoggerFactory",
    "LogLevel",
    
    # 通用数据传输对象
    "ValidationResult",
    "BaseContext",
    "ExecutionContext",
    "WorkflowExecutionContext",
    "OperationResult",
    "PagedResult",
    
    # 通用枚举类型
    "BaseStatus",
    "BasePriority",
    "BaseNumericPriority",
    
    # 抽象数据类型
    "AbstractSessionStatus",
    "AbstractSessionData",
    
    # 消息接口
    "IBaseMessage",
    "IMessageConverter",
    "IMessageFactory",
    "IMessageSerializer",
    "IMessageValidator",
    
    # UI消息接口
    "IUIMessage",
    "IUIMessageRenderer",
    "IUIMessageAdapter",
    "IUIMessageManager",
    "IUIMessageController",
    
    # 配置接口
    "ConfigValidationResult",
    "ValidationSeverity",
    "IConfigValidator",
    "IConfigManager",
    
    # 文件系统接口
    "IFileWatcher",
    "IFileWatcherFactory",
    "FileWatcherError",
    "FileWatchPathError",
    "FileWatchCallbackError",
]