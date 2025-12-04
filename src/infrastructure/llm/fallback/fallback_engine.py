"""降级引擎基础设施模块

提供统一的降级执行功能，支持多种降级策略和并行执行。
"""

import time
import asyncio
from typing import Any, Optional, Sequence, Dict, List, Tuple, Callable, Awaitable
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession, FallbackStrategy


class FallbackEngine:
    """降级引擎
    
    提供统一的降级执行功能，支持多种降级策略和并行执行。
    """
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        """
        初始化降级引擎
        
        Args:
            config: 降级配置
        """
        self.config = config or FallbackConfig()
    
    async def execute_with_fallback(
        self,
        primary_func: Callable[..., Awaitable],
        fallback_funcs: Dict[str, Callable[..., Awaitable]],
        *args,
        **kwargs
    ) -> Tuple[Any, FallbackSession]:
        """
        执行带降级的异步函数
        
        Args:
            primary_func: 主要函数
            fallback_funcs: 降级函数字典 {model_name: func}
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            元组：(执行结果, 降级会话)
        """
        if not self.config.is_enabled():
            # 如果降级未启用，直接执行主函数
            result = await primary_func(*args, **kwargs)
            session = FallbackSession(
                primary_model="primary",
                start_time=time.time(),
                end_time=time.time(),
                success=True,
                final_response=result
            )
            return result, session
        
        # 创建降级会话
        session = FallbackSession(
            primary_model="primary",
            start_time=time.time()
        )
        
        try:
            if self.config.strategy == FallbackStrategy.PARALLEL:
                return await self._execute_parallel_fallback(
                    primary_func, fallback_funcs, session, *args, **kwargs
                )
            else:
                return await self._execute_sequential_fallback(
                    primary_func, fallback_funcs, session, *args, **kwargs
                )
        except Exception as e:
            session.mark_failure(e)
            raise e
    
    async def _execute_sequential_fallback(
        self,
        primary_func: Callable[..., Awaitable],
        fallback_funcs: Dict[str, Callable[..., Awaitable]],
        session: FallbackSession,
        *args,
        **kwargs
    ) -> Tuple[Any, FallbackSession]:
        """执行顺序降级"""
        attempt = 0
        last_error = None
        
        # 尝试主函数
        try:
            start_time = time.time()
            result = await primary_func(*args, **kwargs)
            
            # 记录成功
            attempt_record = FallbackAttempt(
                primary_model="primary",
                fallback_model=None,
                error=None,
                attempt_number=1,
                timestamp=start_time,
                success=True,
                response=result,
                duration=time.time() - start_time
            )
            session.add_attempt(attempt_record)
            session.mark_success(result)
            
            return result, session
            
        except Exception as e:
            last_error = e
            attempt_record = FallbackAttempt(
                primary_model="primary",
                fallback_model=None,
                error=e,
                attempt_number=1,
                timestamp=time.time(),
                success=False
            )
            session.add_attempt(attempt_record)
        
        # 尝试降级函数
        for i, fallback_model in enumerate(self.config.fallback_models):
            if attempt >= self.config.max_attempts:
                break
                
            attempt += 1
            
            # 检查是否应该降级
            if not self.config.should_fallback_on_error(last_error):
                break
            
            # 计算延迟
            delay = self.config.calculate_delay(attempt)
            if delay > 0:
                await asyncio.sleep(delay)
            
            # 获取降级函数
            fallback_func = fallback_funcs.get(fallback_model)
            if not fallback_func:
                continue
            
            try:
                start_time = time.time()
                result = await fallback_func(*args, **kwargs)
                
                # 记录成功
                attempt_record = FallbackAttempt(
                    primary_model="primary",
                    fallback_model=fallback_model,
                    error=None,
                    attempt_number=attempt + 1,
                    timestamp=start_time,
                    success=True,
                    response=result,
                    delay=delay,
                    duration=time.time() - start_time
                )
                session.add_attempt(attempt_record)
                session.mark_success(result)
                
                return result, session
                
            except Exception as e:
                last_error = e
                attempt_record = FallbackAttempt(
                    primary_model="primary",
                    fallback_model=fallback_model,
                    error=e,
                    attempt_number=attempt + 1,
                    timestamp=time.time(),
                    success=False,
                    delay=delay
                )
                session.add_attempt(attempt_record)
        
        # 所有尝试都失败
        session.mark_failure(last_error)
        raise last_error
    
    async def _execute_parallel_fallback(
        self,
        primary_func: Callable[..., Awaitable],
        fallback_funcs: Dict[str, Callable[..., Awaitable]],
        session: FallbackSession,
        *args,
        **kwargs
    ) -> Tuple[Any, FallbackSession]:
        """执行并行降级"""
        tasks = []
        
        # 添加主函数任务
        tasks.append(("primary", primary_func(*args, **kwargs)))
        
        # 添加降级函数任务
        for fallback_model in self.config.fallback_models:
            fallback_func = fallback_funcs.get(fallback_model)
            if fallback_func:
                tasks.append((fallback_model, fallback_func(*args, **kwargs)))
        
        # 并行执行所有任务
        try:
            if self.config.parallel_timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                    timeout=self.config.parallel_timeout
                )
            else:
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            # 处理结果
            success_count = 0
            first_result = None
            first_error = None
            
            for i, (model_name, _) in enumerate(tasks):
                result = results[i]
                start_time = time.time()
                
                if isinstance(result, Exception):
                    # 失败
                    attempt_record = FallbackAttempt(
                        primary_model="primary",
                        fallback_model=model_name if model_name != "primary" else None,
                        error=result,
                        attempt_number=i + 1,
                        timestamp=start_time,
                        success=False
                    )
                    session.add_attempt(attempt_record)
                    
                    if first_error is None:
                        first_error = result
                else:
                    # 成功
                    success_count += 1
                    if first_result is None:
                        first_result = result
                    
                    attempt_record = FallbackAttempt(
                        primary_model="primary",
                        fallback_model=model_name if model_name != "primary" else None,
                        error=None,
                        attempt_number=i + 1,
                        timestamp=start_time,
                        success=True,
                        response=result
                    )
                    session.add_attempt(attempt_record)
            
            # 检查是否达到成功阈值
            if success_count >= self.config.parallel_success_threshold:
                session.mark_success(first_result)
                return first_result, session
            else:
                session.mark_failure(first_error or Exception("并行降级失败"))
                raise first_error or Exception("并行降级失败")
                
        except asyncio.TimeoutError:
            session.mark_failure(Exception("并行降级超时"))
            raise Exception("并行降级超时")
    
    def execute_with_fallback_sync(
        self,
        primary_func: Callable,
        fallback_funcs: Dict[str, Callable],
        *args,
        **kwargs
    ) -> Tuple[Any, FallbackSession]:
        """
        执行带降级的同步函数
        
        Args:
            primary_func: 主要函数
            fallback_funcs: 降级函数字典 {model_name: func}
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            元组：(执行结果, 降级会话)
        """
        if not self.config.is_enabled():
            # 如果降级未启用，直接执行主函数
            result = primary_func(*args, **kwargs)
            session = FallbackSession(
                primary_model="primary",
                start_time=time.time(),
                end_time=time.time(),
                success=True,
                final_response=result
            )
            return result, session
        
        # 创建降级会话
        session = FallbackSession(
            primary_model="primary",
            start_time=time.time()
        )
        
        try:
            return self._execute_sequential_fallback_sync(
                primary_func, fallback_funcs, session, *args, **kwargs
            )
        except Exception as e:
            session.mark_failure(e)
            raise e
    
    def _execute_sequential_fallback_sync(
        self,
        primary_func: Callable,
        fallback_funcs: Dict[str, Callable],
        session: FallbackSession,
        *args,
        **kwargs
    ) -> Tuple[Any, FallbackSession]:
        """执行同步顺序降级"""
        attempt = 0
        last_error = None
        
        # 尝试主函数
        try:
            start_time = time.time()
            result = primary_func(*args, **kwargs)
            
            # 记录成功
            attempt_record = FallbackAttempt(
                primary_model="primary",
                fallback_model=None,
                error=None,
                attempt_number=1,
                timestamp=start_time,
                success=True,
                response=result,
                duration=time.time() - start_time
            )
            session.add_attempt(attempt_record)
            session.mark_success(result)
            
            return result, session
            
        except Exception as e:
            last_error = e
            attempt_record = FallbackAttempt(
                primary_model="primary",
                fallback_model=None,
                error=e,
                attempt_number=1,
                timestamp=time.time(),
                success=False
            )
            session.add_attempt(attempt_record)
        
        # 尝试降级函数
        for i, fallback_model in enumerate(self.config.fallback_models):
            if attempt >= self.config.max_attempts:
                break
                
            attempt += 1
            
            # 检查是否应该降级
            if not self.config.should_fallback_on_error(last_error):
                break
            
            # 计算延迟
            delay = self.config.calculate_delay(attempt)
            if delay > 0:
                time.sleep(delay)
            
            # 获取降级函数
            fallback_func = fallback_funcs.get(fallback_model)
            if not fallback_func:
                continue
            
            try:
                start_time = time.time()
                result = fallback_func(*args, **kwargs)
                
                # 记录成功
                attempt_record = FallbackAttempt(
                    primary_model="primary",
                    fallback_model=fallback_model,
                    error=None,
                    attempt_number=attempt + 1,
                    timestamp=start_time,
                    success=True,
                    response=result,
                    delay=delay,
                    duration=time.time() - start_time
                )
                session.add_attempt(attempt_record)
                session.mark_success(result)
                
                return result, session
                
            except Exception as e:
                last_error = e
                attempt_record = FallbackAttempt(
                    primary_model="primary",
                    fallback_model=fallback_model,
                    error=e,
                    attempt_number=attempt + 1,
                    timestamp=time.time(),
                    success=False,
                    delay=delay
                )
                session.add_attempt(attempt_record)
        
        # 所有尝试都失败
        session.mark_failure(last_error)
        raise last_error
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置
        
        Args:
            config: 新的降级配置
        """
        self.config = config
    
    def is_enabled(self) -> bool:
        """检查降级是否启用"""
        return self.config.is_enabled()
    
    def get_available_fallback_models(self) -> List[str]:
        """获取可用的降级模型列表"""
        return self.config.get_fallback_models()


class FallbackEngineFactory:
    """降级引擎工厂"""
    
    @staticmethod
    def create_default() -> FallbackEngine:
        """创建默认降级引擎"""
        return FallbackEngine()
    
    @staticmethod
    def create_with_config(config: FallbackConfig) -> FallbackEngine:
        """使用指定配置创建降级引擎"""
        return FallbackEngine(config)
    
    @staticmethod
    def create_from_dict(config_dict: dict) -> FallbackEngine:
        """从字典配置创建降级引擎"""
        config = FallbackConfig.from_dict(config_dict)
        return FallbackEngine(config)