"""Thread检查点领域异常

定义Thread检查点相关的领域异常类。
"""

from typing import Optional, Dict, Any


class CheckpointDomainError(Exception):
    """检查点领域错误基类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            context: 错误上下文
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            异常信息字典
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class CheckpointNotFoundError(CheckpointDomainError):
    """检查点未找到错误"""
    
    def __init__(self, checkpoint_id: str, thread_id: Optional[str] = None):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            thread_id: 线程ID
        """
        message = f"Checkpoint {checkpoint_id} not found"
        if thread_id:
            message += f" in thread {thread_id}"
        
        super().__init__(
            message=message,
            error_code="CHECKPOINT_NOT_FOUND",
            context={
                "checkpoint_id": checkpoint_id,
                "thread_id": thread_id
            }
        )


class CheckpointValidationError(CheckpointDomainError):
    """检查点验证错误"""
    
    def __init__(self, message: str, checkpoint_id: Optional[str] = None):
        """初始化异常
        
        Args:
            message: 错误消息
            checkpoint_id: 检查点ID
        """
        super().__init__(
            message=message,
            error_code="CHECKPOINT_VALIDATION_ERROR",
            context={
                "checkpoint_id": checkpoint_id
            }
        )


class CheckpointRestoreError(CheckpointDomainError):
    """检查点恢复错误"""
    
    def __init__(self, checkpoint_id: str, reason: str):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            reason: 恢复失败原因
        """
        super().__init__(
            message=f"Failed to restore checkpoint {checkpoint_id}: {reason}",
            error_code="CHECKPOINT_RESTORE_ERROR",
            context={
                "checkpoint_id": checkpoint_id,
                "reason": reason
            }
        )


class CheckpointStorageError(CheckpointDomainError):
    """检查点存储错误"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        """初始化异常
        
        Args:
            message: 错误消息
            operation: 操作类型
        """
        super().__init__(
            message=message,
            error_code="CHECKPOINT_STORAGE_ERROR",
            context={
                "operation": operation
            }
        )


class CheckpointLimitExceededError(CheckpointDomainError):
    """检查点数量超限错误"""
    
    def __init__(self, thread_id: str, current_count: int, max_count: int):
        """初始化异常
        
        Args:
            thread_id: 线程ID
            current_count: 当前数量
            max_count: 最大数量
        """
        super().__init__(
            message=f"Checkpoint limit exceeded for thread {thread_id}: {current_count}/{max_count}",
            error_code="CHECKPOINT_LIMIT_EXCEEDED",
            context={
                "thread_id": thread_id,
                "current_count": current_count,
                "max_count": max_count
            }
        )


class CheckpointSizeExceededError(CheckpointDomainError):
    """检查点大小超限错误"""
    
    def __init__(self, checkpoint_id: str, size_mb: float, max_size_mb: float):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            size_mb: 实际大小（MB）
            max_size_mb: 最大大小（MB）
        """
        super().__init__(
            message=f"Checkpoint size exceeded for {checkpoint_id}: {size_mb:.2f}MB > {max_size_mb}MB",
            error_code="CHECKPOINT_SIZE_EXCEEDED",
            context={
                "checkpoint_id": checkpoint_id,
                "size_mb": size_mb,
                "max_size_mb": max_size_mb
            }
        )


class CheckpointExpiredError(CheckpointDomainError):
    """检查点已过期错误"""
    
    def __init__(self, checkpoint_id: str, expired_at: str):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            expired_at: 过期时间
        """
        super().__init__(
            message=f"Checkpoint {checkpoint_id} expired at {expired_at}",
            error_code="CHECKPOINT_EXPIRED",
            context={
                "checkpoint_id": checkpoint_id,
                "expired_at": expired_at
            }
        )


class CheckpointCorruptedError(CheckpointDomainError):
    """检查点损坏错误"""
    
    def __init__(self, checkpoint_id: str, corruption_reason: str):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            corruption_reason: 损坏原因
        """
        super().__init__(
            message=f"Checkpoint {checkpoint_id} is corrupted: {corruption_reason}",
            error_code="CHECKPOINT_CORRUPTED",
            context={
                "checkpoint_id": checkpoint_id,
                "corruption_reason": corruption_reason
            }
        )


class CheckpointBackupError(CheckpointDomainError):
    """检查点备份错误"""
    
    def __init__(self, checkpoint_id: str, backup_operation: str, reason: str):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            backup_operation: 备份操作
            reason: 失败原因
        """
        super().__init__(
            message=f"Backup {backup_operation} failed for checkpoint {checkpoint_id}: {reason}",
            error_code="CHECKPOINT_BACKUP_ERROR",
            context={
                "checkpoint_id": checkpoint_id,
                "backup_operation": backup_operation,
                "reason": reason
            }
        )


class CheckpointChainError(CheckpointDomainError):
    """检查点链错误"""
    
    def __init__(self, chain_id: str, reason: str):
        """初始化异常
        
        Args:
            chain_id: 链ID
            reason: 错误原因
        """
        super().__init__(
            message=f"Checkpoint chain {chain_id} error: {reason}",
            error_code="CHECKPOINT_CHAIN_ERROR",
            context={
                "chain_id": chain_id,
                "reason": reason
            }
        )


class ThreadNotFoundError(CheckpointDomainError):
    """线程未找到错误"""
    
    def __init__(self, thread_id: str):
        """初始化异常
        
        Args:
            thread_id: 线程ID
        """
        super().__init__(
            message=f"Thread {thread_id} not found",
            error_code="THREAD_NOT_FOUND",
            context={
                "thread_id": thread_id
            }
        )


class ThreadStateError(CheckpointDomainError):
    """线程状态错误"""
    
    def __init__(self, thread_id: str, current_state: str, expected_state: str):
        """初始化异常
        
        Args:
            thread_id: 线程ID
            current_state: 当前状态
            expected_state: 期望状态
        """
        super().__init__(
            message=f"Thread {thread_id} is in {current_state} state, expected {expected_state}",
            error_code="THREAD_STATE_ERROR",
            context={
                "thread_id": thread_id,
                "current_state": current_state,
                "expected_state": expected_state
            }
        )


class CheckpointConcurrencyError(CheckpointDomainError):
    """检查点并发错误"""
    
    def __init__(self, checkpoint_id: str, operation: str, conflict_details: str):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            operation: 操作类型
            conflict_details: 冲突详情
        """
        super().__init__(
            message=f"Concurrency conflict during {operation} on checkpoint {checkpoint_id}: {conflict_details}",
            error_code="CHECKPOINT_CONCURRENCY_ERROR",
            context={
                "checkpoint_id": checkpoint_id,
                "operation": operation,
                "conflict_details": conflict_details
            }
        )


class CheckpointPermissionError(CheckpointDomainError):
    """检查点权限错误"""
    
    def __init__(self, checkpoint_id: str, operation: str, user_id: Optional[str] = None):
        """初始化异常
        
        Args:
            checkpoint_id: 检查点ID
            operation: 操作类型
            user_id: 用户ID
        """
        message = f"Permission denied for {operation} on checkpoint {checkpoint_id}"
        if user_id:
            message += f" by user {user_id}"
        
        super().__init__(
            message=message,
            error_code="CHECKPOINT_PERMISSION_ERROR",
            context={
                "checkpoint_id": checkpoint_id,
                "operation": operation,
                "user_id": user_id
            }
        )


class CheckpointConfigurationError(CheckpointDomainError):
    """检查点配置错误"""
    
    def __init__(self, config_key: str, config_value: Any, reason: str):
        """初始化异常
        
        Args:
            config_key: 配置键
            config_value: 配置值
            reason: 错误原因
        """
        super().__init__(
            message=f"Invalid configuration for {config_key}={config_value}: {reason}",
            error_code="CHECKPOINT_CONFIGURATION_ERROR",
            context={
                "config_key": config_key,
                "config_value": config_value,
                "reason": reason
            }
        )