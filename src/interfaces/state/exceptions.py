"""状态管理异常定义

定义状态管理系统的异常类，不包含存储相关异常（存储异常在storage模块中定义）。
"""

from typing import Optional, Any, Dict


class StateError(Exception):
    """状态管理基础异常"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class StateValidationError(StateError):
    """状态验证异常"""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_VALIDATION_ERROR", kwargs)
        self.field = field
        self.value = value
        self.validation_rule = validation_rule
        
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["value"] = value
        if validation_rule:
            self.details["validation_rule"] = validation_rule


class StateNotFoundError(StateError):
    """状态未找到异常"""
    
    def __init__(
        self, 
        message: str, 
        state_id: Optional[str] = None,
        state_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_NOT_FOUND_ERROR", kwargs)
        self.state_id = state_id
        self.state_type = state_type
        
        if state_id:
            self.details["state_id"] = state_id
        if state_type:
            self.details["state_type"] = state_type


class StateTimeoutError(StateError):
    """状态操作超时异常"""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_TIMEOUT_ERROR", kwargs)
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        
        if operation:
            self.details["operation"] = operation
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class StateCapacityError(StateError):
    """状态容量超限异常"""
    
    def __init__(
        self, 
        message: str, 
        required_size: int = 0, 
        available_size: int = 0,
        capacity_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_CAPACITY_ERROR", kwargs)
        self.required_size = required_size
        self.available_size = available_size
        self.capacity_type = capacity_type
        
        self.details["required_size"] = required_size
        self.details["available_size"] = available_size
        if capacity_type:
            self.details["capacity_type"] = capacity_type


class StateTransitionError(StateError):
    """状态转换错误异常"""
    
    def __init__(
        self, 
        message: str, 
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        transition_rule: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_TRANSITION_ERROR", kwargs)
        self.from_state = from_state
        self.to_state = to_state
        self.transition_rule = transition_rule
        
        if from_state:
            self.details["from_state"] = from_state
        if to_state:
            self.details["to_state"] = to_state
        if transition_rule:
            self.details["transition_rule"] = transition_rule


class StateConsistencyError(StateError):
    """状态一致性错误异常"""
    
    def __init__(
        self, 
        message: str, 
        inconsistency_type: Optional[str] = None,
        expected_value: Optional[Any] = None,
        actual_value: Optional[Any] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_CONSISTENCY_ERROR", kwargs)
        self.inconsistency_type = inconsistency_type
        self.expected_value = expected_value
        self.actual_value = actual_value
        
        if inconsistency_type:
            self.details["inconsistency_type"] = inconsistency_type
        if expected_value is not None:
            self.details["expected_value"] = expected_value
        if actual_value is not None:
            self.details["actual_value"] = actual_value


class StateSerializationError(StateError):
    """状态序列化错误异常"""
    
    def __init__(
        self, 
        message: str, 
        serialization_format: Optional[str] = None,
        data_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_SERIALIZATION_ERROR", kwargs)
        self.serialization_format = serialization_format
        self.data_type = data_type
        
        if serialization_format:
            self.details["serialization_format"] = serialization_format
        if data_type:
            self.details["data_type"] = data_type


class StateDeserializationError(StateError):
    """状态反序列化错误异常"""
    
    def __init__(
        self, 
        message: str, 
        serialization_format: Optional[str] = None,
        data_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_DESERIALIZATION_ERROR", kwargs)
        self.serialization_format = serialization_format
        self.data_type = data_type
        
        if serialization_format:
            self.details["serialization_format"] = serialization_format
        if data_type:
            self.details["data_type"] = data_type


class StateLockError(StateError):
    """状态锁定错误异常"""
    
    def __init__(
        self, 
        message: str, 
        lock_id: Optional[str] = None,
        lock_owner: Optional[str] = None,
        lock_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_LOCK_ERROR", kwargs)
        self.lock_id = lock_id
        self.lock_owner = lock_owner
        self.lock_type = lock_type
        
        if lock_id:
            self.details["lock_id"] = lock_id
        if lock_owner:
            self.details["lock_owner"] = lock_owner
        if lock_type:
            self.details["lock_type"] = lock_type


class StateVersionError(StateError):
    """状态版本错误异常"""
    
    def __init__(
        self, 
        message: str, 
        current_version: Optional[str] = None,
        expected_version: Optional[str] = None,
        version_conflict: Optional[bool] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_VERSION_ERROR", kwargs)
        self.current_version = current_version
        self.expected_version = expected_version
        self.version_conflict = version_conflict
        
        if current_version:
            self.details["current_version"] = current_version
        if expected_version:
            self.details["expected_version"] = expected_version
        if version_conflict is not None:
            self.details["version_conflict"] = version_conflict


class StateConflictError(StateError):
    """状态冲突异常"""
    
    def __init__(
        self,
        message: str,
        conflict_type: Optional[str] = None,
        conflicting_state: Optional[Any] = None,
        expected_state: Optional[Any] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_CONFLICT_ERROR", kwargs)
        self.conflict_type = conflict_type
        self.conflicting_state = conflicting_state
        self.expected_state = expected_state
        
        if conflict_type:
            self.details["conflict_type"] = conflict_type
        if conflicting_state is not None:
            self.details["conflicting_state"] = conflicting_state
        if expected_state is not None:
            self.details["expected_state"] = expected_state


class StateCacheError(StateError):
    """状态缓存异常"""
    
    def __init__(
        self,
        message: str,
        cache_operation: Optional[str] = None,
        cache_key: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "STATE_CACHE_ERROR", kwargs)
        self.cache_operation = cache_operation
        self.cache_key = cache_key
        
        if cache_operation:
            self.details["cache_operation"] = cache_operation
        if cache_key:
            self.details["cache_key"] = cache_key


# 别名，保持向后兼容性
StateException = StateError


# 导出所有异常
__all__ = [
    "StateError",
    "StateException",
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
    "StateConflictError",
    "StateCacheError",
]