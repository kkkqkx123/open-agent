"""
存储相关异常定义
"""

from typing import Dict, Any, Optional


class StorageError(Exception):
    """存储基础异常
    
    所有存储相关异常的基类，提供统一的错误处理接口。
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """初始化存储异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
            cause: 原始异常
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "STORAGE_ERROR"
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class StorageConnectionError(StorageError):
    """存储连接异常
    
    当无法连接到存储后端时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage connection failed",
        connection_string: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化连接异常
        
        Args:
            message: 错误消息
            connection_string: 连接字符串
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_CONNECTION_ERROR",
            **kwargs
        )
        self.connection_string = connection_string
        
        if connection_string:
            self.details["connection_string"] = connection_string


class StorageTransactionError(StorageError):
    """存储事务异常
    
    当事务操作失败时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage transaction failed",
        transaction_id: Optional[str] = None,
        operation_index: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """初始化事务异常
        
        Args:
            message: 错误消息
            transaction_id: 事务ID
            operation_index: 失败的操作索引
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_TRANSACTION_ERROR",
            **kwargs
        )
        self.transaction_id = transaction_id
        self.operation_index = operation_index
        
        if transaction_id:
            self.details["transaction_id"] = transaction_id
        if operation_index is not None:
            self.details["operation_index"] = operation_index


class StorageValidationError(StorageError):
    """存储验证异常
    
    当数据验证失败时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage validation failed",
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化验证异常
        
        Args:
            message: 错误消息
            field_name: 字段名
            field_value: 字段值
            validation_rule: 验证规则
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_VALIDATION_ERROR",
            **kwargs
        )
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule
        
        if field_name:
            self.details["field_name"] = field_name
        if field_value is not None:
            self.details["field_value"] = str(field_value)
        if validation_rule:
            self.details["validation_rule"] = validation_rule


class StorageNotFoundError(StorageError):
    """存储未找到异常
    
    当请求的数据不存在时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage item not found",
        item_id: Optional[str] = None,
        item_type: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化未找到异常
        
        Args:
            message: 错误消息
            item_id: 项目ID
            item_type: 项目类型
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_NOT_FOUND_ERROR",
            **kwargs
        )
        self.item_id = item_id
        self.item_type = item_type
        
        if item_id:
            self.details["item_id"] = item_id
        if item_type:
            self.details["item_type"] = item_type


class StoragePermissionError(StorageError):
    """存储权限异常
    
    当没有足够权限执行操作时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage permission denied",
        operation: Optional[str] = None,
        resource: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化权限异常
        
        Args:
            message: 错误消息
            operation: 操作类型
            resource: 资源标识
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_PERMISSION_ERROR",
            **kwargs
        )
        self.operation = operation
        self.resource = resource
        
        if operation:
            self.details["operation"] = operation
        if resource:
            self.details["resource"] = resource


class StorageTimeoutError(StorageError):
    """存储超时异常
    
    当操作超时时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage operation timed out",
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化超时异常
        
        Args:
            message: 错误消息
            timeout_seconds: 超时时间（秒）
            operation: 操作类型
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_TIMEOUT_ERROR",
            **kwargs
        )
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        
        if timeout_seconds is not None:
            self.details["timeout_seconds"] = timeout_seconds
        if operation:
            self.details["operation"] = operation


class StorageCapacityError(StorageError):
    """存储容量异常
    
    当存储空间不足时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage capacity exceeded",
        required_size: Optional[int] = None,
        available_size: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """初始化容量异常
        
        Args:
            message: 错误消息
            required_size: 需要的空间（字节）
            available_size: 可用空间（字节）
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_CAPACITY_ERROR",
            **kwargs
        )
        self.required_size = required_size
        self.available_size = available_size
        
        if required_size is not None:
            self.details["required_size"] = required_size
        if available_size is not None:
            self.details["available_size"] = available_size


class StorageIntegrityError(StorageError):
    """存储完整性异常
    
    当数据完整性检查失败时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage integrity check failed",
        checksum_expected: Optional[str] = None,
        checksum_actual: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """初始化完整性异常
        
        Args:
            message: 错误消息
            checksum_expected: 期望的校验和
            checksum_actual: 实际的校验和
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_INTEGRITY_ERROR",
            **kwargs
        )
        self.checksum_expected = checksum_expected
        self.checksum_actual = checksum_actual
        
        if checksum_expected:
            self.details["checksum_expected"] = checksum_expected
        if checksum_actual:
            self.details["checksum_actual"] = checksum_actual


class StorageConfigurationError(StorageError):
    """存储配置异常
    
    当存储配置错误时抛出。
    """
    
    def __init__(
        self, 
        message: str = "Storage configuration error",
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        """初始化配置异常
        
        Args:
            message: 错误消息
            config_key: 配置键
            config_value: 配置值
            **kwargs: 其他参数
        """
        super().__init__(
            message=message,
            error_code="STORAGE_CONFIGURATION_ERROR",
            **kwargs
        )
        self.config_key = config_key
        self.config_value = config_value
        
        if config_key:
            self.details["config_key"] = config_key
        if config_value is not None:
            self.details["config_value"] = str(config_value)


class StorageMigrationError(StorageError):
     """存储迁移异常
     
     当数据迁移失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage migration failed",
         migration_version: Optional[str] = None,
         migration_step: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化迁移异常
         
         Args:
             message: 错误消息
             migration_version: 迁移版本
             migration_step: 迁移步骤
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_MIGRATION_ERROR",
             **kwargs
         )
         self.migration_version = migration_version
         self.migration_step = migration_step
         
         if migration_version:
             self.details["migration_version"] = migration_version
         if migration_step:
             self.details["migration_step"] = migration_step


class StorageSerializationError(StorageError):
     """存储序列化异常
     
     当数据序列化失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage serialization failed",
         data_type: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化序列化异常
         
         Args:
             message: 错误消息
             data_type: 数据类型
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_SERIALIZATION_ERROR",
             **kwargs
         )
         self.data_type = data_type
         
         if data_type:
             self.details["data_type"] = data_type


class StorageCompressionError(StorageError):
     """存储压缩异常
     
     当数据压缩失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage compression failed",
         compression_algorithm: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化压缩异常
         
         Args:
             message: 错误消息
             compression_algorithm: 压缩算法
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_COMPRESSION_ERROR",
             **kwargs
         )
         self.compression_algorithm = compression_algorithm
         
         if compression_algorithm:
             self.details["compression_algorithm"] = compression_algorithm


class StorageEncryptionError(StorageError):
     """存储加密异常
     
     当数据加密失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage encryption failed",
         encryption_algorithm: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化加密异常
         
         Args:
             message: 错误消息
             encryption_algorithm: 加密算法
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_ENCRYPTION_ERROR",
             **kwargs
         )
         self.encryption_algorithm = encryption_algorithm
         
         if encryption_algorithm:
             self.details["encryption_algorithm"] = encryption_algorithm


class StorageIndexError(StorageError):
     """存储索引异常
     
     当索引操作失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage index error",
         index_name: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化索引异常
         
         Args:
             message: 错误消息
             index_name: 索引名称
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_INDEX_ERROR",
             **kwargs
         )
         self.index_name = index_name
         
         if index_name:
             self.details["index_name"] = index_name


class StorageBackupError(StorageError):
     """存储备份异常
     
     当备份操作失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage backup failed",
         backup_location: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化备份异常
         
         Args:
             message: 错误消息
             backup_location: 备份位置
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_BACKUP_ERROR",
             **kwargs
         )
         self.backup_location = backup_location
         
         if backup_location:
             self.details["backup_location"] = backup_location


class StorageLockError(StorageError):
     """存储锁定异常
     
     当锁定操作失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage lock error",
         lock_id: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化锁定异常
         
         Args:
             message: 错误消息
             lock_id: 锁定ID
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_LOCK_ERROR",
             **kwargs
         )
         self.lock_id = lock_id
         
         if lock_id:
             self.details["lock_id"] = lock_id


class StorageQueryError(StorageError):
     """存储查询异常
     
     当查询操作失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage query error",
         query: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化查询异常
         
         Args:
             message: 错误消息
             query: 查询语句
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_QUERY_ERROR",
             **kwargs
         )
         self.query = query
         
         if query:
             self.details["query"] = query


class StorageHealthError(StorageError):
     """存储健康检查异常
     
     当健康检查失败时抛出。
     """
     
     def __init__(
         self, 
         message: str = "Storage health check failed",
         component: Optional[str] = None,
         **kwargs: Any
     ) -> None:
         """初始化健康检查异常
         
         Args:
             message: 错误消息
             component: 组件名称
             **kwargs: 其他参数
         """
         super().__init__(
             message=message,
             error_code="STORAGE_HEALTH_ERROR",
             **kwargs
         )
         self.component = component
         
         if component:
             self.details["component"] = component


# 异常映射字典，用于根据错误代码创建异常
EXCEPTION_MAP = {
     "STORAGE_CONNECTION_ERROR": StorageConnectionError,
     "STORAGE_TRANSACTION_ERROR": StorageTransactionError,
     "STORAGE_VALIDATION_ERROR": StorageValidationError,
     "STORAGE_NOT_FOUND_ERROR": StorageNotFoundError,
     "STORAGE_PERMISSION_ERROR": StoragePermissionError,
     "STORAGE_TIMEOUT_ERROR": StorageTimeoutError,
     "STORAGE_CAPACITY_ERROR": StorageCapacityError,
     "STORAGE_INTEGRITY_ERROR": StorageIntegrityError,
     "STORAGE_CONFIGURATION_ERROR": StorageConfigurationError,
     "STORAGE_MIGRATION_ERROR": StorageMigrationError,
     "STORAGE_SERIALIZATION_ERROR": StorageSerializationError,
     "STORAGE_COMPRESSION_ERROR": StorageCompressionError,
     "STORAGE_ENCRYPTION_ERROR": StorageEncryptionError,
     "STORAGE_INDEX_ERROR": StorageIndexError,
     "STORAGE_BACKUP_ERROR": StorageBackupError,
     "STORAGE_LOCK_ERROR": StorageLockError,
     "STORAGE_QUERY_ERROR": StorageQueryError,
     "STORAGE_HEALTH_ERROR": StorageHealthError,
}


def create_storage_error(
    error_code: str, 
    message: str, 
    details: Optional[Dict[str, Any]] = None,
    cause: Optional[Exception] = None
) -> StorageError:
    """根据错误代码创建存储异常
    
    Args:
        error_code: 错误代码
        message: 错误消息
        details: 错误详情
        cause: 原始异常
        
    Returns:
        存储异常实例
    """
    exception_class = EXCEPTION_MAP.get(error_code, StorageError)
    return exception_class(  # type: ignore[no-any-return]
        message=message,
        error_code=error_code,
        details=details,
        cause=cause
    )
