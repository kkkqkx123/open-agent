"""Checkpoint接口定义

包含Checkpoint接口和异常定义。
"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class CheckpointError(Exception):
    """Checkpoint操作基础异常"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint未找到异常"""
    
    def __init__(
        self, 
        message: str, 
        checkpoint_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "CHECKPOINT_NOT_FOUND_ERROR", kwargs)
        self.checkpoint_id = checkpoint_id
        self.thread_id = thread_id
        
        if checkpoint_id:
            self.details["checkpoint_id"] = checkpoint_id
        if thread_id:
            self.details["thread_id"] = thread_id


class CheckpointStorageError(CheckpointError):
    """Checkpoint存储异常"""
    
    def __init__(
        self, 
        message: str, 
        storage_operation: Optional[str] = None,
        storage_backend: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "CHECKPOINT_STORAGE_ERROR", kwargs)
        self.storage_operation = storage_operation
        self.storage_backend = storage_backend
        
        if storage_operation:
            self.details["storage_operation"] = storage_operation
        if storage_backend:
            self.details["storage_backend"] = storage_backend


class CheckpointValidationError(CheckpointError):
    """Checkpoint验证异常"""
    
    def __init__(
        self, 
        message: str, 
        validation_errors: Optional[List[str]] = None,
        checkpoint_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        super().__init__(message, "CHECKPOINT_VALIDATION_ERROR", kwargs)
        self.validation_errors = validation_errors or []
        self.checkpoint_data = checkpoint_data or {}
        
        if validation_errors:
            self.details["validation_errors"] = validation_errors
        if checkpoint_data:
            self.details["checkpoint_data"] = checkpoint_data


class CheckpointSerializationError(CheckpointError):
    """Checkpoint序列化异常"""
    
    def __init__(
        self, 
        message: str, 
        serialization_format: Optional[str] = None,
        data_type: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "CHECKPOINT_SERIALIZATION_ERROR", kwargs)
        self.serialization_format = serialization_format
        self.data_type = data_type
        
        if serialization_format:
            self.details["serialization_format"] = serialization_format
        if data_type:
            self.details["data_type"] = data_type


class CheckpointTimeoutError(CheckpointError):
    """Checkpoint操作超时异常"""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(message, "CHECKPOINT_TIMEOUT_ERROR", kwargs)
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        
        if operation:
            self.details["operation"] = operation
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class CheckpointVersionError(CheckpointError):
    """Checkpoint版本错误异常"""
    
    def __init__(
        self, 
        message: str, 
        current_version: Optional[str] = None,
        expected_version: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, "CHECKPOINT_VERSION_ERROR", kwargs)
        self.current_version = current_version
        self.expected_version = expected_version
        
        if current_version:
            self.details["current_version"] = current_version
        if expected_version:
            self.details["expected_version"] = expected_version


# Checkpoint接口定义
class CheckpointInterface(ABC):
    """Checkpoint接口定义"""
    
    @abstractmethod
    def save(
        self, 
        checkpoint_id: str, 
        data: Dict[str, Any], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存checkpoint数据"""
        pass
    
    @abstractmethod
    def load(self, checkpoint_id: str) -> Dict[str, Any]:
        """加载checkpoint数据"""
        pass
    
    @abstractmethod
    def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        pass
    
    @abstractmethod
    def list_checkpoints(
        self, 
        thread_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出checkpoint"""
        pass
    
    @abstractmethod
    def exists(self, checkpoint_id: str) -> bool:
        """检查checkpoint是否存在"""
        pass


# 导出所有异常和接口
__all__ = [
    # 异常类
    "CheckpointError",
    "CheckpointNotFoundError",
    "CheckpointStorageError",
    "CheckpointValidationError",
    "CheckpointSerializationError",
    "CheckpointTimeoutError",
    "CheckpointVersionError",
    # 接口类
    "CheckpointInterface",
]