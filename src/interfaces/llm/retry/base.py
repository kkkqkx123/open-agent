"""LLM重试管理接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IRetryStrategy(ABC):
    """重试策略接口"""
    
    @abstractmethod
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该重试
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该重试
        """
        pass
    
    @abstractmethod
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """
        获取重试延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        pass
    
    @abstractmethod
    def on_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """
        重试尝试时的回调
        
        Args:
            error: 发生的错误
            attempt: 尝试次数
            delay: 延迟时间
        """
        pass
    
    @abstractmethod
    def on_retry_success(self, result: Any, attempt: int) -> None:
        """
        重试成功时的回调
        
        Args:
            result: 结果
            attempt: 尝试次数
        """
        pass
    
    @abstractmethod
    def on_retry_failure(self, error: Exception, total_attempts: int) -> None:
        """
        重试失败时的回调
        
        Args:
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        pass


class IRetryLogger(ABC):
    """重试日志记录器接口"""
    
    @abstractmethod
    def log_retry_attempt(self, func_name: str, error: Exception, attempt: int, delay: float) -> None:
        """
        记录重试尝试
        
        Args:
            func_name: 函数名称
            error: 发生的错误
            attempt: 尝试次数
            delay: 延迟时间
        """
        pass