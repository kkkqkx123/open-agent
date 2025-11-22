"""
核心模块统一异常导出

为了向后兼容，所有异常都可以从此模块导入。
"""

# 核心异常
from .core import (
    CoreError,
    ServiceError,
    ValidationError,
    ConfigurationError,
    DependencyError,
)

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
)

__all__ = [
    # 核心异常
    "CoreError",
    "ServiceError",
    "ValidationError",
    "ConfigurationError",
    "DependencyError",
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
]
