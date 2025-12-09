"""存储后端核心异常类

定义存储后端和提供者的专用异常。
"""

from src.interfaces.storage.exceptions import StorageError


class StorageBackendError(StorageError):
    """存储后端错误
    
    用于存储后端相关的错误。
    """
    
    def __init__(self, message: str, backend_type: str | None = None, error_code: str | None = None):
        """初始化存储后端错误
        
        Args:
            message: 错误消息
            backend_type: 后端类型
            error_code: 错误代码
        """
        super().__init__(message)
        self.backend_type = backend_type
        self.error_code = error_code


class ProviderError(StorageError):
    """存储提供者错误
    
    用于存储提供者相关的错误。
    """
    
    def __init__(self, message: str, provider_type: str | None = None, operation: str | None = None):
        """初始化存储提供者错误
        
        Args:
            message: 错误消息
            provider_type: 提供者类型
            operation: 操作类型
        """
        super().__init__(message)
        self.provider_type = provider_type
        self.operation = operation


class ConnectionError(StorageBackendError):
    """连接错误
    
    用于连接相关的错误。
    """
    
    def __init__(self, message: str, backend_type: str | None = None, connection_details: str | None = None):
        """初始化连接错误
        
        Args:
            message: 错误消息
            backend_type: 后端类型
            connection_details: 连接详情
        """
        super().__init__(message, backend_type, "CONNECTION_ERROR")
        self.connection_details = connection_details


class ConfigurationError(StorageBackendError):
    """配置错误
    
    用于配置相关的错误。
    """
    
    def __init__(self, message: str, backend_type: str | None = None, config_key: str | None = None):
        """初始化配置错误
        
        Args:
            message: 错误消息
            backend_type: 后端类型
            config_key: 配置键
        """
        super().__init__(message, backend_type, "CONFIGURATION_ERROR")
        self.config_key = config_key


class TransactionError(ProviderError):
    """事务错误
    
    用于事务相关的错误。
    """
    
    def __init__(self, message: str, provider_type: str | None = None, transaction_id: str | None = None):
        """初始化事务错误
        
        Args:
            message: 错误消息
            provider_type: 提供者类型
            transaction_id: 事务ID
        """
        super().__init__(message, provider_type, "TRANSACTION")
        self.transaction_id = transaction_id


class ValidationError(StorageBackendError):
    """验证错误
    
    用于数据验证相关的错误。
    """
    
    def __init__(self, message: str, backend_type: str | None = None, field_name: str | None = None):
        """初始化验证错误
        
        Args:
            message: 错误消息
            backend_type: 后端类型
            field_name: 字段名
        """
        super().__init__(message, backend_type, "VALIDATION_ERROR")
        self.field_name = field_name