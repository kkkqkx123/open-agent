"""重试接口定义"""

from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, List, Dict
from datetime import datetime


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
    
    @abstractmethod
    def log_retry_success(self, func_name: str, result: Any, attempt: int) -> None:
        """
        记录重试成功
        
        Args:
            func_name: 函数名称
            result: 结果
            attempt: 尝试次数
        """
        pass
    
    @abstractmethod
    def log_retry_failure(self, func_name: str, error: Exception, total_attempts: int) -> None:
        """
        记录重试失败
        
        Args:
            func_name: 函数名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        pass


class IRetryCondition(ABC):
    """重试条件接口"""
    
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


class IRetryDelayCalculator(ABC):
    """重试延迟计算器接口"""
    
    @abstractmethod
    def calculate_delay(self, attempt: int, base_delay: float, **kwargs) -> float:
        """
        计算重试延迟
        
        Args:
            attempt: 尝试次数
            base_delay: 基础延迟时间
            **kwargs: 其他参数
            
        Returns:
            延迟时间（秒）
        """
        pass


class IRetryContext:
    """重试上下文接口"""
    
    @abstractmethod
    def get_attempt_count(self) -> int:
        """获取当前尝试次数"""
        pass
    
    @abstractmethod
    def get_total_attempts(self) -> int:
        """获取总尝试次数"""
        pass
    
    @abstractmethod
    def get_start_time(self) -> datetime:
        """获取开始时间"""
        pass
    
    @abstractmethod
    def get_last_error(self) -> Optional[Exception]:
        """获取最后一次错误"""
        pass
    
    @abstractmethod
    def get_elapsed_time(self) -> float:
        """获取已用时间（秒）"""
        pass