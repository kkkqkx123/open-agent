"""检查点模块异常定义

定义检查点相关的异常类型。
"""

from typing import Any, Dict, Optional


class CheckpointError(Exception):
    """检查点基础异常类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化异常
        
        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """返回异常字符串表示"""
        if self.details:
            return f"{self.message} (详情: {self.details})"
        return self.message


class CheckpointValidationError(CheckpointError):
    """检查点验证错误
    
    当检查点数据验证失败时抛出。
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        """初始化验证错误
        
        Args:
            message: 错误消息
            field: 验证失败的字段名
            value: 验证失败的值
        """
        details = {}
        if field is not None:
            details["field"] = field
        if value is not None:
            details["value"] = value
        
        super().__init__(message, details)
        self.field = field
        self.value = value


class CheckpointNotFoundError(CheckpointError):
    """检查点未找到错误
    
    当请求的检查点不存在时抛出。
    """
    
    def __init__(self, checkpoint_id: str, thread_id: Optional[str] = None):
        """初始化未找到错误
        
        Args:
            checkpoint_id: 检查点ID
            thread_id: 线程ID（可选）
        """
        message = f"检查点未找到: {checkpoint_id}"
        details = {"checkpoint_id": checkpoint_id}
        
        if thread_id:
            details["thread_id"] = thread_id
            message += f" (线程: {thread_id})"
        
        super().__init__(message, details)
        self.checkpoint_id = checkpoint_id
        self.thread_id = thread_id


class CheckpointStorageError(CheckpointError):
    """检查点存储错误
    
    当存储操作失败时抛出。
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, storage_type: Optional[str] = None):
        """初始化存储错误
        
        Args:
            message: 错误消息
            operation: 失败的操作类型
            storage_type: 存储类型
        """
        details = {}
        if operation:
            details["operation"] = operation
        if storage_type:
            details["storage_type"] = storage_type
        
        super().__init__(message, details)
        self.operation = operation
        self.storage_type = storage_type


class CheckpointConflictError(CheckpointError):
    """检查点冲突错误
    
    当检查点操作发生冲突时抛出（如并发修改）。
    """
    
    def __init__(self, message: str, checkpoint_id: str, conflict_type: Optional[str] = None):
        """初始化冲突错误
        
        Args:
            message: 错误消息
            checkpoint_id: 检查点ID
            conflict_type: 冲突类型
        """
        details = {"checkpoint_id": checkpoint_id}
        if conflict_type:
            details["conflict_type"] = conflict_type
        
        super().__init__(message, details)
        self.checkpoint_id = checkpoint_id
        self.conflict_type = conflict_type


class CheckpointTimeoutError(CheckpointError):
    """检查点超时错误
    
    当检查点操作超时时抛出。
    """
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, operation: Optional[str] = None):
        """初始化超时错误
        
        Args:
            message: 错误消息
            timeout_seconds: 超时时间（秒）
            operation: 超时的操作
        """
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class CheckpointQuotaExceededError(CheckpointError):
    """检查点配额超限错误
    
    当检查点数量或大小超过配额时抛出。
    """
    
    def __init__(self, message: str, quota_type: str, current_value: int, max_value: int):
        """初始化配额超限错误
        
        Args:
            message: 错误消息
            quota_type: 配额类型（如 "count", "size"）
            current_value: 当前值
            max_value: 最大值
        """
        details = {
            "quota_type": quota_type,
            "current_value": current_value,
            "max_value": max_value
        }
        
        super().__init__(message, details)
        self.quota_type = quota_type
        self.current_value = current_value
        self.max_value = max_value


class CheckpointCorruptionError(CheckpointError):
    """检查点损坏错误
    
    当检查点数据损坏时抛出。
    """
    
    def __init__(self, message: str, checkpoint_id: str, corruption_details: Optional[str] = None):
        """初始化损坏错误
        
        Args:
            message: 错误消息
            checkpoint_id: 检查点ID
            corruption_details: 损坏详情
        """
        details = {"checkpoint_id": checkpoint_id}
        if corruption_details:
            details["corruption_details"] = corruption_details
        
        super().__init__(message, details)
        self.checkpoint_id = checkpoint_id
        self.corruption_details = corruption_details


class CheckpointVersionError(CheckpointError):
    """检查点版本错误
    
    当检查点版本不兼容时抛出。
    """
    
    def __init__(self, message: str, expected_version: Optional[str] = None, actual_version: Optional[str] = None):
        """初始化版本错误
        
        Args:
            message: 错误消息
            expected_version: 期望的版本
            actual_version: 实际的版本
        """
        details = {}
        if expected_version:
            details["expected_version"] = expected_version
        if actual_version:
            details["actual_version"] = actual_version
        
        super().__init__(message, details)
        self.expected_version = expected_version
        self.actual_version = actual_version


class CheckpointConfigurationError(CheckpointError):
    """检查点配置错误
    
    当检查点配置无效时抛出。
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None):
        """初始化配置错误
        
        Args:
            message: 错误消息
            config_key: 配置键
            config_value: 配置值
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = config_value
        
        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class CheckpointHookError(CheckpointError):
    """检查点Hook错误
    
    当检查点Hook执行失败时抛出。
    """
    
    def __init__(self, message: str, hook_name: Optional[str] = None, hook_type: Optional[str] = None):
        """初始化Hook错误
        
        Args:
            message: 错误消息
            hook_name: Hook名称
            hook_type: Hook类型（如 "before_save", "after_load"）
        """
        details = {}
        if hook_name:
            details["hook_name"] = hook_name
        if hook_type:
            details["hook_type"] = hook_type
        
        super().__init__(message, details)
        self.hook_name = hook_name
        self.hook_type = hook_type


class CheckpointCacheError(CheckpointError):
    """检查点缓存错误
    
    当检查点缓存操作失败时抛出。
    """
    
    def __init__(self, message: str, cache_operation: Optional[str] = None, cache_key: Optional[str] = None):
        """初始化缓存错误
        
        Args:
            message: 错误消息
            cache_operation: 缓存操作类型
            cache_key: 缓存键
        """
        details = {}
        if cache_operation:
            details["cache_operation"] = cache_operation
        if cache_key:
            details["cache_key"] = cache_key
        
        super().__init__(message, details)
        self.cache_operation = cache_operation
        self.cache_key = cache_key


class CheckpointResourceError(CheckpointError):
    """检查点资源错误
     
    当检查点资源不足时抛出。
    """
     
    def __init__(self, message: str, resource_type: str, required_amount: Optional[int] = None, available_amount: Optional[int] = None):
        """初始化资源错误
         
        Args:
            message: 错误消息
            resource_type: 资源类型（如 "memory", "disk"）
            required_amount: 需要的资源量
            available_amount: 可用的资源量
        """
        details: Dict[str, Any] = {"resource_type": resource_type}
        if required_amount is not None:
            details["required_amount"] = required_amount
        if available_amount is not None:
            details["available_amount"] = available_amount
        
        super().__init__(message, details)
        self.resource_type = resource_type
        self.required_amount = required_amount
        self.available_amount = available_amount