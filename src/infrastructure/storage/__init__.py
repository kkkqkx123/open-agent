"""存储基础设施模块

提供存储系统的基础设施组件，包括错误处理、指标收集、事务管理和健康检查。
"""

from .base_storage import BaseStorage
from .error_handler import StorageErrorHandler, StorageErrorClassifier
from .metrics import StorageMetrics, MetricsCollector, OperationMetrics, TimeSeriesPoint
from .transaction import (
    TransactionManager,
    Transaction,
    TransactionOperation,
    TransactionContext,
    TransactionState,
    OperationType
)
from .health_checker import (
    HealthChecker,
    HealthStatus,
    HealthCheckResult,
    HealthThresholds,
    StorageHealthChecker
)

__all__ = [
    # 基础存储
    "BaseStorage",
    
    # 错误处理
    "StorageErrorHandler",
    "StorageErrorClassifier",
    
    # 指标收集
    "StorageMetrics",
    "MetricsCollector",
    "OperationMetrics",
    "TimeSeriesPoint",
    
    # 事务管理
    "TransactionManager",
    "Transaction",
    "TransactionOperation",
    "TransactionContext",
    "TransactionState",
    "OperationType",
    
    # 健康检查
    "HealthChecker",
    "HealthStatus",
    "HealthCheckResult",
    "HealthThresholds",
    "StorageHealthChecker",
]