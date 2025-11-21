"""降级引擎

整合了降级执行器和编排器的功能，提供统一的降级处理逻辑。
"""

import time
import asyncio
from typing import Any, Optional, Sequence, Dict, List, Tuple
from langchain_core.messages import BaseMessage

from .interfaces import IFallbackStrategy, IClientFactory, IFallbackLogger
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession
from .strategies import create_fallback_strategy

# 修复导入路径
from src.core.llm.models import LLMResponse
from src.core.llm.exceptions import LLMCallError

# Services 层的导入
from src.interfaces.llm import ITaskGroupManager, IPollingPoolManager
from src.core.llm.wrappers.fallback_manager import (
    GroupBasedFallbackStrategy,
    PollingPoolFallbackStrategy,
)


class FallbackEngine:
    """降级引擎
    
    整合了降级执行器和编排器的功能，包括：
    1. Core 层的降级执行逻辑
    2. Services 层的业务编排逻辑
    3. 任务组降级策略执行
    4. 轮询池降级策略执行
    5. 统一的降级目标判断和选择
    """
    
    def __init__(self, 
                 config: Optional[FallbackConfig] = None,
                 client_factory: Optional[IClientFactory] = None,
                 logger: Optional[IFallbackLogger] = None,
                 task_group_manager: Optional[ITaskGroupManager] = None,
                 polling_pool_manager: Optional[IPollingPoolManager] = None):
        """
        初始化降级引擎
        
        Args:
            config: 降级配置
            client_factory: 客户端工厂
            logger: 日志记录器
            task_group_manager: 任务组管理器
            polling_pool_manager: 轮询池管理器
        """
        self.config = config
        self.client_factory = client_factory
        self.logger = logger
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        
        # Core 层策略
        self._core_strategy = None
        
        # Services 层策略
        self._group_strategy = None
        self._pool_strategy = None
        
        # 延迟初始化策略，避免循环依赖
        self._strategies_initialized = False
    
    def _initialize_strategies(self):
        """延迟初始化策略，避免循环依赖"""
        if self._strategies_initialized:
            return
            
        # Core 层策略初始化
        if self.config:
            self._core_strategy = create_fallback_strategy(self.config)
            
        # Services 层策略初始化
        if self.task_group_manager:
            self._group_strategy = GroupBasedFallbackStrategy(self.task_group_manager)
        if self.polling_pool_manager:
            self._pool_strategy = PollingPoolFallbackStrategy(self.polling_pool_manager)
            
        self._strategies_initialized = True
    
    async def generate_with_fallback(
        self, 
        messages: Sequence[BaseMessage], 
        parameters: Optional[Dict[str, Any]] = None,
        primary_model: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[LLMResponse, FallbackSession]:
        """
        带降级的异步生成（Core 层方法）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            primary_model: 主模型名称
            **kwargs: 其他参数
            
        Returns:
            元组：(LLM响应, 会话记录)
            
        Raises:
            LLMCallError: 所有尝试都失败
        """
        self._initialize_strategies()
        
        # 创建降级会话
        session = FallbackSession(
            primary_model=primary_model or "",
            start_time=time.time()
        )
        
        try:
            if not self.config or not self.config.is_enabled():
                # 如果降级未启用，直接使用主模型
                if not self.client_factory:
                    raise LLMCallError("客户端工厂未初始化")
                    
                client = self.client_factory.create_client(primary_model or "")
                response = await client.generate_async(messages, parameters or {}, **kwargs)
                
                # 记录成功
                fallback_attempt = FallbackAttempt(
                    primary_model=primary_model or "",
                    fallback_model=None,
                    error=None,
                    attempt_number=1,
                    timestamp=time.time(),
                    success=True,
                    delay=0.0,
                    response=response
                )
                session.add_attempt(fallback_attempt)
                session.mark_success(response)
                
                return response, session
            
            attempt = 0
            last_error = None
            
            # 检查是否是并行降级策略
            from .strategies import ParallelFallbackStrategy
            if self._core_strategy and isinstance(self._core_strategy, ParallelFallbackStrategy):
                # 并行降级策略
                try:
                    response = await self._core_strategy.execute_parallel_fallback(
                        self.client_factory, messages, parameters or {}, primary_model or "", **kwargs
                    )
                    
                    # 记录成功
                    fallback_attempt = FallbackAttempt(
                        primary_model=primary_model or "",
                        fallback_model="parallel_fallback",
                        error=None,
                        attempt_number=1,
                        timestamp=time.time(),
                        success=True,
                        delay=0.0,
                        response=response
                    )
                    session.add_attempt(fallback_attempt)
                    session.mark_success(response)
                    
                    if self.logger:
                        self.logger.log_fallback_success(
                            primary_model or "", "parallel_fallback", response, 1
                        )
                    
                    return response, session
                    
                except Exception as e:
                    # 并行降级失败
                    last_error = e
                    fallback_attempt = FallbackAttempt(
                        primary_model=primary_model or "",
                        fallback_model="parallel_fallback",
                        error=e,
                        attempt_number=1,
                        timestamp=time.time(),
                        success=False,
                        delay=0.0
                    )
                    session.add_attempt(fallback_attempt)
                    
                    if self.logger:
                        self.logger.log_fallback_failure(primary_model or "", e, 1)
                    session.mark_failure(e)
                    raise e
            else:
                # 顺序降级策略
                while self.config and attempt < self.config.get_max_attempts():
                    # 获取降级目标
                    target_model = self._core_strategy.get_fallback_target(last_error or Exception("Initial attempt"), attempt) if self._core_strategy else None
                    
                    # 如果没有目标模型，使用主模型
                    if target_model is None and attempt == 0:
                        target_model = primary_model or ""
                    
                    if target_model is None:
                        break
                    
                    # 计算延迟
                    delay = 0.0
                    if attempt > 0 and last_error and self._core_strategy:
                        delay = self._core_strategy.get_fallback_delay(last_error, attempt)
                        if delay > 0:
                            await asyncio.sleep(delay)
                    
                    # 创建尝试记录
                    fallback_attempt = FallbackAttempt(
                        primary_model=primary_model or "",
                        fallback_model=target_model if attempt > 0 else None,
                        error=last_error,
                        attempt_number=attempt + 1,
                        timestamp=time.time(),
                        success=False,
                        delay=delay
                    )
                    
                    try:
                        # 创建客户端并生成响应
                        if not self.client_factory:
                            raise LLMCallError("客户端工厂未初始化")
                            
                        client = self.client_factory.create_client(target_model)
                        response = await client.generate_async(messages, parameters or {}, **kwargs)
                        
                        # 成功
                        fallback_attempt.success = True
                        fallback_attempt.response = response
                        session.add_attempt(fallback_attempt)
                        session.mark_success(response)
                        
                        # 记录成功日志
                        if attempt > 0 and self.logger:
                            self.logger.log_fallback_success(
                                primary_model or "", target_model, response, attempt + 1
                            )
                        
                        return response, session
                        
                    except Exception as e:
                        # 失败
                        last_error = e
                        fallback_attempt.error = e
                        session.add_attempt(fallback_attempt)
                        
                        # 记录尝试日志
                        if attempt > 0 and self.logger:
                            self.logger.log_fallback_attempt(
                                primary_model or "", target_model, e, attempt + 1
                            )
                        
                        # 检查是否应该继续降级
                        if self._core_strategy and not self._core_strategy.should_fallback(e, attempt + 1):
                            break
                    
                    attempt += 1
            
            # 所有尝试都失败
            final_error = last_error or LLMCallError("未知错误")
            session.mark_failure(final_error)
            if self.logger:
                self.logger.log_fallback_failure(primary_model or "", final_error, attempt)
            
            # 抛出最后的错误
            raise last_error or LLMCallError("降级失败")
            
        finally:
            # 会话已经在上面创建并管理，这里不需要额外操作
            pass
    
    async def execute_with_fallback(
        self,
        primary_target: str,
        fallback_groups: List[str],
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        执行带降级的请求（Services 层方法）
        
        Args:
            primary_target: 主要目标
            fallback_groups: 降级组列表
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
            
        Raises:
            LLMCallError: 所有尝试都失败
        """
        self._initialize_strategies()
        
        try:
            # 判断是任务组还是轮询池
            if self._is_polling_pool_target(primary_target):
                return await self._execute_with_pool_fallback(primary_target, prompt, parameters, **kwargs)
            else:
                return await self._execute_with_group_fallback(primary_target, prompt, parameters, **kwargs)
                
        except Exception as e:
            if self.logger:
                self.logger.log_fallback_failure(primary_target, e, 1)
            raise LLMCallError(f"降级执行失败: {e}")
    
    async def _execute_with_group_fallback(
        self,
        primary_target: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        使用任务组降级策略执行
        
        Args:
            primary_target: 主要目标
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        current_target = primary_target
        attempt = 0
        last_error = None
        
        while attempt < 5:  # 最大尝试5次
            try:
                # 获取目标模型列表
                if not self.task_group_manager:
                    raise LLMCallError("任务组管理器未初始化")
                    
                models = self.task_group_manager.get_models_for_group(current_target)
                if not models:
                    raise ValueError(f"没有找到模型: {current_target}")
                
                # 选择第一个模型
                model_name = models[0]
                
                # 创建客户端并执行
                if not self.client_factory:
                    raise LLMCallError("客户端工厂未初始化")
                    
                client = self.client_factory.create_client(model_name)
                messages = [BaseMessage(content=prompt)]
                response = await client.generate_async(messages, parameters or {}, **kwargs)
                
                # 记录成功
                if self._group_strategy:
                    self._group_strategy.record_success(current_target)
                
                if attempt > 0 and self.logger:
                    self.logger.log_fallback_success(primary_target, current_target, response, attempt + 1)
                
                return response
                
            except Exception as e:
                last_error = e
                # 记录失败
                if self._group_strategy:
                    self._group_strategy.record_failure(current_target, e)
                
                # 获取降级目标
                if self._group_strategy:
                    fallback_targets = self._group_strategy.get_fallback_targets(current_target, e)
                    
                    if not fallback_targets or attempt >= 4:
                        break
                    
                    # 选择下一个降级目标
                    current_target = fallback_targets[0]
                    attempt += 1
                    
                    # 记录降级尝试
                    if self.logger:
                        self.logger.log_fallback_attempt(primary_target, current_target, e, attempt + 1)
                else:
                    break
        
        # 所有尝试都失败
        raise last_error or LLMCallError("任务组降级失败")
    
    async def _execute_with_pool_fallback(
        self,
        primary_target: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        使用轮询池降级策略执行
        
        Args:
            primary_target: 主要目标（轮询池名称）
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        if not self.polling_pool_manager:
            raise LLMCallError("轮询池管理器未初始化")
            
        pool = self.polling_pool_manager.get_pool(primary_target)
        if not pool:
            raise ValueError(f"轮询池不存在: {primary_target}")
        
        try:
            # 轮询池内部处理实例轮换和降级
            result = await pool.call_llm(prompt, **kwargs)
            
            return result
            
        except Exception as e:
            raise LLMCallError(f"轮询池执行失败: {e}")
    
    def _is_polling_pool_target(self, target: str) -> bool:
        """
        判断目标是否是轮询池
        
        Args:
            target: 目标名称
            
        Returns:
            是否是轮询池
        """
        # 检查是否是已知的轮询池
        if not self.polling_pool_manager:
            return False
        pools = self.polling_pool_manager.list_all_status()
        return target in pools
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置
        
        Args:
            config: 新的降级配置
        """
        self.config = config
        self._core_strategy = create_fallback_strategy(config)
        self._strategies_initialized = False  # 重新初始化策略
    
    def is_enabled(self) -> bool:
        """检查降级是否启用"""
        return self.config is not None and self.config.is_enabled()
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        if not self.client_factory:
            return []
        return self.client_factory.get_available_models()