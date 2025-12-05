"""
核心模块统一异常导出

为了向后兼容，所有异常都可以从此模块导入。
"""

# 导入pydantic的ValidationError
from typing import Optional, Dict, Any
from pydantic import ValidationError

# 基础异常
class CoreError(Exception):
    """核心模块基础异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ServiceError(CoreError):
    """服务模块基础异常"""
    pass


class DependencyError(CoreError):
    """依赖错误异常"""
    pass


# 从接口层导入配置异常
from src.interfaces.configuration import (
    ConfigError,
    ConfigurationValidationError,
    ConfigurationLoadError,
    ConfigurationEnvironmentError,
    ConfigurationParseError,
    ConfigurationMergeError,
    ConfigurationSchemaError,
    ConfigurationInheritanceError,
)

# 为了向后兼容，保留ConfigurationError别名
class ConfigurationError(ConfigError):
    """配置错误异常（向后兼容）"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        super().__init__(message, config_path, details)


# 从接口层导入Workflow异常
from src.interfaces.workflow.exceptions import (
    WorkflowError,
    WorkflowValidationError,
    WorkflowExecutionError,
    WorkflowStepError,
    WorkflowTransitionError,
    WorkflowRuleError,
    WorkflowTimeoutError,
    WorkflowStateError,
    WorkflowConfigError,
    WorkflowDependencyError,
    WorkflowPermissionError,
    WorkflowConcurrencyError,
    WorkflowResourceError,
    WorkflowIntegrationError,
    WorkflowTemplateError,
    WorkflowVersionError,
    WORKFLOW_EXCEPTION_MAP,
    create_workflow_exception,
    handle_workflow_exception,
)

# 从接口层导入Tool异常
from src.interfaces.tool.exceptions import (
    ToolError,
    ToolRegistrationError,
    ToolExecutionError,
    ToolValidationError,
    ToolNotFoundError,
    ToolConfigurationError,
    ToolTimeoutError,
    ToolPermissionError,
    ToolDependencyError,
    ToolResourceError,
)

# 从接口层导入LLM异常
from src.interfaces.llm.exceptions import (
    LLMError,
    LLMClientCreationError,
    UnsupportedModelTypeError,
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
    LLMConfigurationError,
    LLMFallbackError,
    # LLM Wrapper异常
    LLMWrapperError,
    TaskGroupWrapperError,
    PollingPoolWrapperError,
    WrapperFactoryError,
    WrapperConfigError,
    WrapperExecutionError,
)

# 从接口层导入State异常
from src.interfaces.state.exceptions import (
    StateError,
    StateValidationError,
    StateNotFoundError,
    StateTimeoutError,
    StateCapacityError,
    StateTransitionError,
    StateConsistencyError,
    StateSerializationError,
    StateDeserializationError,
    StateLockError,
    StateVersionError,
)

# 从接口层导入History异常
from src.interfaces.history.exceptions import (
    HistoryError,
    TokenCalculationError,
    CostCalculationError,
    StatisticsError,
    RecordNotFoundError,
    QuotaExceededError,
    HistoryQueryError,
    HistoryStorageError,
    HistoryValidationError,
)

# 从接口层导入Checkpoint异常
from src.interfaces.checkpoint import (
    CheckpointError,
    CheckpointNotFoundError,
    CheckpointStorageError,
    CheckpointValidationError,
    CheckpointSerializationError,
    CheckpointTimeoutError,
    CheckpointVersionError,
)

# 从接口层导入Prompt异常
from src.interfaces.prompts.exceptions import (
    PromptError,
    PromptRegistryError,
    PromptLoadError,
    PromptInjectionError,
    PromptConfigurationError,
    PromptNotFoundError,
    PromptValidationError,
    PromptCacheError,
    PromptTypeNotFoundError,
    PromptTypeRegistrationError,
    PromptReferenceError,
    PromptCircularReferenceError,
    PromptTemplateError,
    PromptRenderingError,
)

# 从接口层导入Session异常
from src.interfaces.sessions.exceptions import (
    SessionThreadException,
    ThreadCreationError,
    ThreadRemovalError,
    ThreadTransferError,
    SessionThreadInconsistencyError,
    AssociationNotFoundError,
    DuplicateThreadNameError,
    ThreadNotFoundError,
    SessionNotFoundError,
    TransactionRollbackError,
    WorkflowExecutionError,
    SynchronizationError,
    ConfigurationValidationError as SessionConfigurationValidationError,
    SessionTimeoutError,
    SessionCapacityError,
    SessionPermissionError,
)

# Repository异常 - 从接口层导入以实现向后兼容
from src.interfaces.repository import (
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryOperationError,
    RepositoryConnectionError,
    RepositoryTransactionError,
    RepositoryValidationError,
    RepositoryTimeoutError,
)

__all__ = [
    # 基础异常
    "CoreError",
    "ServiceError",
    "ValidationError",
    "ConfigurationError",
    "DependencyError",
    # 配置异常
    "ConfigError",
    "ConfigurationValidationError",
    "ConfigurationLoadError",
    "ConfigurationEnvironmentError",
    "ConfigurationParseError",
    "ConfigurationMergeError",
    "ConfigurationSchemaError",
    "ConfigurationInheritanceError",
    # Workflow异常
    "WorkflowError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    "WorkflowStepError",
    "WorkflowTransitionError",
    "WorkflowRuleError",
    "WorkflowTimeoutError",
    "WorkflowStateError",
    "WorkflowConfigError",
    "WorkflowDependencyError",
    "WorkflowPermissionError",
    "WorkflowConcurrencyError",
    "WorkflowResourceError",
    "WorkflowIntegrationError",
    "WorkflowTemplateError",
    "WorkflowVersionError",
    "WORKFLOW_EXCEPTION_MAP",
    "create_workflow_exception",
    "handle_workflow_exception",
    # Tool异常
    "ToolError",
    "ToolRegistrationError",
    "ToolExecutionError",
    "ToolValidationError",
    "ToolNotFoundError",
    "ToolConfigurationError",
    "ToolTimeoutError",
    "ToolPermissionError",
    "ToolDependencyError",
    "ToolResourceError",
    # LLM异常
    "LLMError",
    "LLMClientCreationError",
    "UnsupportedModelTypeError",
    "LLMCallError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    "LLMModelNotFoundError",
    "LLMTokenLimitError",
    "LLMContentFilterError",
    "LLMServiceUnavailableError",
    "LLMInvalidRequestError",
    "LLMConfigurationError",
    "LLMFallbackError",
    # LLM Wrapper异常
    "LLMWrapperError",
    "TaskGroupWrapperError",
    "PollingPoolWrapperError",
    "WrapperFactoryError",
    "WrapperConfigError",
    "WrapperExecutionError",
    # State异常
    "StateError",
    "StateValidationError",
    "StateNotFoundError",
    "StateTimeoutError",
    "StateCapacityError",
    "StateTransitionError",
    "StateConsistencyError",
    "StateSerializationError",
    "StateDeserializationError",
    "StateLockError",
    "StateVersionError",
    # History异常
    "HistoryError",
    "TokenCalculationError",
    "CostCalculationError",
    "StatisticsError",
    "RecordNotFoundError",
    "QuotaExceededError",
    "HistoryQueryError",
    "HistoryStorageError",
    "HistoryValidationError",
    # Checkpoint异常
    "CheckpointError",
    "CheckpointNotFoundError",
    "CheckpointStorageError",
    "CheckpointValidationError",
    "CheckpointSerializationError",
    "CheckpointTimeoutError",
    "CheckpointVersionError",
    # Prompt异常
    "PromptError",
    "PromptRegistryError",
    "PromptLoadError",
    "PromptInjectionError",
    "PromptConfigurationError",
    "PromptNotFoundError",
    "PromptValidationError",
    "PromptCacheError",
    "PromptTypeNotFoundError",
    "PromptTypeRegistrationError",
    "PromptReferenceError",
    "PromptCircularReferenceError",
    "PromptTemplateError",
    "PromptRenderingError",
    # Session异常
    "SessionThreadException",
    "ThreadCreationError",
    "ThreadRemovalError",
    "ThreadTransferError",
    "SessionThreadInconsistencyError",
    "AssociationNotFoundError",
    "DuplicateThreadNameError",
    "ThreadNotFoundError",
    "SessionNotFoundError",
    "TransactionRollbackError",
    "WorkflowExecutionError",
    "SynchronizationError",
    "SessionConfigurationValidationError",
    "SessionTimeoutError",
    "SessionCapacityError",
    "SessionPermissionError",
    # Repository异常（从接口层导入）
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
    "RepositoryValidationError",
    "RepositoryTimeoutError",
]