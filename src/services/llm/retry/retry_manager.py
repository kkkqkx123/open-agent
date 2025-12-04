"""重试管理器"""

import time
import asyncio
import functools
from typing import Any, Callable, Optional, Dict, List, Union
from concurrent.futures import TimeoutError

from src.interfaces.llm import IRetryLogger
# 从基础设施层导入重试配置和策略
from src.infrastructure.llm.retry import RetryConfig, RetryAttempt, RetrySession, RetryStats, create_retry_strategy
from .strategies import DefaultRetryLogger


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
        self._strategy = create_retry_strategy(config)
        self._sessions: List[RetrySession] = []
        self._stats = RetryStats()
    
    def execute_with_retry(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
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
        func_name = getattr(func, '__name__', str(func))
        session = RetrySession(
            func_name=func_name,
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
                
                # 初始化开始时间
                start_time = time.time()
                
                try:
                    
                    # 计算延迟（除了第一次尝试）
                    if attempt > 1 and last_error:
                        delay = self._strategy.get_retry_delay(last_error, attempt)
                        retry_attempt.delay = delay
                        if delay > 0:
                            time.sleep(delay)
                    
                    # 执行函数
                    
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
                    # 确保start_time已定义
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
            if last_error is not None:
                session.mark_failure(last_error)
                self._stats.update(session)
                
                # 调用失败回调
                self._strategy.on_retry_failure(last_error, attempt)
                
                # 抛出最后的错误
                raise last_error
            else:
                # 如果没有错误发生但仍被认为是失败，创建一个默认错误
                error = Exception("Retry failed without specific error")
                session.mark_failure(error)
                self._stats.update(session)
                
                # 调用失败回调
                self._strategy.on_retry_failure(error, attempt)
                
                # 抛出错误
                raise error
            
        finally:
            # 记录会话
            self._sessions.append(session)
    
    async def execute_with_retry_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
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
        func_name = getattr(func, '__name__', str(func))
        session = RetrySession(
            func_name=func_name,
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
                
                # 初始化开始时间
                start_time = time.time()
                
                try:
                    
                    # 计算延迟（除了第一次尝试）
                    if attempt > 1 and last_error:
                        delay = self._strategy.get_retry_delay(last_error, attempt)
                        retry_attempt.delay = delay
                        if delay > 0:
                            await asyncio.sleep(delay)
                    
                    # 执行异步函数
                    
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
                    # 确保start_time已定义
                    if 'start_time' in locals():
                        retry_attempt.duration = time.time() - start_time
                    
                    session.add_attempt(retry_attempt)
                    
                    # 调用尝试回调
                    delay = self._strategy.get_retry_delay(e, attempt)
                    self._strategy.on_retry_attempt(e, attempt, delay)
                    
                    # 检查是否应该继续重试
                    if not self._strategy.should_retry(e, attempt):
                        break
                    
                    # 检查是否达到了最大尝试次数
                    if attempt >= self.config.get_max_attempts():
                        break
                    
                    # 继续下一次尝试
                    continue
            
            # 所有尝试都失败
            if last_error is not None:
                session.mark_failure(last_error)
                self._stats.update(session)
                
                # 调用失败回调
                self._strategy.on_retry_failure(last_error, attempt)
                
                # 抛出最后的错误
                raise last_error
            else:
                # 如果没有错误发生但仍被认为是失败，创建一个默认错误
                error = Exception("Retry failed without specific error")
                session.mark_failure(error)
                self._stats.update(session)
                
                # 调用失败回调
                self._strategy.on_retry_failure(error, attempt)
                
                # 抛出错误
                raise error
            
        finally:
            # 记录会话
            self._sessions.append(session)
    
    def _execute_with_timeout(self, func: Callable[..., Any], timeout: float, *args: Any, **kwargs: Any) -> Any:
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
        import threading
        import queue
        
        result_queue: queue.Queue[Any] = queue.Queue()
        exception_queue: queue.Queue[Exception] = queue.Queue()
        
        def target() -> None:
            try:
                result = func(*args, **kwargs)
                result_queue.put(result)
            except Exception as e:
                exception_queue.put(e)
        
        # 启动线程
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        
        # 等待结果或超时
        try:
            # 首先尝试获取结果
            result = result_queue.get(timeout=timeout)
            return result
        except queue.Empty:
            # 如果超时，检查是否有异常
            if not exception_queue.empty():
                raise exception_queue.get()
            else:
                raise TimeoutError(f"函数执行超时（{timeout}秒）")
    
    async def _execute_with_timeout_async(self, func: Callable[..., Any], timeout: float, *args: Any, **kwargs: Any) -> Any:
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
    
    def retry(self, func: Optional[Callable] = None, *, config: Optional[RetryConfig] = None) -> Union[Callable, Any]:
        """
        重试装饰器
        
        Args:
            func: 要装饰的函数
            config: 重试配置（可选）
            
        Returns:
            装饰后的函数或装饰器
        """
        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # 使用提供的配置或默认配置
                retry_config = config or self.config
                retry_manager = RetryManager(retry_config, self.logger)
                return retry_manager.execute_with_retry(f, *args, **kwargs)
            
            @functools.wraps(f)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
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
        self._strategy = create_retry_strategy(config)


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