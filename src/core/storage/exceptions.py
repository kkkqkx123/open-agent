"""
存储系统异常定义

定义了存储系统相关的异常类型，提供统一的错误处理机制。
"""

from typing import Optional, Dict, Any


class StorageError(Exception):
    """存储错误基类
    
    所有存储相关的异常都应该继承自这个基类。
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化存储错误
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            错误信息字典
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class StorageConnectionError(StorageError):
    """存储连接错误
    
    当无法连接到存储后端时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储连接失败", 
        backend_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        **kwargs
    ):
        """初始化存储连接错误
        
        Args:
            message: 错误消息
            backend_name: 后端名称
            connection_string: 连接字符串
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if backend_name:
            details["backend_name"] = backend_name
        if connection_string:
            details["connection_string"] = connection_string
        
        super().__init__(
            message=message,
            error_code="STORAGE_CONNECTION_ERROR",
            details=details
        )
        self.backend_name = backend_name
        self.connection_string = connection_string


class StorageOperationError(StorageError):
    """存储操作错误
    
    当存储操作失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储操作失败", 
        operation: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ):
        """初始化存储操作错误
        
        Args:
            message: 错误消息
            operation: 操作类型
            key: 操作键
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        if key:
            details["key"] = key
        
        super().__init__(
            message=message,
            error_code="STORAGE_OPERATION_ERROR",
            details=details
        )
        self.operation = operation
        self.key = key


class StorageValidationError(StorageError):
    """存储验证错误
    
    当存储数据验证失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储数据验证失败", 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        """初始化存储验证错误
        
        Args:
            message: 错误消息
            field: 验证失败的字段
            value: 验证失败的值
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="STORAGE_VALIDATION_ERROR",
            details=details
        )
        self.field = field
        self.value = value


class StorageNotFoundError(StorageError):
    """存储未找到错误
    
    当请求的数据不存在时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储数据未找到", 
        key: Optional[str] = None,
        entity_id: Optional[str] = None,
        **kwargs
    ):
        """初始化存储未找到错误
        
        Args:
            message: 错误消息
            key: 数据键
            entity_id: 实体ID
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if key:
            details["key"] = key
        if entity_id:
            details["entity_id"] = entity_id
        
        super().__init__(
            message=message,
            error_code="STORAGE_NOT_FOUND_ERROR",
            details=details
        )
        self.key = key
        self.entity_id = entity_id


class StorageTimeoutError(StorageError):
    """存储超时错误
    
    当存储操作超时时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储操作超时", 
        timeout: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """初始化存储超时错误
        
        Args:
            message: 错误消息
            timeout: 超时时间（秒）
            operation: 操作类型
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if timeout:
            details["timeout"] = timeout
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="STORAGE_TIMEOUT_ERROR",
            details=details
        )
        self.timeout = timeout
        self.operation = operation


class StorageCapacityError(StorageError):
    """存储容量错误
    
    当存储容量不足时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储容量不足", 
        current_size: Optional[int] = None,
        max_size: Optional[int] = None,
        **kwargs
    ):
        """初始化存储容量错误
        
        Args:
            message: 错误消息
            current_size: 当前大小
            max_size: 最大大小
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if current_size:
            details["current_size"] = current_size
        if max_size:
            details["max_size"] = max_size
        
        super().__init__(
            message=message,
            error_code="STORAGE_CAPACITY_ERROR",
            details=details
        )
        self.current_size = current_size
        self.max_size = max_size


class StorageIntegrityError(StorageError):
    """存储完整性错误
    
    当存储数据完整性检查失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储数据完整性检查失败", 
        checksum: Optional[str] = None,
        expected_checksum: Optional[str] = None,
        **kwargs
    ):
        """初始化存储完整性错误
        
        Args:
            message: 错误消息
            checksum: 实际校验和
            expected_checksum: 期望校验和
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if checksum:
            details["checksum"] = checksum
        if expected_checksum:
            details["expected_checksum"] = expected_checksum
        
        super().__init__(
            message=message,
            error_code="STORAGE_INTEGRITY_ERROR",
            details=details
        )
        self.checksum = checksum
        self.expected_checksum = expected_checksum


class StorageConfigurationError(StorageError):
    """存储配置错误
    
    当存储配置错误时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储配置错误", 
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs
    ):
        """初始化存储配置错误
        
        Args:
            message: 错误消息
            config_key: 配置键
            config_value: 配置值
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)
        
        super().__init__(
            message=message,
            error_code="STORAGE_CONFIGURATION_ERROR",
            details=details
        )
        self.config_key = config_key
        self.config_value = config_value


class StorageMigrationError(StorageError):
    """存储迁移错误
    
    当存储迁移失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储迁移失败", 
        migration_id: Optional[str] = None,
        migration_version: Optional[str] = None,
        **kwargs
    ):
        """初始化存储迁移错误
        
        Args:
            message: 错误消息
            migration_id: 迁移ID
            migration_version: 迁移版本
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if migration_id:
            details["migration_id"] = migration_id
        if migration_version:
            details["migration_version"] = migration_version
        
        super().__init__(
            message=message,
            error_code="STORAGE_MIGRATION_ERROR",
            details=details
        )
        self.migration_id = migration_id
        self.migration_version = migration_version


class StorageTransactionError(StorageError):
    """存储事务错误
    
    当存储事务操作失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储事务操作失败", 
        transaction_id: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """初始化存储事务错误
        
        Args:
            message: 错误消息
            transaction_id: 事务ID
            operation: 操作类型
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if transaction_id:
            details["transaction_id"] = transaction_id
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="STORAGE_TRANSACTION_ERROR",
            details=details
        )
        self.transaction_id = transaction_id
        self.operation = operation


class StoragePermissionError(StorageError):
    """存储权限错误
    
    当存储操作权限不足时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储操作权限不足", 
        required_permission: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """初始化存储权限错误
        
        Args:
            message: 错误消息
            required_permission: 所需权限
            operation: 操作类型
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="STORAGE_PERMISSION_ERROR",
            details=details
        )
        self.required_permission = required_permission
        self.operation = operation


class StorageSerializationError(StorageError):
    """存储序列化错误
    
    当存储数据序列化失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储数据序列化失败", 
        data_type: Optional[str] = None,
        serialization_format: Optional[str] = None,
        **kwargs
    ):
        """初始化存储序列化错误
        
        Args:
            message: 错误消息
            data_type: 数据类型
            serialization_format: 序列化格式
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if data_type:
            details["data_type"] = data_type
        if serialization_format:
            details["serialization_format"] = serialization_format
        
        super().__init__(
            message=message,
            error_code="STORAGE_SERIALIZATION_ERROR",
            details=details
        )
        self.data_type = data_type
        self.serialization_format = serialization_format


class StorageCompressionError(StorageError):
    """存储压缩错误
    
    当存储数据压缩失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储数据压缩失败", 
        compression_algorithm: Optional[str] = None,
        original_size: Optional[int] = None,
        **kwargs
    ):
        """初始化存储压缩错误
        
        Args:
            message: 错误消息
            compression_algorithm: 压缩算法
            original_size: 原始大小
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if compression_algorithm:
            details["compression_algorithm"] = compression_algorithm
        if original_size:
            details["original_size"] = original_size
        
        super().__init__(
            message=message,
            error_code="STORAGE_COMPRESSION_ERROR",
            details=details
        )
        self.compression_algorithm = compression_algorithm
        self.original_size = original_size


class StorageEncryptionError(StorageError):
    """存储加密错误
    
    当存储数据加密失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str = "存储数据加密失败", 
        encryption_algorithm: Optional[str] = None,
        key_id: Optional[str] = None,
        **kwargs
    ):
        """初始化存储加密错误
        
        Args:
            message: 错误消息
            encryption_algorithm: 加密算法
            key_id: 密钥ID
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if encryption_algorithm:
            details["encryption_algorithm"] = encryption_algorithm
        if key_id:
            details["key_id"] = key_id
        
        super().__init__(
            message=message,
            error_code="STORAGE_ENCRYPTION_ERROR",
            details=details
        )
        self.encryption_algorithm = encryption_algorithm
        self.key_id = key_id