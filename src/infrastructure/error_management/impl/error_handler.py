"""Storage模块错误处理器

为存储操作提供统一的错误处理机制。
"""

from typing import Any, Dict, Optional, List
from src.interfaces.dependency_injection import get_logger
import time

from src.infrastructure.error_management import BaseErrorHandler, ErrorCategory, ErrorSeverity
from src.infrastructure.exceptions.storage import (
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
    StorageSerializationError,
    StorageCompressionError,
    StorageEncryptionError,
    StorageIndexError,
    StorageBackupError,
    StorageLockError,
    StorageQueryError,
    StorageHealthError
)

logger = get_logger(__name__)


class StorageErrorHandler(BaseErrorHandler):
    """Storage模块错误处理器"""
    
    def __init__(self):
        """初始化Storage错误处理器"""
        super().__init__(ErrorCategory.STORAGE, ErrorSeverity.CRITICAL)
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误
        
        Args:
            error: 异常对象
            
        Returns:
            是否可以处理
        """
        return isinstance(error, (
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
            StorageSerializationError,
            StorageCompressionError,
            StorageEncryptionError,
            StorageIndexError,
            StorageBackupError,
            StorageLockError,
            StorageQueryError,
            StorageHealthError
        ))
    
    def handle(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """处理Storage相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        # 添加Storage特定的上下文信息
        enhanced_context = self._enhance_context(error, context)
        
        # 记录详细的错误信息
        self._log_storage_error(error, enhanced_context)
        
        # 根据错误类型采取不同的处理策略
        if isinstance(error, StorageConnectionError):
            self._handle_connection_error(error, enhanced_context)
        elif isinstance(error, StorageTransactionError):
            self._handle_transaction_error(error, enhanced_context)
        elif isinstance(error, StorageValidationError):
            self._handle_validation_error(error, enhanced_context)
        elif isinstance(error, StorageTimeoutError):
            self._handle_timeout_error(error, enhanced_context)
        elif isinstance(error, StorageCapacityError):
            self._handle_capacity_error(error, enhanced_context)
        elif isinstance(error, StorageIntegrityError):
            self._handle_integrity_error(error, enhanced_context)
        else:
            # 调用基类处理
            super().handle(error, enhanced_context)
    
    def _enhance_context(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """增强错误上下文信息
        
        Args:
            error: 异常对象
            context: 原始上下文
            
        Returns:
            增强后的上下文
        """
        enhanced_context = context or {}
        enhanced_context.update({
            "module": "storage",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time()
        })
        
        # 根据错误类型添加特定信息
        if isinstance(error, StorageConnectionError):
            enhanced_context["connection_string"] = getattr(error, 'connection_string', 'unknown')
        elif isinstance(error, StorageTransactionError):
            enhanced_context["transaction_id"] = getattr(error, 'transaction_id', 'unknown')
        elif isinstance(error, StorageValidationError):
            enhanced_context["validation_field"] = getattr(error, 'field', 'unknown')
        elif isinstance(error, StorageTimeoutError):
            enhanced_context["timeout_duration"] = getattr(error, 'timeout', 'unknown')
        elif isinstance(error, StorageCapacityError):
            enhanced_context["capacity_limit"] = getattr(error, 'limit', 'unknown')
        
        return enhanced_context
    
    def _log_storage_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """记录Storage错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        if isinstance(error, (StorageConnectionError, StorageIntegrityError)):
            logger.critical(
                f"存储严重错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (StorageTransactionError, StorageCapacityError)):
            logger.error(
                f"存储操作错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (StorageValidationError, StorageTimeoutError)):
            logger.warning(
                f"存储警告: {error}",
                extra={"context": context},
                exc_info=True
            )
        else:
            logger.error(
                f"存储未知错误: {error}",
                extra={"context": context},
                exc_info=True
            )
    
    def _handle_connection_error(
        self, 
        error: StorageConnectionError, 
        context: Dict[str, Any]
    ) -> None:
        """处理存储连接错误
        
        Args:
            error: 存储连接错误
            context: 错误上下文
        """
        logger.critical(f"存储连接失败: {context.get('connection_string')}")
        
        # 连接错误通常需要重试
        # 这里可以添加重连逻辑
        self._schedule_connection_retry(context)
        
        # 连接错误总是抛出，因为无法继续操作
        raise error
    
    def _handle_transaction_error(
        self, 
        error: StorageTransactionError, 
        context: Dict[str, Any]
    ) -> None:
        """处理存储事务错误
        
        Args:
            error: 存储事务错误
            context: 错误上下文
        """
        logger.error(f"存储事务失败: {context.get('transaction_id')}")
        
        # 事务错误需要回滚
        self._rollback_transaction(context)
        
        # 事务错误总是抛出，因为数据一致性很重要
        raise error
    
    def _handle_validation_error(
        self, 
        error: StorageValidationError, 
        context: Dict[str, Any]
    ) -> None:
        """处理存储验证错误
        
        Args:
            error: 存储验证错误
            context: 错误上下文
        """
        logger.warning(f"存储数据验证失败: {context.get('validation_field')}")
        
        # 验证错误可能需要修复数据
        self._attempt_data_repair(context)
        
        # 验证错误的严重度可能较低，可以根据具体情况决定是否抛出
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error
    
    def _handle_timeout_error(
        self, 
        error: StorageTimeoutError, 
        context: Dict[str, Any]
    ) -> None:
        """处理存储超时错误
        
        Args:
            error: 存储超时错误
            context: 错误上下文
        """
        logger.warning(f"存储操作超时: {context.get('timeout_duration')}")
        
        # 超时错误可能需要重试或优化查询
        self._optimize_operation(context)
        
        # 超时错误通常可以重试
        raise error
    
    def _handle_capacity_error(
        self, 
        error: StorageCapacityError, 
        context: Dict[str, Any]
    ) -> None:
        """处理存储容量错误
        
        Args:
            error: 存储容量错误
            context: 错误上下文
        """
        logger.error(f"存储容量不足: {context.get('capacity_limit')}")
        
        # 容量错误需要清理空间
        self._cleanup_storage(context)
        
        # 容量错误总是抛出
        raise error
    
    def _handle_integrity_error(
        self, 
        error: StorageIntegrityError, 
        context: Dict[str, Any]
    ) -> None:
        """处理存储完整性错误
        
        Args:
            error: 存储完整性错误
            context: 错误上下文
        """
        logger.critical(f"存储数据完整性检查失败")
        
        # 完整性错误需要立即修复
        self._repair_data_integrity(context)
        
        # 完整性错误总是抛出
        raise error
    
    def _schedule_connection_retry(self, context: Dict[str, Any]) -> None:
        """安排连接重试
        
        Args:
            context: 错误上下文
        """
        logger.info("安排存储连接重试")
        # 这里可以实现具体的重试逻辑
    
    def _rollback_transaction(self, context: Dict[str, Any]) -> None:
        """回滚事务
        
        Args:
            context: 错误上下文
        """
        logger.info("回滚存储事务")
        # 这里可以实现具体的事务回滚逻辑
    
    def _attempt_data_repair(self, context: Dict[str, Any]) -> None:
        """尝试修复数据
        
        Args:
            context: 错误上下文
        """
        logger.info("尝试修复存储数据")
        # 这里可以实现具体的数据修复逻辑
    
    def _optimize_operation(self, context: Dict[str, Any]) -> None:
        """优化操作
        
        Args:
            context: 错误上下文
        """
        logger.info("优化存储操作")
        # 这里可以实现具体的操作优化逻辑
    
    def _cleanup_storage(self, context: Dict[str, Any]) -> None:
        """清理存储空间
        
        Args:
            context: 错误上下文
        """
        logger.info("清理存储空间")
        # 这里可以实现具体的存储清理逻辑
    
    def _repair_data_integrity(self, context: Dict[str, Any]) -> None:
        """修复数据完整性
        
        Args:
            context: 错误上下文
        """
        logger.critical("修复存储数据完整性")
        # 这里可以实现具体的数据完整性修复逻辑


class StorageOperationHandler:
    """存储操作处理器，提供带错误处理的操作包装"""
    
    @staticmethod
    def safe_storage_operation(
        operation_func,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全存储操作，带重试机制
        
        Args:
            operation_func: 操作函数
            max_retries: 最大重试次数
            backoff_factor: 退避因子
            context: 操作上下文
            
        Returns:
            操作结果
            
        Raises:
            StorageError: 存储操作失败
        """
        from src.infrastructure.error_management import operation_with_retry
        
        operation_context = context or {}
        operation_context.update({
            "operation": "storage_operation",
            "max_retries": max_retries
        })
        
        # 定义可重试的异常类型
        retryable_exceptions = (
            StorageConnectionError,
            StorageTimeoutError,
            StorageLockError
        )
        
        try:
            return operation_with_retry(
                operation_func,
                max_retries=max_retries,
                retryable_exceptions=retryable_exceptions,
                context=operation_context
            )
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise StorageError(f"存储操作失败: {e}") from e
    
    @staticmethod
    def safe_batch_operation(
        operations: List[Any],
        batch_size: int = 100,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """安全批处理操作
        
        Args:
            operations: 操作列表
            batch_size: 批次大小
            context: 操作上下文
            
        Returns:
            操作结果列表
            
        Raises:
            StorageTransactionError: 批处理失败
        """
        from src.infrastructure.error_management import safe_execution
        
        operation_context = context or {}
        operation_context.update({
            "operation": "batch_operation",
            "batch_size": batch_size,
            "total_operations": len(operations)
        })
        
        results = []
        
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            batch_context = operation_context.copy()
            batch_context["batch_number"] = i // batch_size + 1
            
            def _process_batch():
                batch_results = []
                for operation in batch:
                    result = operation()
                    batch_results.append(result)
                return batch_results
            
            try:
                batch_results = safe_execution(
                    _process_batch,
                    context=batch_context
                )
                if batch_results is not None:
                    results.extend(batch_results)
            except Exception as e:
                from src.infrastructure.error_management import handle_error
                handle_error(e, batch_context)
                raise StorageTransactionError(f"批处理操作失败: {e}") from e
        
        return results
    
    @staticmethod
    def safe_transaction_operation(
        transaction_func,
        rollback_func=None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全事务操作
        
        Args:
            transaction_func: 事务函数
            rollback_func: 回滚函数
            context: 操作上下文
            
        Returns:
            操作结果
            
        Raises:
            StorageTransactionError: 事务失败
        """
        operation_context = context or {}
        operation_context.update({
            "operation": "transaction_operation"
        })
        
        try:
            return transaction_func()
        except Exception as e:
            # 执行回滚
            if rollback_func:
                try:
                    rollback_func()
                    logger.info("事务回滚成功")
                except Exception as rollback_error:
                    logger.error(f"事务回滚失败: {rollback_error}")
                    from src.infrastructure.error_management import handle_error
                    handle_error(rollback_error, operation_context)
            
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise StorageTransactionError(f"事务操作失败: {e}") from e