"""降级管理器"""

import time
import asyncio
from typing import Any, Optional, Sequence, Dict, List
from langchain_core.messages import BaseMessage

from .interfaces import IFallbackStrategy, IClientFactory, IFallbackLogger
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession
from .strategies import create_fallback_strategy
from ..models import LLMResponse
from ..exceptions import LLMCallError


class DefaultFallbackLogger(IFallbackLogger):
    """默认降级日志记录器"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化默认降级日志记录器
        
        Args:
            enabled: 是否启用日志记录
        """
        self.enabled = enabled
        self._sessions: List[FallbackSession] = []
    
    def log_fallback_attempt(self, primary_model: str, fallback_model: str, 
                            error: Exception, attempt: int) -> None:
        """
        记录降级尝试
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            error: 发生的错误
            attempt: 尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Fallback] 尝试 {attempt}: {primary_model} -> {fallback_model}, 错误: {error}")
    
    def log_fallback_success(self, primary_model: str, fallback_model: str, 
                           response: LLMResponse, attempt: int) -> None:
        """
        记录降级成功
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            response: 响应结果
            attempt: 尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Fallback] 成功: {primary_model} -> {fallback_model}, 尝试: {attempt}")
    
    def log_fallback_failure(self, primary_model: str, error: Exception, 
                           total_attempts: int) -> None:
        """
        记录降级失败
        
        Args:
            primary_model: 主模型名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Fallback] 失败: {primary_model}, 总尝试: {total_attempts}, 错误: {error}")
    
    def add_session(self, session: FallbackSession) -> None:
        """添加会话记录"""
        self._sessions.append(session)
    
    def get_sessions(self) -> List[FallbackSession]:
        """获取所有会话记录"""
        return self._sessions.copy()
    
    def clear_sessions(self) -> None:
        """清空会话记录"""
        self._sessions.clear()


class FallbackManager:
    """降级管理器"""
    
    def __init__(self, config: FallbackConfig, client_factory: IClientFactory, 
                 logger: Optional[IFallbackLogger] = None):
        """
        初始化降级管理器
        
        Args:
            config: 降级配置
            client_factory: 客户端工厂
            logger: 日志记录器
        """
        self.config = config
        self.client_factory = client_factory
        self.logger = logger or DefaultFallbackLogger()
        self._strategy = create_fallback_strategy(config)
        self._sessions: List[FallbackSession] = []
    
    async def generate_with_fallback(
        self, 
        messages: Sequence[BaseMessage], 
        parameters: Optional[Dict[str, Any]] = None,
        primary_model: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """
        带降级的异步生成
        
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
        if not self.config.is_enabled():
            # 如果降级未启用，直接使用主模型
            client = self.client_factory.create_client(primary_model or "")
            return await client.generate_async(messages, parameters or {}, **kwargs)
        
        # 创建降级会话
        session = FallbackSession(
            primary_model=primary_model or "",
            start_time=time.time()
        )
        
        try:
            attempt = 0
            last_error = None
            
            while attempt < self.config.get_max_attempts():
                # 获取降级目标
                target_model = self._strategy.get_fallback_target(last_error, attempt)
                
                # 如果没有目标模型，使用主模型
                if target_model is None and attempt == 0:
                    target_model = primary_model or ""
                
                if target_model is None:
                    break
                
                # 计算延迟
                delay = 0.0
                if attempt > 0 and last_error:
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
                    if not self._strategy.should_fallback(e, attempt + 1):
                        break
                
                attempt += 1
            
            # 所有尝试都失败
            session.mark_failure(last_error or LLMCallError("未知错误"))
            self.logger.log_fallback_failure(primary_model or "", last_error, attempt)
            
            # 抛出最后的错误
            raise last_error or LLMCallError("降级失败")
            
        finally:
            # 记录会话
            self._sessions.append(session)
            if isinstance(self.logger, DefaultFallbackLogger):
                self.logger.add_session(session)
    
    def generate_with_fallback(
        self, 
        messages: Sequence[BaseMessage], 
        parameters: Optional[Dict[str, Any]] = None,
        primary_model: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """
        带降级的同步生成
        
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
        # 使用asyncio运行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.generate_with_fallback_async(messages, parameters, primary_model, **kwargs)
            )
        finally:
            loop.close()
    
    async def generate_with_fallback_async(
        self, 
        messages: Sequence[BaseMessage], 
        parameters: Optional[Dict[str, Any]] = None,
        primary_model: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """
        带降级的异步生成（别名）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            primary_model: 主模型名称
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        return await self.generate_with_fallback(messages, parameters, primary_model, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取降级统计信息
        
        Returns:
            统计信息字典
        """
        total_sessions = len(self._sessions)
        successful_sessions = sum(1 for s in self._sessions if s.success)
        failed_sessions = total_sessions - successful_sessions
        
        total_attempts = sum(s.get_total_attempts() for s in self._sessions)
        
        # 计算平均尝试次数
        avg_attempts = total_attempts / total_sessions if total_sessions > 0 else 0
        
        # 计算降级使用率
        fallback_usage = sum(1 for s in self._sessions if s.get_total_attempts() > 1)
        fallback_rate = fallback_usage / total_sessions if total_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "failed_sessions": failed_sessions,
            "success_rate": successful_sessions / total_sessions if total_sessions > 0 else 0,
            "total_attempts": total_attempts,
            "average_attempts": avg_attempts,
            "fallback_usage": fallback_usage,
            "fallback_rate": fallback_rate,
            "config": self.config.to_dict(),
        }
    
    def get_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取降级会话记录
        
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
        if isinstance(self.logger, DefaultFallbackLogger):
            self.logger.clear_sessions()
    
    def is_enabled(self) -> bool:
        """检查降级是否启用"""
        return self.config.is_enabled()
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return self.client_factory.get_available_models()
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置
        
        Args:
            config: 新的降级配置
        """
        self.config = config
        self._strategy = create_fallback_strategy(config)