"""错误处理器接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .error_category import ErrorCategory
from .error_severity import ErrorSeverity


class IErrorHandler(ABC):
    """错误处理器接口"""
    
    @abstractmethod
    def can_handle(self, error: Exception) -> bool:
        """是否可以处理该错误
        
        Args:
            error: 异常对象
            
        Returns:
            是否可以处理
        """
        pass
    
    @abstractmethod
    def handle(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        pass


class BaseErrorHandler(IErrorHandler):
    """基础错误处理器"""
    
    def __init__(
        self, 
        error_category: ErrorCategory,
        error_severity: ErrorSeverity
    ):
        """初始化基础错误处理器
        
        Args:
            error_category: 错误分类
            error_severity: 错误严重度
        """
        self.error_category = error_category
        self.error_severity = error_severity
    
    def can_handle(self, error: Exception) -> bool:
        """默认实现：可以处理所有错误"""
        return True
    
    def handle(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """基础错误处理实现
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        # 记录错误日志
        self._log_error(error, context)
        
        # 根据严重度决定是否抛出异常
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error
    
    def _log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        from src.interfaces.dependency_injection import get_logger
        
        logger = get_logger(__name__)
        
        error_info = {
            "category": self.error_category.value,
            "severity": self.error_severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        # 根据严重度选择日志级别
        if self.error_severity == ErrorSeverity.CRITICAL:
            logger.critical(f"严重错误: {error_info}", exc_info=True)
        elif self.error_severity == ErrorSeverity.HIGH:
            logger.error(f"高级错误: {error_info}", exc_info=True)
        elif self.error_severity == ErrorSeverity.MEDIUM:
            logger.warning(f"中级错误: {error_info}")
        elif self.error_severity == ErrorSeverity.LOW:
            logger.info(f"低级错误: {error_info}")
        else:  # INFO
            logger.debug(f"信息性错误: {error_info}")