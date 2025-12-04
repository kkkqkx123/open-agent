"""重试执行器基础设施模块

提供统一的重试执行功能，支持同步和异步操作。
"""

import time
import asyncio
from typing import Any, Callable, Optional, Awaitable, Union
from .retry_config import RetryConfig, RetrySession, RetryAttempt, RetryStats
from .strategies import create_retry_strategy


class RetryExecutor:
    """重试执行器
    
    提供统一的重试执行功能，支持同步和异步操作。
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        初始化重试执行器
        
        Args:
            config: 重试配置
        """
        self.config = config or RetryConfig()
        self.strategy = create_retry_strategy(self.config)
        self.stats = RetryStats()
    
    def execute(
        self, 
        func: Callable, 
        *args, 
        func_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        执行带重试的同步函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            func_name: 函数名称（用于日志）
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        if not self.config.is_enabled():
            return func(*args, **kwargs)
        
        # 创建重试会话
        session = RetrySession(
            func_name=func_name or func.__name__,
            start_time=time.time()
        )
        
        attempt = 0
        last_error = None
        
        try:
            while self.config.should_continue_retry(attempt, session.start_time):
                attempt += 1
                
                # 计算延迟
                delay = 0.0
                if attempt > 1:
                    delay = self.config.calculate_delay(attempt)
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
                
                # 执行函数
                start_attempt = time.time()
                
                try:
                    # 检查单次尝试超时
                    if self.config.per_attempt_timeout is not None:
                        # Windows不支持signal.SIGALRM，使用线程超时
                        import concurrent.futures
                        
                        try:
                            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                                future = executor.submit(func, *args, **kwargs)
                                result = future.result(timeout=self.config.per_attempt_timeout)
                        except concurrent.futures.TimeoutError:
                            raise TimeoutError(f"函数执行超时: {self.config.per_attempt_timeout}秒")
                    else:
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
                    last_error = e
                    retry_attempt.error = e
                    retry_attempt.duration = time.time() - start_attempt
                    session.add_attempt(retry_attempt)
                    
                    # 检查是否应该继续重试
                    if not self.config.should_retry_on_error(e):
                        break
            
            # 所有尝试都失败
            if last_error is None:
                last_error = Exception("所有重试尝试都失败")
            session.mark_failure(last_error)
            raise last_error
            
        finally:
            # 更新统计信息
            self.stats.update(session)
    
    async def execute_async(
        self, 
        func: Callable[..., Awaitable], 
        *args, 
        func_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        执行带重试的异步函数
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            func_name: 函数名称（用于日志）
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        if not self.config.is_enabled():
            return await func(*args, **kwargs)
        
        # 创建重试会话
        session = RetrySession(
            func_name=func_name or func.__name__,
            start_time=time.time()
        )
        
        attempt = 0
        last_error = None
        
        try:
            while self.config.should_continue_retry(attempt, session.start_time):
                attempt += 1
                
                # 计算延迟
                delay = 0.0
                if attempt > 1:
                    delay = self.config.calculate_delay(attempt)
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
                
                # 执行函数
                start_attempt = time.time()
                
                try:
                    # 检查单次尝试超时
                    if self.config.per_attempt_timeout is not None:
                        try:
                            result = await asyncio.wait_for(
                                func(*args, **kwargs),
                                timeout=self.config.per_attempt_timeout
                            )
                        except asyncio.TimeoutError:
                            raise TimeoutError(f"函数执行超时: {self.config.per_attempt_timeout}秒")
                    else:
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
                    last_error = e
                    retry_attempt.error = e
                    retry_attempt.duration = time.time() - start_attempt
                    session.add_attempt(retry_attempt)
                    
                    # 检查是否应该继续重试
                    if not self.config.should_retry_on_error(e):
                        break
            
            # 所有尝试都失败
            if last_error is None:
                last_error = Exception("所有重试尝试都失败")
            session.mark_failure(last_error)
            raise last_error
            
        finally:
            # 更新统计信息
            self.stats.update(session)
    
    def execute_with_session(
        self, 
        func: Callable, 
        *args, 
        func_name: Optional[str] = None,
        **kwargs
    ) -> tuple[Any, RetrySession]:
        """
        执行带重试的函数并返回会话信息
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            func_name: 函数名称（用于日志）
            **kwargs: 函数关键字参数
            
        Returns:
            元组：(执行结果, 重试会话)
        """
        if not self.config.is_enabled():
            result = func(*args, **kwargs)
            # 创建一个简单的会话记录
            session = RetrySession(
                func_name=func_name or func.__name__,
                start_time=time.time(),
                end_time=time.time(),
                success=True,
                final_result=result
            )
            return result, session
        
        # 创建重试会话
        session = RetrySession(
            func_name=func_name or func.__name__,
            start_time=time.time()
        )
        
        attempt = 0
        last_error = None
        
        try:
            while self.config.should_continue_retry(attempt, session.start_time):
                attempt += 1
                
                # 计算延迟
                delay = 0.0
                if attempt > 1:
                    delay = self.config.calculate_delay(attempt)
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
                
                # 执行函数
                start_attempt = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # 成功
                    retry_attempt.success = True
                    retry_attempt.result = result
                    retry_attempt.duration = time.time() - start_attempt
                    session.add_attempt(retry_attempt)
                    session.mark_success(result)
                    
                    return result, session
                    
                except Exception as e:
                    # 失败
                    last_error = e
                    retry_attempt.error = e
                    retry_attempt.duration = time.time() - start_attempt
                    session.add_attempt(retry_attempt)
                    
                    # 检查是否应该继续重试
                    if not self.config.should_retry_on_error(e):
                        break
            
            # 所有尝试都失败
            if last_error is None:
                last_error = Exception("所有重试尝试都失败")
            session.mark_failure(last_error)
            raise last_error
            
        finally:
            # 更新统计信息
            self.stats.update(session)
    
    async def execute_async_with_session(
        self, 
        func: Callable[..., Awaitable], 
        *args, 
        func_name: Optional[str] = None,
        **kwargs
    ) -> tuple[Any, RetrySession]:
        """
        执行带重试的异步函数并返回会话信息
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            func_name: 函数名称（用于日志）
            **kwargs: 函数关键字参数
            
        Returns:
            元组：(执行结果, 重试会话)
        """
        if not self.config.is_enabled():
            result = await func(*args, **kwargs)
            # 创建一个简单的会话记录
            session = RetrySession(
                func_name=func_name or func.__name__,
                start_time=time.time(),
                end_time=time.time(),
                success=True,
                final_result=result
            )
            return result, session
        
        # 创建重试会话
        session = RetrySession(
            func_name=func_name or func.__name__,
            start_time=time.time()
        )
        
        attempt = 0
        last_error = None
        
        try:
            while self.config.should_continue_retry(attempt, session.start_time):
                attempt += 1
                
                # 计算延迟
                delay = 0.0
                if attempt > 1:
                    delay = self.config.calculate_delay(attempt)
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
                
                # 执行函数
                start_attempt = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # 成功
                    retry_attempt.success = True
                    retry_attempt.result = result
                    retry_attempt.duration = time.time() - start_attempt
                    session.add_attempt(retry_attempt)
                    session.mark_success(result)
                    
                    return result, session
                    
                except Exception as e:
                    # 失败
                    last_error = e
                    retry_attempt.error = e
                    retry_attempt.duration = time.time() - start_attempt
                    session.add_attempt(retry_attempt)
                    
                    # 检查是否应该继续重试
                    if not self.config.should_retry_on_error(e):
                        break
            
            # 所有尝试都失败
            if last_error is None:
                last_error = Exception("所有重试尝试都失败")
            session.mark_failure(last_error)
            raise last_error
            
        finally:
            # 更新统计信息
            self.stats.update(session)
    
    def update_config(self, config: RetryConfig) -> None:
        """
        更新重试配置
        
        Args:
            config: 新的重试配置
        """
        self.config = config
        self.strategy = create_retry_strategy(config)
    
    def get_stats(self) -> RetryStats:
        """获取重试统计信息"""
        return self.stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = RetryStats()
    
    def is_enabled(self) -> bool:
        """检查重试是否启用"""
        return self.config.is_enabled()


class RetryExecutorFactory:
    """重试执行器工厂"""
    
    @staticmethod
    def create_default() -> RetryExecutor:
        """创建默认重试执行器"""
        return RetryExecutor()
    
    @staticmethod
    def create_with_config(config: RetryConfig) -> RetryExecutor:
        """使用指定配置创建重试执行器"""
        return RetryExecutor(config)
    
    @staticmethod
    def create_from_dict(config_dict: dict) -> RetryExecutor:
        """从字典配置创建重试执行器"""
        config = RetryConfig.from_dict(config_dict)
        return RetryExecutor(config)