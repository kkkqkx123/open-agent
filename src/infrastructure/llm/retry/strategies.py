"""重试策略基础设施模块

提供多种重试策略的实现，支持不同的延迟计算和重试逻辑。
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Any, Callable, Awaitable
from .retry_config import RetryConfig, RetrySession, RetryAttempt


class RetryStrategy(ABC):
    """重试策略基类"""
    
    @abstractmethod
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算重试延迟时间"""
        pass
    
    @abstractmethod
    def should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """指数退避策略"""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算指数退避延迟"""
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        return attempt < config.max_attempts and config.should_retry_on_error(error)


class LinearBackoffStrategy(RetryStrategy):
    """线性退避策略"""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算线性退避延迟"""
        delay = config.base_delay * attempt
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        return attempt < config.max_attempts and config.should_retry_on_error(error)


class FixedDelayStrategy(RetryStrategy):
    """固定延迟策略"""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算固定延迟"""
        delay = config.base_delay
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        return attempt < config.max_attempts and config.should_retry_on_error(error)


class AdaptiveStrategy(RetryStrategy):
    """自适应策略"""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算自适应延迟"""
        # 基础指数退避
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay = min(delay, config.max_delay)
        
        # 可以根据错误类型进一步调整
        # 这里可以扩展更复杂的自适应逻辑
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        return attempt < config.max_attempts and config.should_retry_on_error(error)


def create_retry_strategy(config: RetryConfig) -> RetryStrategy:
    """创建重试策略实例
    
    Args:
        config: 重试配置
        
    Returns:
        重试策略实例
    """
    strategy_map = {
        config.strategy.EXPONENTIAL_BACKOFF: ExponentialBackoffStrategy,
        config.strategy.LINEAR_BACKOFF: LinearBackoffStrategy,
        config.strategy.FIXED_DELAY: FixedDelayStrategy,
        config.strategy.ADAPTIVE: AdaptiveStrategy,
    }
    
    strategy_class = strategy_map.get(config.strategy, ExponentialBackoffStrategy)
    return strategy_class()


class RetryContext:
    """重试上下文管理器"""
    
    def __init__(self, config: RetryConfig, func_name: str):
        self.config = config
        self.func_name = func_name
        self.session = None
        self.strategy = create_retry_strategy(config)
    
    def __enter__(self):
        self.session = RetrySession(
            func_name=self.func_name,
            start_time=time.time()
        )
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is None:
                self.session.mark_success(None)
            else:
                self.session.mark_failure(exc_val)
        return False  # 不抑制异常


class AsyncRetryContext:
    """异步重试上下文管理器"""
    
    def __init__(self, config: RetryConfig, func_name: str):
        self.config = config
        self.func_name = func_name
        self.session = None
        self.strategy = create_retry_strategy(config)
    
    async def __aenter__(self):
        self.session = RetrySession(
            func_name=self.func_name,
            start_time=time.time()
        )
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is None:
                self.session.mark_success(None)
            else:
                self.session.mark_failure(exc_val)
        return False  # 不抑制异常


def retry_with_config(config: RetryConfig):
    """重试装饰器
    
    Args:
        config: 重试配置
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not config.is_enabled():
                return func(*args, **kwargs)
            
            with RetryContext(config, func.__name__) as session:
                attempt = 0
                start_time = time.time()
                last_attempt = None
                
                while config.should_continue_retry(attempt, start_time):
                    attempt += 1
                    
                    # 计算延迟
                    delay = 0.0
                    if attempt > 1:
                        delay = config.calculate_delay(attempt)
                        if delay > 0:
                            time.sleep(delay)
                    
                    # 创建尝试记录
                    retry_attempt = RetryAttempt(
                        attempt_number=attempt,
                        error=None,
                        timestamp=time.time(),
                        delay=delay,
                        success=False
                    )
                    last_attempt = retry_attempt
                    start_attempt = time.time()
                    
                    try:
                        # 执行函数
                        result = func(*args, **kwargs)
                        
                        # 成功
                        retry_attempt.success = True
                        retry_attempt.result = result
                        retry_attempt.duration = time.time() - start_attempt
                        session.add_attempt(retry_attempt)
                        session.mark_success(result)
                        
                        return result
                        
                    except Exception as e:
                        # 失败
                        retry_attempt.error = e
                        retry_attempt.duration = time.time() - start_attempt
                        session.add_attempt(retry_attempt)
                        
                        # 检查是否应该继续重试
                        if not config.should_retry_on_error(e):
                            break
                
                # 所有尝试都失败
                if last_attempt and last_attempt.error:
                    session.mark_failure(last_attempt.error)
                    raise last_attempt.error
                else:
                    # 如果没有错误信息，创建一个通用异常
                    error = Exception("All retry attempts failed")
                    session.mark_failure(error)
                    raise error
        
        return wrapper
    
    return decorator


def async_retry_with_config(config: RetryConfig):
    """异步重试装饰器
    
    Args:
        config: 重试配置
        
    Returns:
        异步装饰器函数
    """
    def decorator(func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        async def wrapper(*args, **kwargs):
            if not config.is_enabled():
                return await func(*args, **kwargs)
            
            async with AsyncRetryContext(config, func.__name__) as session:
                attempt = 0
                start_time = time.time()
                last_attempt = None
                
                while config.should_continue_retry(attempt, start_time):
                    attempt += 1
                    
                    # 计算延迟
                    delay = 0.0
                    if attempt > 1:
                        delay = config.calculate_delay(attempt)
                        if delay > 0:
                            await asyncio.sleep(delay)
                    
                    # 创建尝试记录
                    retry_attempt = RetryAttempt(
                        attempt_number=attempt,
                        error=None,
                        timestamp=time.time(),
                        delay=delay,
                        success=False
                    )
                    last_attempt = retry_attempt
                    start_attempt = time.time()
                    
                    try:
                        # 执行函数
                        result = await func(*args, **kwargs)
                        
                        # 成功
                        retry_attempt.success = True
                        retry_attempt.result = result
                        retry_attempt.duration = time.time() - start_attempt
                        session.add_attempt(retry_attempt)
                        session.mark_success(result)
                        
                        return result
                        
                    except Exception as e:
                        # 失败
                        retry_attempt.error = e
                        retry_attempt.duration = time.time() - start_attempt
                        session.add_attempt(retry_attempt)
                        
                        # 检查是否应该继续重试
                        if not config.should_retry_on_error(e):
                            break
                
                # 所有尝试都失败
                if last_attempt and last_attempt.error:
                    session.mark_failure(last_attempt.error)
                    raise last_attempt.error
                else:
                    # 如果没有错误信息，创建一个通用异常
                    error = Exception("All retry attempts failed")
                    session.mark_failure(error)
                    raise error
        
        return wrapper
    
    return decorator