"""
核心通用模块

提供核心模块使用的通用工具、异常和类型定义。
"""

from .exceptions import (
    CoreError,
    ServiceError,
    ValidationError,
    ConfigurationError,
    DependencyError,
    ToolError,
    ToolRegistrationError,
    ToolExecutionError,
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
    PromptError,
    PromptRegistryError,
    PromptLoadError,
    PromptInjectionError,
    PromptConfigurationError,
    PromptNotFoundError,
    EXCEPTION_MAP,
    create_storage_error,
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
    
    # 提示词异常
    "PromptError",
    "PromptRegistryError",
    "PromptLoadError",
    "PromptInjectionError",
    "PromptConfigurationError",
    "PromptNotFoundError",
    
    # 工具函数
    "EXCEPTION_MAP",
    "create_storage_error",
]
