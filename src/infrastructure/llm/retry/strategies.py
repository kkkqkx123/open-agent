"""重试策略实现"""

import time
import random
from typing import Optional, List, Callable, Any

from .interfaces import IRetryStrategy, IRetryLogger, IRetryCondition, IRetryDelayCalculator
from .retry_config import RetryConfig, RetryAttempt, RetrySession


class DefaultRetryLogger(IRetryLogger):
    """默认重试日志记录器"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化默认重试日志记录器
        
        Args:
            enabled: 是否启用日志记录
        """
        self.enabled = enabled
    
    def log_retry_attempt(self, func_name: str, error: Exception, attempt: int, delay: float) -> None:
        """
        记录重试尝试
        
        Args:
            func_name: 函数名称
            error: 发生的错误
            attempt: 尝试次数
            delay: 延迟时间
        """
        if not self.enabled:
            return
        
        print(f"[Retry] {func_name} 尝试 {attempt} 失败: {error}, {delay:.2f}秒后重试")
    
    def log_retry_success(self, func_name: str, result: Any, attempt: int) -> None:
        """
        记录重试成功
        
        Args:
            func_name: 函数名称
            result: 结果
            attempt: 尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Retry] {func_name} 在第 {attempt} 次尝试后成功")
    
    def log_retry_failure(self, func_name: str, error: Exception, total_attempts: int) -> None:
        """
        记录重试失败
        
        Args:
            func_name: 函数名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Retry] {func_name} 在 {total_attempts} 次尝试后失败: {error}")


class ExponentialBackoffStrategy(IRetryStrategy):
    """指数退避重试策略"""
    
    def __init__(self, config: RetryConfig, logger: Optional[IRetryLogger] = None):
        """
        初始化指数退避重试策略
        
        Args:
            config: 重试配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or DefaultRetryLogger()
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该重试
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该重试
        """
        # 检查是否达到最大尝试次数
        if attempt >= self.config.get_max_attempts():
            return False
        
        # 检查错误类型是否应该重试
        return self.config.should_retry_on_error(error)
    
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """
        获取重试延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        return self.config.calculate_delay(attempt)
    
    def on_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """
        重试尝试时的回调
        
        Args:
            error: 发生的错误
            attempt: 尝试次数
            delay: 延迟时间
        """
        self.logger.log_retry_attempt("function", error, attempt, delay)
    
    def on_retry_success(self, result: Any, attempt: int) -> None:
        """
        重试成功时的回调
        
        Args:
            result: 结果
            attempt: 尝试次数
        """
        self.logger.log_retry_success("function", result, attempt)
    
    def on_retry_failure(self, error: Exception, total_attempts: int) -> None:
        """
        重试失败时的回调
        
        Args:
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        self.logger.log_retry_failure("function", error, total_attempts)


class LinearBackoffStrategy(IRetryStrategy):
    """线性退避重试策略"""
    
    def __init__(self, config: RetryConfig, logger: Optional[IRetryLogger] = None):
        """
        初始化线性退避重试策略
        
        Args:
            config: 重试配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or DefaultRetryLogger()
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.get_max_attempts():
            return False
        return self.config.should_retry_on_error(error)
    
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """获取重试延迟时间"""
        delay = self.config.base_delay * attempt
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def on_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """重试尝试时的回调"""
        self.logger.log_retry_attempt("function", error, attempt, delay)
    
    def on_retry_success(self, result: Any, attempt: int) -> None:
        """重试成功时的回调"""
        self.logger.log_retry_success("function", result, attempt)
    
    def on_retry_failure(self, error: Exception, total_attempts: int) -> None:
        """重试失败时的回调"""
        self.logger.log_retry_failure("function", error, total_attempts)


class FixedDelayStrategy(IRetryStrategy):
    """固定延迟重试策略"""
    
    def __init__(self, config: RetryConfig, logger: Optional[IRetryLogger] = None):
        """
        初始化固定延迟重试策略
        
        Args:
            config: 重试配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or DefaultRetryLogger()
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.get_max_attempts():
            return False
        return self.config.should_retry_on_error(error)
    
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """获取重试延迟时间"""
        delay = self.config.base_delay
        
        if self.config.jitter:
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def on_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """重试尝试时的回调"""
        self.logger.log_retry_attempt("function", error, attempt, delay)
    
    def on_retry_success(self, result: Any, attempt: int) -> None:
        """重试成功时的回调"""
        self.logger.log_retry_success("function", result, attempt)
    
    def on_retry_failure(self, error: Exception, total_attempts: int) -> None:
        """重试失败时的回调"""
        self.logger.log_retry_failure("function", error, total_attempts)


class AdaptiveRetryStrategy(IRetryStrategy):
    """自适应重试策略"""
    
    def __init__(self, config: RetryConfig, logger: Optional[IRetryLogger] = None):
        """
        初始化自适应重试策略
        
        Args:
            config: 重试配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or DefaultRetryLogger()
        self._error_history: List[Exception] = []
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.get_max_attempts():
            return False
        
        # 记录错误历史
        self._error_history.append(error)
        
        # 根据错误模式调整重试策略
        return self.config.should_retry_on_error(error)
    
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """获取重试延迟时间"""
        # 基础延迟
        delay = self.config.calculate_delay(attempt)
        
        # 根据错误类型调整延迟
        error_type = type(error).__name__
        
        # 某些错误类型需要更长的延迟
        if "RateLimit" in error_type or "rate_limit" in str(error).lower():
            delay *= 2  # 频率限制错误需要更长延迟
        elif "Timeout" in error_type or "timeout" in str(error).lower():
            delay *= 1.5  # 超时错误需要稍长延迟
        
        # 如果连续出现相同错误，增加延迟
        if len(self._error_history) >= 2:
            last_error = self._error_history[-1]
            prev_error = self._error_history[-2]
            if type(last_error) == type(prev_error):
                delay *= 1.2
        
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def on_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """重试尝试时的回调"""
        self.logger.log_retry_attempt("function", error, attempt, delay)
    
    def on_retry_success(self, result: Any, attempt: int) -> None:
        """重试成功时的回调"""
        # 清空错误历史
        self._error_history.clear()
        self.logger.log_retry_success("function", result, attempt)
    
    def on_retry_failure(self, error: Exception, total_attempts: int) -> None:
        """重试失败时的回调"""
        self.logger.log_retry_failure("function", error, total_attempts)


class ConditionalRetryStrategy(IRetryStrategy):
    """条件重试策略"""
    
    def __init__(self, config: RetryConfig, conditions: List[IRetryCondition], 
                 logger: Optional[IRetryLogger] = None):
        """
        初始化条件重试策略
        
        Args:
            config: 重试配置
            conditions: 重试条件列表
            logger: 日志记录器
        """
        self.config = config
        self.conditions = conditions
        self.logger = logger or DefaultRetryLogger()
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.get_max_attempts():
            return False
        
        # 检查所有条件
        for condition in self.conditions:
            if not condition.should_retry(error, attempt):
                return False
        
        return self.config.should_retry_on_error(error)
    
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """获取重试延迟时间"""
        return self.config.calculate_delay(attempt)
    
    def on_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """重试尝试时的回调"""
        self.logger.log_retry_attempt("function", error, attempt, delay)
    
    def on_retry_success(self, result: Any, attempt: int) -> None:
        """重试成功时的回调"""
        self.logger.log_retry_success("function", result, attempt)
    
    def on_retry_failure(self, error: Exception, total_attempts: int) -> None:
        """重试失败时的回调"""
        self.logger.log_retry_failure("function", error, total_attempts)


def create_retry_strategy(config: RetryConfig, logger: Optional[IRetryLogger] = None, 
                         **kwargs) -> IRetryStrategy:
    """
    创建重试策略
    
    Args:
        config: 重试配置
        logger: 日志记录器
        **kwargs: 策略特定参数
        
    Returns:
        重试策略实例
    """
    strategy_type = config.strategy_type.lower()
    
    if strategy_type == "exponential_backoff":
        return ExponentialBackoffStrategy(config, logger)
    elif strategy_type == "linear":
        return LinearBackoffStrategy(config, logger)
    elif strategy_type == "fixed":
        return FixedDelayStrategy(config, logger)
    elif strategy_type == "adaptive":
        return AdaptiveRetryStrategy(config, logger)
    elif strategy_type == "conditional":
        return ConditionalRetryStrategy(config, kwargs.get("conditions", []), logger)
    else:
        raise ValueError(f"不支持的重试策略类型: {strategy_type}")


class StatusCodeRetryCondition(IRetryCondition):
    """状态码重试条件"""
    
    def __init__(self, retry_status_codes: List[int]):
        """
        初始化状态码重试条件
        
        Args:
            retry_status_codes: 需要重试的状态码列表
        """
        self.retry_status_codes = retry_status_codes
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            return error.response.status_code in self.retry_status_codes
        return True


class ErrorTypeRetryCondition(IRetryCondition):
    """错误类型重试条件"""
    
    def __init__(self, retry_error_types: List[str], block_error_types: List[str] = None):
        """
        初始化错误类型重试条件
        
        Args:
            retry_error_types: 需要重试的错误类型列表
            block_error_types: 不重试的错误类型列表
        """
        self.retry_error_types = retry_error_types
        self.block_error_types = block_error_types or []
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        error_type = type(error).__name__
        error_str = str(error).lower()
        
        # 检查是否在阻塞列表中
        for block_type in self.block_error_types:
            if block_type in error_type or block_type in error_str:
                return False
        
        # 检查是否在重试列表中
        for retry_type in self.retry_error_types:
            if retry_type in error_type or retry_type in error_str:
                return True
        
        return True