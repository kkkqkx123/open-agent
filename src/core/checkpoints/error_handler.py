"""Checkpoint模块错误处理器

为Checkpoint操作提供统一的错误处理机制。
"""

from typing import Any, Dict, Optional
import logging

from src.core.common.error_management import BaseErrorHandler, ErrorCategory, ErrorSeverity
from src.core.common.exceptions.checkpoint import (
    CheckpointError,
    CheckpointNotFoundError,
    CheckpointStorageError,
    CheckpointValidationError
)

logger = logging.getLogger(__name__)


class CheckpointErrorHandler(BaseErrorHandler):
    """Checkpoint模块错误处理器"""
    
    def __init__(self):
        """初始化Checkpoint错误处理器"""
        super().__init__(ErrorCategory.STATE, ErrorSeverity.HIGH)
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误
        
        Args:
            error: 异常对象
            
        Returns:
            是否可以处理
        """
        return isinstance(error, (
            CheckpointError,
            CheckpointNotFoundError,
            CheckpointStorageError,
            CheckpointValidationError
        ))
    
    def handle(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """处理Checkpoint相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        # 添加Checkpoint特定的上下文信息
        enhanced_context = self._enhance_context(error, context)
        
        # 记录详细的错误信息
        self._log_checkpoint_error(error, enhanced_context)
        
        # 根据错误类型采取不同的处理策略
        if isinstance(error, CheckpointNotFoundError):
            self._handle_not_found_error(error, enhanced_context)
        elif isinstance(error, CheckpointStorageError):
            self._handle_storage_error(error, enhanced_context)
        elif isinstance(error, CheckpointValidationError):
            self._handle_validation_error(error, enhanced_context)
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
            "module": "checkpoints",
            "error_type": type(error).__name__,
            "error_message": str(error)
        })
        
        # 根据错误类型添加特定信息
        if isinstance(error, CheckpointNotFoundError):
            enhanced_context["checkpoint_id"] = getattr(error, 'checkpoint_id', 'unknown')
        elif isinstance(error, CheckpointStorageError):
            enhanced_context["storage_operation"] = getattr(error, 'operation', 'unknown')
        elif isinstance(error, CheckpointValidationError):
            enhanced_context["validation_field"] = getattr(error, 'field', 'unknown')
        
        return enhanced_context
    
    def _log_checkpoint_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """记录Checkpoint错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        if isinstance(error, CheckpointNotFoundError):
            logger.error(
                f"Checkpoint未找到: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, CheckpointStorageError):
            logger.critical(
                f"Checkpoint存储错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, CheckpointValidationError):
            logger.warning(
                f"Checkpoint验证错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        else:
            logger.error(
                f"Checkpoint未知错误: {error}",
                extra={"context": context},
                exc_info=True
            )
    
    def _handle_not_found_error(
        self, 
        error: CheckpointNotFoundError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Checkpoint未找到错误
        
        Args:
            error: Checkpoint未找到错误
            context: 错误上下文
        """
        # 可以在这里添加特定的恢复逻辑
        # 例如：尝试从备份恢复、创建默认checkpoint等
        logger.info(f"尝试处理Checkpoint未找到错误: {context.get('checkpoint_id')}")
        
        # 根据严重度决定是否抛出异常
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error
    
    def _handle_storage_error(
        self, 
        error: CheckpointStorageError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Checkpoint存储错误
        
        Args:
            error: Checkpoint存储错误
            context: 错误上下文
        """
        # 存储错误通常比较严重，可能需要重试或降级
        logger.critical(f"Checkpoint存储操作失败: {context.get('storage_operation')}")
        
        # 存储错误总是抛出，因为数据完整性很重要
        raise error
    
    def _handle_validation_error(
        self, 
        error: CheckpointValidationError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Checkpoint验证错误
        
        Args:
            error: Checkpoint验证错误
            context: 错误上下文
        """
        # 验证错误通常表示数据问题，需要修复数据
        logger.warning(f"Checkpoint数据验证失败: {context.get('validation_field')}")
        
        # 验证错误的严重度可能较低，可以根据具体情况决定是否抛出
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error


class CheckpointOperationHandler:
    """Checkpoint操作处理器，提供带错误处理的操作包装"""
    
    @staticmethod
    def safe_save_checkpoint(
        save_func,
        checkpoint_data: Any,
        max_retries: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全保存Checkpoint，带重试机制
        
        Args:
            save_func: 保存函数
            checkpoint_data: Checkpoint数据
            max_retries: 最大重试次数
            context: 操作上下文
            
        Returns:
            保存结果
            
        Raises:
            CheckpointStorageError: 保存失败
        """
        from src.core.common.error_management import operation_with_retry
        
        operation_context = context or {}
        operation_context.update({
            "operation": "save_checkpoint",
            "checkpoint_id": getattr(checkpoint_data, 'id', 'unknown')
        })
        
        def _save():
            return save_func(checkpoint_data)
        
        try:
            return operation_with_retry(
                _save,
                max_retries=max_retries,
                retryable_exceptions=(CheckpointStorageError,),
                context=operation_context
            )
        except Exception as e:
            from src.core.common.error_management import handle_error
            handle_error(e, operation_context)
            raise CheckpointStorageError(f"保存Checkpoint失败: {e}") from e
    
    @staticmethod
    def safe_load_checkpoint(
        load_func,
        checkpoint_id: str,
        fallback_func=None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全加载Checkpoint，带降级机制
        
        Args:
            load_func: 加载函数
            checkpoint_id: Checkpoint ID
            fallback_func: 降级函数
            context: 操作上下文
            
        Returns:
            加载的Checkpoint数据
            
        Raises:
            CheckpointNotFoundError: Checkpoint未找到且无降级策略
        """
        from src.core.common.error_management import operation_with_fallback
        
        operation_context = context or {}
        operation_context.update({
            "operation": "load_checkpoint",
            "checkpoint_id": checkpoint_id
        })
        
        def _load():
            return load_func(checkpoint_id)
        
        def _fallback():
            if fallback_func:
                return fallback_func(checkpoint_id)
            raise CheckpointNotFoundError(f"Checkpoint未找到: {checkpoint_id}")
        
        try:
            return operation_with_fallback(
                _load,
                _fallback,
                fallback_exceptions=(CheckpointNotFoundError, CheckpointStorageError),
                context=operation_context
            )
        except Exception as e:
            from src.core.common.error_management import handle_error
            handle_error(e, operation_context)
            raise