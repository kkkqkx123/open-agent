"""
核心模块统一异常导出

为了向后兼容，所有异常都可以从此模块导入。
"""

# 导入pydantic的ValidationError
from typing import Optional, Dict, Any
from pydantic import ValidationError

# 导入配置异常
from .config import ConfigError

# 基础异常
class CoreError(Exception):
    """核心模块基础异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ServiceError(CoreError):
    """服务模块基础异常"""
    pass


class ConfigurationError(ConfigError):
    """配置错误异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        super().__init__(message, config_path, details)


class DependencyError(CoreError):
    """依赖错误异常"""
    pass


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
    PromptReferenceError,
    PromptCircularReferenceError,
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
    "PromptReferenceError",
    "PromptCircularReferenceError",
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
    # Repository异常
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
    "RepositoryValidationError",
    "RepositoryTimeoutError",
]