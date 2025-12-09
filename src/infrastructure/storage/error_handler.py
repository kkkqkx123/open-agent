"""存储错误处理器

提供统一的存储错误处理机制。
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional, Type
from src.interfaces.storage.exceptions import StorageError, StorageConnectionError, StorageTimeoutError


class StorageErrorHandler:
    """存储错误处理器
    
    提供统一的错误处理、重试机制和错误分类功能。
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        timeout: Optional[float] = None
    ) -> None:
        """初始化错误处理器
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            backoff_factor: 退避因子
            timeout: 操作超时时间（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self._error_stats: Dict[str, Dict[str, int]] = {}
    
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
        # 初始化错误统计
        if operation not in self._error_stats:
            self._error_stats[operation] = {
                "total_attempts": 0,
                "successes": 0,
                "failures": 0,
                "retries": 0
            }
        
        last_exception = None
        current_delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            self._error_stats[operation]["total_attempts"] += 1
            
            try:
                # 应用超时
                if self.timeout:
                    result = await asyncio.wait_for(
                        operation_func(), 
                        timeout=self.timeout
                    )
                else:
                    result = await operation_func()
                
                # 成功，更新统计
                self._error_stats[operation]["successes"] += 1
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = StorageTimeoutError(
                    f"Operation {operation} timed out after {self.timeout}s"
                )
                
            except StorageConnectionError as e:
                last_exception = e
                # 连接错误通常可以重试
                
            except StorageError as e:
                last_exception = e
                # 其他存储错误可能不适合重试
                if not self._should_retry(e):
                    break
                    
            except Exception as e:
                last_exception = StorageError(
                    f"Unexpected error in {operation}: {e}"
                )
            
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries:
                self._error_stats[operation]["retries"] += 1
                await asyncio.sleep(current_delay)
                current_delay *= self.backoff_factor
        
        # 所有尝试都失败
        self._error_stats[operation]["failures"] += 1
        if last_exception is None:
            raise StorageError(f"Operation {operation} failed after {self.max_retries + 1} attempts")
        raise last_exception
    
    def _should_retry(self, error: StorageError) -> bool:
        """判断是否应该重试错误
        
        Args:
            error: 存储错误
            
        Returns:
            是否应该重试
        """
        # 某些错误类型不适合重试
        non_retryable_errors = [
            "PermissionError",
            "ValidationError",
            "NotFoundError"
        ]
        
        error_type = type(error).__name__
        return error_type not in non_retryable_errors
    
    def get_error_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取错误统计信息
        
        Args:
            operation: 操作名称，None表示获取所有操作统计
            
        Returns:
            错误统计信息
        """
        if operation:
            return self._error_stats.get(operation, {})
        
        return self._error_stats.copy()
    
    def reset_error_stats(self, operation: Optional[str] = None) -> None:
        """重置错误统计
        
        Args:
            operation: 操作名称，None表示重置所有统计
        """
        if operation:
            self._error_stats.pop(operation, None)
        else:
            self._error_stats.clear()


class StorageErrorClassifier:
    """存储错误分类器
    
    对存储错误进行分类和标记，便于错误处理和监控。
    """
    
    # 错误类别映射
    ERROR_CATEGORIES = {
        "connection": [
            StorageConnectionError,
            ConnectionError,
            ConnectionRefusedError,
        ],
        "timeout": [
            StorageTimeoutError,
            asyncio.TimeoutError,
        ],
        "permission": [
            PermissionError,
        ],
        "not_found": [
            FileNotFoundError,
            KeyError,
        ],
        "validation": [
            ValueError,
            TypeError,
        ],
        "resource": [
            MemoryError,
            OSError,
        ],
    }
    
    @classmethod
    def classify_error(cls, error: Exception) -> str:
        """分类错误
        
        Args:
            error: 异常对象
            
        Returns:
            错误类别
        """
        error_type = type(error)
        
        for category, error_types in cls.ERROR_CATEGORIES.items():
            if any(issubclass(error_type, et) for et in error_types):
                return category
        
        return "unknown"
    
    @classmethod
    def is_retryable(cls, error: Exception) -> bool:
        """判断错误是否可重试
        
        Args:
            error: 异常对象
            
        Returns:
            是否可重试
        """
        category = cls.classify_error(error)
        
        # 连接和超时错误通常可以重试
        retryable_categories = ["connection", "timeout"]
        
        return category in retryable_categories
    
    @classmethod
    def get_severity(cls, error: Exception) -> str:
        """获取错误严重程度
        
        Args:
            error: 异常对象
            
        Returns:
            错误严重程度：low, medium, high, critical
        """
        category = cls.classify_error(error)
        
        severity_map = {
            "connection": "high",
            "timeout": "medium",
            "permission": "high",
            "not_found": "low",
            "validation": "medium",
            "resource": "critical",
            "unknown": "medium",
        }
        
        return severity_map.get(category, "medium")