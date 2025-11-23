"""
核心模块统一异常导出

为了向后兼容，所有异常都可以从此模块导入。
"""

# 工具异常
from .tool import (
    ToolError,
    ToolRegistrationError,
    ToolExecutionError,
)

# 存储异常
from .storage import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageValidationError,
    StorageNotFoundError,
    StoragePermissionError,
    StorageTimeoutError,
    StorageCapacityError,
    StorageIntegrityError,
    StorageConfigurationError,
    StorageMigrationError,
    create_storage_error,
    EXCEPTION_MAP,
)

# 提示词异常
from .prompt import (
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
)

# 历史异常
from .history import (
    HistoryError,
    TokenCalculationError,
    CostCalculationError,
    StatisticsError,
    RecordNotFoundError,
    QuotaExceededError,
)

# Checkpoint异常
from .checkpoint import (
    CheckpointError,
    CheckpointNotFoundError,
    CheckpointStorageError,
    CheckpointValidationError,
)

__all__ = [
    # 工具异常
    "ToolError",
    "ToolRegistrationError",
    "ToolExecutionError",
    # 存储异常
    "StorageError",
    "StorageConnectionError",
    "StorageTransactionError",
    "StorageValidationError",
    "StorageNotFoundError",
    "StoragePermissionError",
    "StorageTimeoutError",
    "StorageCapacityError",
    "StorageIntegrityError",
    "StorageConfigurationError",
    "StorageMigrationError",
    "create_storage_error",
    "EXCEPTION_MAP",
    # 提示词异常
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
    # 历史异常
    "HistoryError",
    "TokenCalculationError",
    "CostCalculationError",
    "StatisticsError",
    "RecordNotFoundError",
    "QuotaExceededError",
    # Checkpoint异常
    "CheckpointError",
    "CheckpointNotFoundError",
    "CheckpointStorageError",
    "CheckpointValidationError",
]
