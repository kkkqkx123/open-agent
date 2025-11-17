"""降级管理器

整合了 Core 层和 Services 层的降级管理功能。
Core 层提供基础的降级策略和执行逻辑，Services 层提供业务编排和高级功能。
"""

import time
import asyncio
from typing import Any, Optional, Sequence, Dict, List
from langchain_core.messages import BaseMessage

from .interfaces import IFallbackStrategy, IClientFactory, IFallbackLogger
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession
from .strategies import create_fallback_strategy

# 修复导入路径
from src.core.llm.models import LLMResponse
from src.core.llm.exceptions import LLMCallError

# Services 层的导入
from src.core.llm.interfaces import ITaskGroupManager, IPollingPoolManager
from src.core.llm.wrappers.fallback_manager import (
    GroupBasedFallbackStrategy,
    PollingPoolFallbackStrategy,
    DefaultFallbackLogger as CoreDefaultFallbackLogger,
)


class FallbackManager:
    """整合的降级管理器
    
    整合了 Core 层和 Services 层的功能：
    1. Core 层：基础降级策略、配置管理、会话跟踪
    2. Services 层：业务编排、任务组管理、轮询池管理
    """
    
    def __init__(self, 
                 # Core 层参数
                 config: Optional[FallbackConfig] = None,
                 client_factory: Optional[IClientFactory] = None,
                 logger: Optional[IFallbackLogger] = None,
                 # Services 层参数
                 task_group_manager: Optional[ITaskGroupManager] = None,
                 polling_pool_manager: Optional[IPollingPoolManager] = None):
        """
        初始化降级管理器
        
        Args:
            config: 降级配置（Core 层）
            client_factory: 客户端工厂（Core 层）
            logger: 日志记录器（Core 层）
            task_group_manager: 任务组管理器（Services 层）
            polling_pool_manager: 轮询池管理器（Services 层）
        """
        # Core 层初始化
        self.config = config
        self.client_factory = client_factory
        self.logger = logger or CoreDefaultFallbackLogger()
        self._strategy = None
        self._sessions: List[FallbackSession] = []
        
        # Services 层初始化
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        
        # Services 层策略
        self._group_strategy = None
        self._pool_strategy = None
        
        # 统计信息（整合 Core 和 Services 层）
        self._stats = {
            # Core 层统计
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_attempts": 0,
            "average_attempts": 0.0,
            "fallback_usage": 0,
            "fallback_rate": 0.0,
            # Services 层统计
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }
        
        # 延迟初始化策略，避免循环依赖
        self._strategies_initialized = False
    
    def _initialize_strategies(self):
        """延迟初始化策略，避免循环依赖"""
        if self._strategies_initialized:
            return
            
        # Core 层策略初始化
        if self.config:
            self._strategy = create_fallback_strategy(self.config)
        
        # Services 层策略初始化
        if self.task_group_manager:
            self._group_strategy = GroupBasedFallbackStrategy(self.task_group_manager)
        if self.polling_pool_manager:
            self._pool_strategy = PollingPoolFallbackStrategy(self.polling_pool_manager)
            
        self._strategies_initialized = True
    
    def _update_core_stats(self) -> None:
        """更新 Core 层统计信息"""
        total_sessions = len(self._sessions)
        successful_sessions = sum(1 for s in self._sessions if s.success)
        failed_sessions = total_sessions - successful_sessions
        
        total_attempts = sum(s.get_total_attempts() for s in self._sessions)
        
        # 计算平均尝试次数
        avg_attempts = total_attempts / total_sessions if total_sessions > 0 else 0
        
        # 计算降级使用率
        fallback_usage = sum(1 for s in self._sessions if s.get_total_attempts() > 1)
        fallback_rate = fallback_usage / total_sessions if total_sessions > 0 else 0
        
        self._stats.update({
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "failed_sessions": failed_sessions,
            "success_rate": successful_sessions / total_sessions if total_sessions > 0 else 0,
            "total_attempts": total_attempts,
            "average_attempts": avg_attempts,
            "fallback_usage": fallback_usage,
            "fallback_rate": fallback_rate,
        })
    
    # === Core 层方法 ===
    
    async def generate_with_fallback(
        self, 
        messages: Sequence[BaseMessage], 
        parameters: Optional[Dict[str, Any]] = None,
        primary_model: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """
        带降级的异步生成（Core 层方法）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            primary_model: 主模型名称
            **kwargs: 其他参数
            
        Returns:
            LLM响应
            
        Raises:
            LLMCallError: 所有尝试都失败
        """
        self._initialize_strategies()
        
        if not self.config or not self.config.is_enabled():
            # 如果降级未启用，直接使用主模型，但仍需记录会话
            session = FallbackSession(
                primary_model=primary_model or "",
                start_time=time.time()
            )
            
            try:
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
                
                return response
            finally:
                # 记录会话
                self._sessions.append(session)
                self._update_core_stats()
        
        # 创建降级会话
        session = FallbackSession(
            primary_model=primary_model or "",
            start_time=time.time()
        )
        
        try:
            attempt = 0
            last_error = None
            
            # 检查是否是并行降级策略
            from .strategies import ParallelFallbackStrategy
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
                    
                    self.logger.log_fallback_success(
                        primary_model or "", "parallel_fallback", response, 1
                    )
                    
                    return response
                    
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
                            self.logger.log_fallback_success(
                                primary_model or "", target_model, response, attempt + 1
                            )
                        
                        return response
                        
                    except Exception as e:
                        # 失败
                        last_error = e
                        fallback_attempt.error = e
                        session.add_attempt(fallback_attempt)
                        
                        # 记录尝试日志
                        if attempt > 0:
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
            self.logger.log_fallback_failure(primary_model or "", final_error, attempt)
            
            # 抛出最后的错误
            raise last_error or LLMCallError("降级失败")
            
        finally:
            # 记录会话
            self._sessions.append(session)
            self._update_core_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取降级统计信息（整合 Core 和 Services 层）
        
        Returns:
            统计信息字典
        """
        self._update_core_stats()
        return self._stats.copy()
    
    def get_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取降级会话记录（Core 层方法）
        
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
        """清空会话记录（Core 层方法）"""
        self._sessions.clear()
        # 重置统计信息
        self._stats.update({
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_attempts": 0,
            "average_attempts": 0.0,
            "fallback_usage": 0,
            "fallback_rate": 0.0,
        })
    
    def is_enabled(self) -> bool:
        """检查降级是否启用（Core 层方法）"""
        return self.config is not None and self.config.is_enabled()
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表（Core 层方法）"""
        if not self.client_factory:
            return []
        return self.client_factory.get_available_models()
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置（Core 层方法）
        
        Args:
            config: 新的降级配置
        """
        self.config = config
        self._strategy = create_fallback_strategy(config)
        self._strategies_initialized = False  # 重新初始化策略
    
    # === Services 层方法 ===
    
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
        
        Services层的核心编排逻辑：
        1. 判断是任务组还是轮询池
        2. 调用相应的执行方法
        3. 处理错误并进行降级重试
        
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
        self._stats["total_requests"] += 1
        
        try:
            # 判断是任务组还是轮询池
            if self._is_polling_pool_target(primary_target):
                return await self._execute_with_pool_fallback(primary_target, prompt, parameters, **kwargs)
            else:
                return await self._execute_with_group_fallback(primary_target, prompt, parameters, **kwargs)
                
        except Exception as e:
            self._stats["failed_requests"] += 1
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
        使用任务组降级策略执行（Services 层方法）
        
        编排流程：
        1. 获取目标模型
        2. 创建客户端执行调用
        3. 如果失败，使用Core层的策略获取降级目标
        4. 重复直到成功或达到尝试次数限制
        
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
                
                # 记录成功 - 使用Core层的策略记录
                if self._group_strategy:
                    self._group_strategy.record_success(current_target)
                self._stats["successful_requests"] += 1
                
                if attempt > 0:
                    self._stats["group_fallbacks"] += 1
                    self.logger.log_fallback_success(primary_target, current_target, response, attempt + 1)
                
                return response
                
            except Exception as e:
                last_error = e
                # 记录失败 - 使用Core层的策略记录
                if self._group_strategy:
                    self._group_strategy.record_failure(current_target, e)
                
                # 获取降级目标 - 使用Core层的策略获取
                if self._group_strategy:
                    fallback_targets = self._group_strategy.get_fallback_targets(current_target, e)
                    
                    if not fallback_targets or attempt >= 4:
                        break
                    
                    # 选择下一个降级目标
                    current_target = fallback_targets[0]
                    attempt += 1
                    
                    # 记录降级尝试 - Services层负责日志记录
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
        使用轮询池降级策略执行（Services 层方法）
        
        编排流程：
        1. 获取轮询池
        2. 使用轮询池执行调用
        3. 轮询池内部处理实例轮换和降级
        
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
            
            self._stats["successful_requests"] += 1
            self._stats["pool_fallbacks"] += 1
            
            return result
            
        except Exception as e:
            raise LLMCallError(f"轮询池执行失败: {e}")
    
    def _is_polling_pool_target(self, target: str) -> bool:
        """
        判断目标是否是轮询池（Services 层方法）
        
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
    
    def reset_stats(self) -> None:
        """重置所有统计信息"""
        self._stats = {
            # Core 层统计
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_attempts": 0,
            "average_attempts": 0.0,
            "fallback_usage": 0,
            "fallback_rate": 0.0,
            # Services 层统计
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }