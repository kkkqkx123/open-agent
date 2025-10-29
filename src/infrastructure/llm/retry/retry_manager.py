"""重试管理器"""

import time
import asyncio
import functools
from typing import Any, Callable, Optional, Dict, List, Union
from concurrent.futures import TimeoutError

from .interfaces import IRetryStrategy, IRetryLogger
from .retry_config import RetryConfig, RetryAttempt, RetrySession, RetryStats
from .strategies import create_retry_strategy, DefaultRetryLogger


class RetryManager:
    """重试管理器"""
    
    def __init__(self, config: RetryConfig, logger: Optional[IRetryLogger] = None):
        """
        初始化重试管理器
        
        Args:
            config: 重试配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or DefaultRetryLogger()
        self._strategy = create_retry_strategy(config, logger)
        self._sessions: List[RetrySession] = []
        self._stats = RetryStats()
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        带重试的同步执行
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        if not self.config.is_enabled():
            return func(*args, **kwargs)
        
        # 创建重试会话
        session = RetrySession(
            func_name=func.__name__,
            start_time=time.time()
        )
        
        try:
            attempt = 0
            last_error = None
            
            while self.config.should_continue_retry(attempt, session.start_time):
                attempt += 1
                
                # 创建尝试记录
                retry_attempt = RetryAttempt(
                    attempt_number=attempt,
                    error=None,
                    timestamp=time.time()
                )
                
                try:
                    # 计算延迟（除了第一次尝试）
                    if attempt > 1 and last_error:
                        delay = self._strategy.get_retry_delay(last_error, attempt)
                        retry_attempt.delay = delay
                        if delay > 0:
                            time.sleep(delay)
                    
                    # 执行函数
                    start_time = time.time()
                    
                    # 如果有每次尝试的超时设置，使用超时执行
                    if self.config.per_attempt_timeout is not None:
                        result = self._execute_with_timeout(
                            func, self.config.per_attempt_timeout, *args, **kwargs
                        )
                    else:
                        result = func(*args, **kwargs)
                    
                    # 成功
                    retry_attempt.success = True
                    retry_attempt.result = result
                    retry_attempt.duration = time.time() - start_time
                    
                    session.add_attempt(retry_attempt)
                    session.mark_success(result)
                    
                    # 更新统计
                    self._stats.update(session)
                    
                    # 调用成功回调
                    self._strategy.on_retry_success(result, attempt)
                    
                    return result
                    
                except Exception as e:
                    # 失败
                    last_error = e
                    retry_attempt.error = e
                    if 'start_time' in locals():
                        retry_attempt.duration = time.time() - start_time
                    
                    session.add_attempt(retry_attempt)
                    
                    # 调用尝试回调
                    delay = self._strategy.get_retry_delay(e, attempt)
                    self._strategy.on_retry_attempt(e, attempt, delay)
                    
                    # 检查是否应该继续重试
                    if not self._strategy.should_retry(e, attempt):
                        break
            
            # 所有尝试都失败
            session.mark_failure(last_error)
            self._stats.update(session)
            
            # 调用失败回调
            self._strategy.on_retry_failure(last_error, attempt)
            
            # 抛出最后的错误
            raise last_error
            
        finally:
            # 记录会话
            self._sessions.append(session)
    
    async def execute_with_retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        带重试的异步执行
        
        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        if not self.config.is_enabled():
            return await func(*args, **kwargs)
        
        # 创建重试会话
        session = RetrySession(
            func_name=func.__name__,
            start_time=time.time()
        )
        
        try:
            attempt = 0
            last_error = None
            
            while self.config.should_continue_retry(attempt, session.start_time):
                attempt += 1
                
                # 创建尝试记录
                retry_attempt = RetryAttempt(
                    attempt_number=attempt,
                    error=None,
                    timestamp=time.time()
                )
                
                try:
                    # 计算延迟（除了第一次尝试）
                    if attempt > 1 and last_error:
                        delay = self._strategy.get_retry_delay(last_error, attempt)
                        retry_attempt.delay = delay
                        if delay > 0:
                            await asyncio.sleep(delay)
                    
                    # 执行异步函数
                    start_time = time.time()
                    
                    # 如果有每次尝试的超时设置，使用超时执行
                    if self.config.per_attempt_timeout is not None:
                        result = await self._execute_with_timeout_async(
                            func, self.config.per_attempt_timeout, *args, **kwargs
                        )
                    else:
                        result = await func(*args, **kwargs)
                    
                    # 成功
                    retry_attempt.success = True
                    retry_attempt.result = result
                    retry_attempt.duration = time.time() - start_time
                    
                    session.add_attempt(retry_attempt)
                    session.mark_success(result)
                    
                    # 更新统计
                    self._stats.update(session)
                    
                    # 调用成功回调
                    self._strategy.on_retry_success(result, attempt)
                    
                    return result
                    
                except Exception as e:
                    # 失败
                    last_error = e
                    retry_attempt.error = e
                    if 'start_time' in locals():
                        retry_attempt.duration = time.time() - start_time
                    
                    session.add_attempt(retry_attempt)
                    
                    # 调用尝试回调
                    delay = self._strategy.get_retry_delay(e, attempt)
                    self._strategy.on_retry_attempt(e, attempt, delay)
                    
                    # 检查是否应该继续重试
                    if not self._strategy.should_retry(e, attempt):
                        break
            
            # 所有尝试都失败
            session.mark_failure(last_error)
            self._stats.update(session)
            
            # 调用失败回调
            self._strategy.on_retry_failure(last_error, attempt)
            
            # 抛出最后的错误
            raise last_error
            
        finally:
            # 记录会话
            self._sessions.append(session)
    
    def _execute_with_timeout(self, func: Callable, timeout: float, *args, **kwargs) -> Any:
        """
        带超时的同步执行
        
        Args:
            func: 要执行的函数
            timeout: 超时时间（秒）
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            TimeoutError: 超时
        """
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"函数执行超时（{timeout}秒）")
        
        # 设置超时信号
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # 恢复原始信号处理器
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    async def _execute_with_timeout_async(self, func: Callable, timeout: float, *args, **kwargs) -> Any:
        """
        带超时的异步执行
        
        Args:
            func: 要执行的异步函数
            timeout: 超时时间（秒）
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            TimeoutError: 超时
        """
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"异步函数执行超时（{timeout}秒）")
    
    def retry(self, func: Callable = None, *, config: Optional[RetryConfig] = None) -> Union[Callable, Any]:
        """
        重试装饰器
        
        Args:
            func: 要装饰的函数
            config: 重试配置（可选）
            
        Returns:
            装饰后的函数或装饰器
        """
        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # 使用提供的配置或默认配置
                retry_config = config or self.config
                retry_manager = RetryManager(retry_config, self.logger)
                return retry_manager.execute_with_retry(f, *args, **kwargs)
            
            @functools.wraps(f)
            async def async_wrapper(*args, **kwargs):
                # 使用提供的配置或默认配置
                retry_config = config or self.config
                retry_manager = RetryManager(retry_config, self.logger)
                return await retry_manager.execute_with_retry_async(f, *args, **kwargs)
            
            # 根据函数是否是协程函数返回对应的包装器
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper
        
        # 如果直接装饰函数，返回装饰后的函数
        if func is not None:
            return decorator(func)
        
        # 否则返回装饰器
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取重试统计信息
        
        Returns:
            统计信息字典
        """
        stats_dict = self._stats.to_dict()
        stats_dict["config"] = self.config.to_dict()
        stats_dict["total_sessions"] = len(self._sessions)
        
        # 添加最近的会话信息
        if self._sessions:
            recent_sessions = self._sessions[-10:]  # 最近10个会话
            stats_dict["recent_sessions"] = [s.to_dict() for s in recent_sessions]
        
        return stats_dict
    
    def get_sessions(self, limit: Optional[int] = None) -> List[RetrySession]:
        """
        获取重试会话记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            会话记录列表
        """
        sessions = self._sessions.copy()
        if limit:
            sessions = sessions[-limit:]
        return sessions
    
    def clear_sessions(self) -> None:
        """清空会话记录"""
        self._sessions.clear()
        self._stats = RetryStats()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = RetryStats()
    
    def is_enabled(self) -> bool:
        """检查重试是否启用"""
        return self.config.is_enabled()
    
    def update_config(self, config: RetryConfig) -> None:
        """
        更新重试配置
        
        Args:
            config: 新的重试配置
        """
        self.config = config
        self._strategy = create_retry_strategy(config, self.logger)


# 全局重试管理器实例
_global_retry_manager: Optional[RetryManager] = None


def get_global_retry_manager() -> RetryManager:
    """获取全局重试管理器"""
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = RetryManager(RetryConfig())
    return _global_retry_manager


def set_global_retry_manager(manager: RetryManager) -> None:
    """设置全局重试管理器"""
    global _global_retry_manager
    _global_retry_manager = manager


def retry(config: Optional[RetryConfig] = None) -> Callable:
    """
    全局重试装饰器
    
    Args:
        config: 重试配置
        
    Returns:
        装饰器
    """
    return get_global_retry_manager().retry(config=config)