"""降级执行器

负责 Core 层的降级执行逻辑，包括顺序降级和并行降级策略。
"""

import time
import asyncio
from typing import Any, Optional, Sequence, Dict, List, Tuple
from src.infrastructure.messages.base import BaseMessage

from src.interfaces.llm import IFallbackStrategy, IClientFactory, IFallbackLogger, LLMResponse
# 从基础设施层导入降级配置和策略
from src.infrastructure.llm.fallback import FallbackConfig, FallbackAttempt, FallbackSession, FallbackEngine

# 修复导入路径
from src.interfaces.llm.exceptions import LLMCallError


class FallbackExecutor:
    """降级执行器
    
    负责 Core 层的降级执行逻辑，包括：
    1. 顺序降级策略执行
    2. 并行降级策略执行
    3. 降级尝试和错误处理
    4. 会话创建和管理
    """
    
    def __init__(self, 
                 config: Optional[FallbackConfig] = None,
                 client_factory: Optional[IClientFactory] = None,
                 logger: Optional[IFallbackLogger] = None):
        """
        初始化降级执行器
        
        Args:
            config: 降级配置
            client_factory: 客户端工厂
            logger: 日志记录器
        """
        self.config = config
        self.client_factory = client_factory
        self.logger = logger
        
        # 延迟初始化策略，避免循环依赖
        self._strategy: Optional[IFallbackStrategy] = None
        self._strategies_initialized = False
    
    def _initialize_strategy(self) -> None:
        """延迟初始化策略，避免循环依赖"""
        if self._strategies_initialized:
            return
            
        if self.config:
            self._engine = FallbackEngine(self.config)
            
        self._strategies_initialized = True
    
    async def generate_with_fallback(
        self, 
        messages: Sequence[BaseMessage], 
        parameters: Optional[Dict[str, Any]] = None,
        primary_model: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[LLMResponse, FallbackSession]:
        """
        带降级的异步生成
        
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
        self._initialize_strategy()
        
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
            from src.infrastructure.llm.fallback import ParallelFallbackStrategy
            if self._strategy and isinstance(self._strategy, ParallelFallbackStrategy):
                # 并行降级策略
                try:
                    response = await self._strategy.execute_parallel_fallback(
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
                    target_model = self._strategy.get_fallback_target(last_error or Exception("Initial attempt"), attempt) if self._strategy else None
                    
                    # 如果没有目标模型，使用主模型
                    if target_model is None and attempt == 0:
                        target_model = primary_model or ""
                    
                    if target_model is None:
                        break
                    
                    # 计算延迟
                    delay = 0.0
                    if attempt > 0 and last_error and self._strategy:
                        delay = self._strategy.get_fallback_delay(last_error, attempt)
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
                        if attempt > 0:
                            if self.logger:
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
                        if attempt > 0:
                            if self.logger:
                                self.logger.log_fallback_attempt(
                                    primary_model or "", target_model, e, attempt + 1
                                )
                        
                        # 检查是否应该继续降级
                        if self._strategy and not self._strategy.should_fallback(e, attempt + 1):
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
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置
        
        Args:
            config: 新的降级配置
        """
        self.config = config
        self._engine = FallbackEngine(config)
        self._strategies_initialized = False  # 重新初始化策略
    
    def is_enabled(self) -> bool:
        """检查降级是否启用"""
        return self.config is not None and self.config.is_enabled()
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        if not self.client_factory:
            return []
        return self.client_factory.get_available_models()