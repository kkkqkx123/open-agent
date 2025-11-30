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
        # 这里需要导入logger，但为了避免循环依赖，我们稍后实现
        # 暂时使用print作为占位符
        error_info = {
            "category": self.error_category.value,
            "severity": self.error_severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        print(f"错误处理: {error_info}")