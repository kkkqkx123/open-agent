"""存储模块错误处理器

为存储管理系统提供专门的错误处理和恢复策略。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, Callable
import asyncio

from src.infrastructure.error_management import (
     BaseErrorHandler, ErrorCategory, ErrorSeverity,
     register_error_handler, operation_with_retry
)
from src.interfaces.storage.exceptions import (
     StorageError, StorageConnectionError, StorageTransactionError,
     StorageValidationError, StorageNotFoundError, StorageTimeoutError,
     StorageCapacityError, StoragePermissionError, StorageConfigurationError,
     StorageMigrationError, StorageSerializationError, StorageCompressionError,
     StorageEncryptionError, StorageIndexError, StorageBackupError, StorageLockError,
     StorageQueryError, StorageHealthError
)
from src.interfaces.storage.adapter import IStorageErrorHandler

logger = get_logger(__name__)


class StorageErrorHandler(BaseErrorHandler):
    """存储模块错误处理器"""
    
    def __init__(self):
        """初始化存储错误处理器"""
        super().__init__(ErrorCategory.STORAGE, ErrorSeverity.HIGH)
        self._recovery_strategies = {
            StorageConnectionError: self._handle_connection_error,
            StorageValidationError: self._handle_validation_error,
            StorageCapacityError: self._handle_capacity_error,
            StoragePermissionError: self._handle_permission_error,
            StorageTimeoutError: self._handle_timeout_error,
            StorageTransactionError: self._handle_transaction_error,
            StorageConfigurationError: self._handle_configuration_error,
            StorageMigrationError: self._handle_migration_error,
            StorageSerializationError: self._handle_serialization_error,
            StorageCompressionError: self._handle_compression_error,
            StorageEncryptionError: self._handle_encryption_error,
            StorageIndexError: self._handle_index_error,
            StorageBackupError: self._handle_backup_error,
            StorageLockError: self._handle_lock_error,
            StorageQueryError: self._handle_query_error,
            StorageHealthError: self._handle_health_error,
        }
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误"""
        return isinstance(error, StorageError)
    
    def handle(self, error: Exception, context: Optional[Dict] = None) -> None:
         """处理存储错误"""
         try:
             # 记录错误日志
             self._log_error(error, context)
             
             # 根据错误类型选择恢复策略
             error_type = type(error)
             if error_type in self._recovery_strategies:
                 self._recovery_strategies[error_type](error, context)  # type: ignore[index]
             else:
                 # 通用存储错误处理
                 if isinstance(error, StorageError):
                     self._handle_generic_storage_error(error, context)
                 
         except Exception as handler_error:
             # 错误处理器本身出错，记录但不抛出异常
             logger.error(f"存储错误处理器内部错误: {handler_error}")
    
    def _handle_connection_error(self, error: StorageConnectionError, context: Optional[Dict] = None) -> None:
        """处理连接错误"""
        logger.error(f"存储连接失败: {error}")
        
        # 提供修复建议
        if context and 'backend_type' in context:
            logger.info(f"建议检查 {context['backend_type']} 存储后端的连接配置")
        
        logger.info("常见连接问题: 网络连接、权限问题、存储服务未启动")
    
    def _handle_validation_error(self, error: StorageValidationError, context: Optional[Dict] = None) -> None:
        """处理验证错误"""
        logger.warning(f"存储验证失败: {error}")
        
        # 提供修复建议
        if context and 'operation' in context:
            logger.info(f"建议检查 {context['operation']} 操作的输入参数")
        
        logger.info("常见验证问题: 数据格式、路径有效性、参数范围")
    
    def _handle_capacity_error(self, error: StorageCapacityError, context: Optional[Dict] = None) -> None:
         """处理容量错误"""
         logger.error(f"存储容量不足: {error}")
         
         # 提供容量管理建议 - 从details获取容量信息
         if hasattr(error, 'details') and error.details:
             required = error.details.get('required_size')
             available = error.details.get('available_size')
             if required is not None and available is not None:
                 logger.info(f"所需大小: {required}, 可用大小: {available}")
         
         logger.info("建议清理旧数据或扩展存储容量")
    
    def _handle_permission_error(self, error: StoragePermissionError, context: Optional[Dict] = None) -> None:
        """处理权限错误"""
        logger.error(f"存储权限不足: {error}")
        
        # 提供权限修复建议
        if context and 'base_path' in context:
            logger.info(f"建议检查路径 {context['base_path']} 的读写权限")
        
        logger.info("建议检查文件系统权限和用户访问控制")
    
    def _handle_timeout_error(self, error: StorageTimeoutError, context: Optional[Dict] = None) -> None:
        """处理超时错误"""
        logger.warning(f"存储操作超时: {error}")
        
        # 提供超时处理建议
        logger.info("建议增加超时时间或优化存储性能")
        logger.info("检查存储系统的负载和响应时间")
    
    def _handle_transaction_error(self, error: StorageTransactionError, context: Optional[Dict] = None) -> None:
        """处理事务错误"""
        logger.error(f"存储事务失败: {error}")
        
        # 提供事务修复建议
        logger.info("建议检查事务状态并回滚未完成的事务")
        logger.info("检查数据库锁定和并发控制")
    
    def _handle_configuration_error(self, error: StorageConfigurationError, context: Optional[Dict] = None) -> None:
        """处理配置错误"""
        logger.error(f"存储配置错误: {error}")
        
        # 提供配置修复建议
        logger.info("建议检查存储配置文件的格式和内容")
        logger.info("验证配置参数的有效性和兼容性")
    
    def _handle_migration_error(self, error: StorageMigrationError, context: Optional[Dict] = None) -> None:
        """处理迁移错误"""
        logger.error(f"存储迁移失败: {error}")
        
        # 提供迁移修复建议
        logger.info("建议检查数据兼容性和迁移脚本")
        logger.info("考虑备份数据后重新执行迁移")
    
    def _handle_serialization_error(self, error: StorageSerializationError, context: Optional[Dict] = None) -> None:
        """处理序列化错误"""
        logger.warning(f"存储序列化失败: {error}")
        
        # 提供序列化修复建议
        logger.info("建议检查数据格式和序列化器配置")
        logger.info("验证数据是否包含不可序列化的对象")
    
    def _handle_compression_error(self, error: StorageCompressionError, context: Optional[Dict] = None) -> None:
        """处理压缩错误"""
        logger.warning(f"存储压缩失败: {error}")
        
        # 提供压缩修复建议
        logger.info("建议检查压缩算法配置和数据完整性")
        logger.info("考虑禁用压缩或更换压缩算法")
    
    def _handle_encryption_error(self, error: StorageEncryptionError, context: Optional[Dict] = None) -> None:
        """处理加密错误"""
        logger.error(f"存储加密失败: {error}")
        
        # 提供加密修复建议
        logger.info("建议检查加密密钥和加密算法配置")
        logger.info("验证加密证书的有效性")
    
    def _handle_index_error(self, error: StorageIndexError, context: Optional[Dict] = None) -> None:
        """处理索引错误"""
        logger.warning(f"存储索引错误: {error}")
        
        # 提供索引修复建议
        logger.info("建议重建或优化存储索引")
        logger.info("检查索引配置和数据一致性")
    
    def _handle_backup_error(self, error: StorageBackupError, context: Optional[Dict] = None) -> None:
        """处理备份错误"""
        logger.error(f"存储备份失败: {error}")
        
        # 提供备份修复建议
        logger.info("建议检查备份路径和存储空间")
        logger.info("验证备份权限和备份配置")
    
    def _handle_lock_error(self, error: StorageLockError, context: Optional[Dict] = None) -> None:
        """处理锁定错误"""
        logger.warning(f"存储锁定错误: {error}")
        
        # 提供锁定修复建议
        logger.info("建议检查并发访问和锁定机制")
        logger.info("考虑释放死锁或等待锁定释放")
    
    def _handle_query_error(self, error: StorageQueryError, context: Optional[Dict] = None) -> None:
        """处理查询错误"""
        logger.warning(f"存储查询错误: {error}")
        
        # 提供查询修复建议
        logger.info("建议检查查询语法和数据结构")
        logger.info("验证查询参数的有效性")
    
    def _handle_health_error(self, error: StorageHealthError, context: Optional[Dict] = None) -> None:
        """处理健康检查错误"""
        logger.error(f"存储健康检查失败: {error}")
        
        # 提供健康检查修复建议
        logger.info("建议检查存储系统的整体状态")
        logger.info("监控存储性能和资源使用情况")
    
    def _handle_generic_storage_error(self, error: StorageError, context: Optional[Dict] = None) -> None:
        """处理通用存储错误"""
        logger.error(f"存储错误: {error}")
        
        # 提供通用建议
        if context and 'operation' in context:
            logger.info(f"失败的操作: {context['operation']}")
        
        logger.info("建议检查存储系统的状态和配置")
    
    def _log_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """记录存储错误日志"""
        error_info = {
            "category": self.error_category.value,
            "severity": self.error_severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        # 添加存储特定的错误信息
        if isinstance(error, StorageError):
            if hasattr(error, 'details') and error.details:
                error_info["error_details"] = error.details
        
        # 添加容量错误特定信息
        if isinstance(error, StorageCapacityError):
            if hasattr(error, 'details') and error.details:
                if 'required_size' in error.details:
                    error_info["required_size"] = error.details['required_size']
                if 'available_size' in error.details:
                    error_info["available_size"] = error.details['available_size']
        
        # 根据严重度选择日志级别
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"存储错误: {error_info}")
        elif self.error_severity == ErrorSeverity.MEDIUM:
            logger.warning(f"存储警告: {error_info}")
        else:
            logger.info(f"存储信息: {error_info}")


class StorageErrorRecovery:
    """存储错误恢复策略"""
    
    @staticmethod
    def retry_storage_operation(storage_operation_func, max_retries: int = 3):
        """重试存储操作"""
        return operation_with_retry(
            storage_operation_func,
            max_retries=max_retries,
            retryable_exceptions=(StorageConnectionError, StorageTimeoutError, IOError),
            context={"operation": "storage_operation"}
        )
    
    @staticmethod
    def fallback_to_memory_storage(primary_storage_func, memory_storage_func):
        """降级到内存存储"""
        try:
            return primary_storage_func()
        except (StorageConnectionError, StoragePermissionError) as e:
            logger.warning(f"主存储失败，降级到内存存储: {e}")
            return memory_storage_func()
    
    @staticmethod
    def validate_storage_path(storage_path: str) -> bool:
        """验证存储路径"""
        try:
            import os
            if not storage_path:
                return False
            
            # 检查路径长度
            if len(storage_path) > 260:  # Windows限制
                return False
            
            # 检查非法字符
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
            if any(char in storage_path for char in invalid_chars):
                return False
            
            # 检查路径是否存在或可创建
            if not os.path.exists(storage_path):
                try:
                    os.makedirs(storage_path, exist_ok=True)
                except OSError:
                    return False
            
            # 检查读写权限
            if not os.access(storage_path, os.R_OK | os.W_OK):
                return False
            
            return True
        except Exception as e:
            logger.error(f"存储路径验证失败: {e}")
            return False
    
    @staticmethod
    def cleanup_storage_storage(storage_manager, max_age_days: int = 30):
        """清理存储数据"""
        try:
            logger.info(f"开始清理超过 {max_age_days} 天的存储数据")
            # 实际实现取决于具体的存储管理器接口
            # deleted_count = await storage_manager.cleanup_old_data(max_age_days)
            # logger.info(f"清理完成，删除了 {deleted_count} 条记录")
        except Exception as e:
            logger.error(f"清理存储数据失败: {e}")


class StorageHealthChecker:
    """存储健康检查器"""
    
    @staticmethod
    def check_storage_health(storage_backend) -> Dict[str, Any]:
        """检查存储健康状态"""
        try:
            health_status = {
                "healthy": True,
                "issues": [],
                "metrics": {}
            }
            
            # 检查连接状态
            try:
                # 这里应该实现具体的连接检查
                # is_connected = storage_backend.is_connected()
                # health_status["metrics"]["connected"] = is_connected
                pass
            except Exception as e:
                health_status["healthy"] = False
                health_status["issues"].append(f"连接检查失败: {e}")
            
            # 检查可用空间
            try:
                # 这里应该实现空间检查
                # available_space = storage_backend.get_available_space()
                # health_status["metrics"]["available_space"] = available_space
                pass
            except Exception as e:
                health_status["issues"].append(f"空间检查失败: {e}")
            
            # 检查性能指标
            try:
                # 这里应该实现性能检查
                # response_time = storage_backend.get_response_time()
                # health_status["metrics"]["response_time"] = response_time
                pass
            except Exception as e:
                health_status["issues"].append(f"性能检查失败: {e}")
            
            return health_status
            
        except Exception as e:
            return {
                "healthy": False,
                "issues": [f"健康检查失败: {e}"],
                "metrics": {}
            }


# 注册存储错误处理器
def register_storage_error_handler():
    """注册存储错误处理器到全局注册表"""
    storage_handler = StorageErrorHandler()
    
    # 注册各种存储异常的处理器
    register_error_handler(StorageError, storage_handler)
    register_error_handler(StorageConnectionError, storage_handler)
    register_error_handler(StorageValidationError, storage_handler)
    register_error_handler(StorageNotFoundError, storage_handler)
    register_error_handler(StorageTimeoutError, storage_handler)
    register_error_handler(StorageCapacityError, storage_handler)
    register_error_handler(StoragePermissionError, storage_handler)
    register_error_handler(StorageConfigurationError, storage_handler)
    register_error_handler(StorageMigrationError, storage_handler)
    register_error_handler(StorageSerializationError, storage_handler)
    register_error_handler(StorageCompressionError, storage_handler)
    register_error_handler(StorageEncryptionError, storage_handler)
    register_error_handler(StorageIndexError, storage_handler)
    register_error_handler(StorageBackupError, storage_handler)
    register_error_handler(StorageLockError, storage_handler)
    register_error_handler(StorageQueryError, storage_handler)
    register_error_handler(StorageHealthError, storage_handler)
    
    logger.info("存储错误处理器已注册到全局注册表")


class StorageAdapterErrorHandler(IStorageErrorHandler):
    """存储适配器错误处理器
    
    实现IStorageErrorHandler接口，为存储适配器提供统一的错误处理。
    """
    
    def __init__(self, max_retries: int = 3):
        """初始化适配器错误处理器
        
        Args:
            max_retries: 最大重试次数
        """
        self.max_retries = max_retries
        self.logger = get_logger(self.__class__.__name__)
        self.storage_error_handler = StorageErrorHandler()
    
    async def handle(self, operation: str, operation_func: Callable) -> Any:
        """处理操作并统一异常
        
        Args:
            operation: 操作名称
            operation_func: 操作函数
            
        Returns:
            操作结果
            
        Raises:
            StorageError: 操作失败时抛出
        """
        context = {
            "operation": operation,
            "component": "storage_adapter",
            "max_retries": self.max_retries
        }
        
        # 定义可重试的异常类型
        retryable_exceptions = (
            StorageConnectionError,
            StorageTimeoutError,
            StorageLockError
        )
        
        try:
            # 使用重试机制执行操作
            if asyncio.iscoroutinefunction(operation_func):
                return await self._async_operation_with_retry(
                    operation_func, retryable_exceptions, context
                )
            else:
                return self._sync_operation_with_retry(
                    operation_func, retryable_exceptions, context
                )
        except Exception as e:
            # 使用存储错误处理器处理异常
            if isinstance(e, StorageError):
                self.storage_error_handler.handle(e, context)
            else:
                # 将非存储异常转换为存储异常
                storage_error = StorageError(f"适配器操作失败: {e}")
                self.storage_error_handler.handle(storage_error, context)
                raise storage_error from e
            raise
    
    async def _async_operation_with_retry(
        self,
        operation_func: Callable,
        retryable_exceptions: tuple,
        context: Dict[str, Any]
    ) -> Any:
        """异步操作重试实现"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await operation_func()
            except retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    self.logger.warning(
                        f"操作 {context['operation']} 失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(
                        f"操作 {context['operation']} 重试 {self.max_retries} 次后仍然失败: {e}"
                    )
            except Exception as e:
                # 非重试异常直接抛出
                raise
        
        # 重试次数用完，抛出最后一个异常
        if last_exception is not None:
            raise last_exception
        else:
            raise StorageError(f"操作 {context['operation']} 重试 {self.max_retries} 次后失败")
    
    def _sync_operation_with_retry(
        self,
        operation_func: Callable,
        retryable_exceptions: tuple,
        context: Dict[str, Any]
    ) -> Any:
        """同步操作重试实现"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation_func()
            except retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    self.logger.warning(
                        f"操作 {context['operation']} 失败，即将重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                else:
                    self.logger.error(
                        f"操作 {context['operation']} 重试 {self.max_retries} 次后仍然失败: {e}"
                    )
            except Exception as e:
                # 非重试异常直接抛出
                raise
        
        # 重试次数用完，抛出最后一个异常
        if last_exception is not None:
            raise last_exception
        else:
            raise StorageError(f"操作 {context['operation']} 重试 {self.max_retries} 次后失败")


# 自动注册
register_storage_error_handler()