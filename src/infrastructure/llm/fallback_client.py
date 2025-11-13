"""降级客户端包装器"""

from typing import Dict, Any, Optional, List, AsyncGenerator, Generator, Sequence
import logging

from langchain_core.messages import BaseMessage  # type: ignore

from .interfaces import ILLMClient
from .models import LLMResponse, TokenUsage
from .fallback_system import (
    FallbackManager, 
    FallbackConfig, 
    create_fallback_manager,
    SelfManagingFallbackFactory
)
from .enhanced_fallback_manager import EnhancedFallbackManager
from .task_group_manager import TaskGroupManager
from .polling_pool import PollingPoolManager
from .exceptions import LLMFallbackError

logger = logging.getLogger(__name__)


class FallbackClientWrapper(ILLMClient):
    """降级客户端包装器"""

    def __init__(
        self, 
        primary_client: ILLMClient, 
        fallback_models: List[str],
        strategy_type: str = "sequential",
        max_attempts: int = 3,
        use_enhanced_fallback: bool = False,  # 新增参数，用于选择使用哪种降级管理器
        task_group_manager: Optional[TaskGroupManager] = None,
        polling_pool_manager: Optional[PollingPoolManager] = None,
        **config_kwargs
    ) -> None:
        """
        初始化降级客户端包装器

        Args:
            primary_client: 主客户端
            fallback_models: 降级模型列表
            strategy_type: 降级策略类型
            max_attempts: 最大尝试次数
            use_enhanced_fallback: 是否使用增强降级管理器
            task_group_manager: 任务组管理器（用于增强降级）
            polling_pool_manager: 轮询池管理器（用于增强降级）
            **config_kwargs: 其他配置参数
        """
        self.primary_client = primary_client
        self.fallback_models = fallback_models
        self.use_enhanced_fallback = use_enhanced_fallback

        if use_enhanced_fallback:
            # 使用增强降级管理器
            if task_group_manager is None:
                raise ValueError("使用增强降级管理器时必须提供 task_group_manager")
            
            self.enhanced_fallback_manager = EnhancedFallbackManager(
                task_group_manager, 
                polling_pool_manager
            )
            self.fallback_manager: Optional[FallbackManager] = None
        else:
            # 创建降级配置
            self.fallback_config = FallbackConfig(
                enabled=len(fallback_models) > 0,
                fallback_models=fallback_models,
                strategy_type=strategy_type,
                max_attempts=max_attempts,
                **config_kwargs
            )

            # 创建自管理降级工厂
            self.client_factory = SelfManagingFallbackFactory(primary_client)

            # 创建降级管理器
            self.fallback_manager = create_fallback_manager(
                self.fallback_config, 
                owner_client=primary_client
            )
            self.enhanced_fallback_manager: Optional[EnhancedFallbackManager] = None

    def generate(
        self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> LLMResponse:
        """
        生成文本响应（带降级支持）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应

        Raises:
            LLMFallbackError: 降级失败
        """
        if self.use_enhanced_fallback:
            # 使用增强降级管理器
            enhanced_manager = self.enhanced_fallback_manager
            if enhanced_manager is None:
                raise ValueError("增强降级管理器未正确初始化")
            
            # 将消息转换为字符串格式以适应增强管理器的接口
            prompt = self._messages_to_prompt(messages)
            
            # 使用默认的主任务组和降级组
            primary_target = kwargs.get('primary_target', 'default_group')
            fallback_groups = kwargs.get('fallback_groups', [])
            
            # 如果没有指定降级组，使用配置的降级模型
            if not fallback_groups and self.fallback_models:
                fallback_groups = [f"fallback_{model}" for model in self.fallback_models]
            
            try:
                import asyncio
                # 在新线程中运行异步方法
                import concurrent.futures
                import threading
                
                def run_in_new_loop():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            enhanced_manager.execute_with_fallback(
                                primary_target=primary_target,
                                fallback_groups=fallback_groups,
                                prompt=prompt,
                                **kwargs
                            )
                        )
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    result = future.result()
                
                # 创建一个模拟的 BaseMessage 对象
                from langchain_core.messages import AIMessage
                message = AIMessage(content=str(result))
                
                # 将结果转换为LLMResponse格式
                return LLMResponse(
                    content=str(result), 
                    message=message,
                    token_usage=TokenUsage(),
                    model="enhanced_fallback"
                )
                
            except Exception as e:
                logger.error(f"增强降级管理器调用失败: {e}")
                raise LLMFallbackError("增强降级管理器调用失败", e)
        elif self.fallback_manager:
            # 使用传统降级管理器
            try:
                # 首先尝试主客户端
                return self.primary_client.generate(messages, parameters, **kwargs)
            except Exception as primary_error:
                logger.warning(f"主客户端调用失败: {primary_error}")

                # 尝试降级
                try:
                    return self.fallback_manager.generate_with_fallback_sync(
                        messages, parameters, self._get_primary_model_name(), **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"所有降级尝试都失败: {fallback_error}")
                    raise LLMFallbackError("所有模型调用都失败", fallback_error)
        else:
            # 如果没有降级管理器，直接调用主客户端
            return self.primary_client.generate(messages, parameters, **kwargs)

    async def generate_async(
        self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> LLMResponse:
        """
        异步生成文本响应（带降级支持）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应
        """
        if self.use_enhanced_fallback:
            # 使用增强降级管理器
            enhanced_manager = self.enhanced_fallback_manager
            if enhanced_manager is None:
                raise ValueError("增强降级管理器未正确初始化")
            
            prompt = self._messages_to_prompt(messages)
            
            primary_target = kwargs.get('primary_target', 'default_group')
            fallback_groups = kwargs.get('fallback_groups', [])
            
            if not fallback_groups and self.fallback_models:
                fallback_groups = [f"fallback_{model}" for model in self.fallback_models]
            
            try:
                result = await enhanced_manager.execute_with_fallback(
                    primary_target=primary_target,
                    fallback_groups=fallback_groups,
                    prompt=prompt,
                    **kwargs
                )
                
                # 创建一个模拟的 BaseMessage 对象
                from langchain_core.messages import AIMessage
                message = AIMessage(content=str(result))
                
                # 将结果转换为LLMResponse格式
                return LLMResponse(
                    content=str(result), 
                    message=message,
                    token_usage=TokenUsage(),
                    model="enhanced_fallback"
                )
                
            except Exception as e:
                logger.error(f"增强降级管理器异步调用失败: {e}")
                raise LLMFallbackError("增强降级管理器异步调用失败", e)
        elif self.fallback_manager:
            # 使用传统降级管理器
            try:
                # 首先尝试主客户端
                return await self.primary_client.generate_async(
                    messages, parameters, **kwargs
                )
            except Exception as primary_error:
                logger.warning(f"主客户端异步调用失败: {primary_error}")

                # 尝试降级
                try:
                    return await self.fallback_manager.generate_with_fallback_async(
                        messages, parameters, self._get_primary_model_name(), **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"所有异步降级尝试都失败: {fallback_error}")
                    raise LLMFallbackError("所有模型异步调用都失败", fallback_error)
        else:
            # 如果没有降级管理器，直接调用主客户端
            return await self.primary_client.generate_async(messages, parameters, **kwargs)

    def stream_generate(
        self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        流式生成文本响应（带降级支持）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        try:
            # 首先尝试主客户端
            for chunk in self.primary_client.stream_generate(
                messages, parameters, **kwargs
            ):
                yield chunk
        except Exception as primary_error:
            logger.warning(f"主客户端流式调用失败: {primary_error}")

            # 流式降级比较复杂，这里简化为非流式降级
            if self.fallback_manager:
                try:
                    response = self.fallback_manager.generate_with_fallback_sync(
                        messages, parameters, self._get_primary_model_name(), **kwargs
                    )
                    # 将完整响应作为单个块返回
                    yield response.content
                except Exception as fallback_error:
                    logger.error(f"流式降级失败: {fallback_error}")
                    raise LLMFallbackError("流式降级失败", fallback_error)
            else:
                raise LLMFallbackError("主客户端流式调用失败且无降级管理器", primary_error)

    def stream_generate_async(
        self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成文本响应（带降级支持）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """

        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 首先尝试主客户端
                async_gen = self.primary_client.stream_generate_async(
                    messages, parameters, **kwargs
                )
                async for chunk in async_gen:
                    yield chunk

            except Exception as primary_error:
                logger.warning(f"主客户端异步流式调用失败: {primary_error}")

                # 异步流式降级比较复杂，这里简化为非流式降级
                if self.fallback_manager:
                    try:
                        response = await self.fallback_manager.generate_with_fallback_async(
                            messages, parameters, self._get_primary_model_name(), **kwargs
                        )
                        # 将完整响应作为单个块返回
                        yield response.content
                    except Exception as fallback_error:
                        logger.error(f"异步流式降级失败: {fallback_error}")
                        raise LLMFallbackError("异步流式降级失败", fallback_error)
                else:
                    raise LLMFallbackError("主客户端异步流式调用失败且无降级管理器", primary_error)

        return _async_generator()

    def get_token_count(self, text: str) -> int:
        """
        计算文本的token数量

        Args:
            text: 输入文本

        Returns:
            int: token数量
        """
        return self.primary_client.get_token_count(text)

    def get_messages_token_count(self, messages: Sequence[BaseMessage]) -> int:
        """
        计算消息列表的token数量

        Args:
            messages: 消息列表

        Returns:
            int: token数量
        """
        return self.primary_client.get_messages_token_count(messages)

    def supports_function_calling(self) -> bool:
        """
        检查是否支持函数调用

        Returns:
            bool: 是否支持函数调用
        """
        return self.primary_client.supports_function_calling()

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        info = self.primary_client.get_model_info()
        info["fallback_models"] = self.fallback_models
        info["use_enhanced_fallback"] = self.use_enhanced_fallback
        if not self.use_enhanced_fallback and self.fallback_manager:
            info["fallback_enabled"] = self.fallback_manager.is_enabled()
            info["fallback_strategy"] = self.fallback_config.strategy_type
            info["fallback_max_attempts"] = self.fallback_config.max_attempts
        return info

    def _get_primary_model_name(self) -> str:
        """
        获取主模型名称

        Returns:
            str: 主模型名称
        """
        try:
            model_info = self.primary_client.get_model_info()
            return model_info.get("model_name", "primary_model")
        except Exception:
            return "primary_model"
    
    def _messages_to_prompt(self, messages: Sequence[BaseMessage]) -> str:
        """
        将消息序列转换为提示文本
        
        Args:
            messages: 消息序列
            
        Returns:
            str: 提示文本
        """
        # 简单实现：将所有消息内容连接起来
        return " ".join([str(msg.content) for msg in messages])

    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        获取降级统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        if self.use_enhanced_fallback and self.enhanced_fallback_manager:
            return self.enhanced_fallback_manager.get_statistics()
        elif self.fallback_manager:
            return self.fallback_manager.get_stats()
        else:
            return {}

    def reset_fallback_stats(self) -> None:
        """重置降级统计信息"""
        if self.use_enhanced_fallback and self.enhanced_fallback_manager:
            # EnhancedFallbackManager 没有直接的重置方法，我们清空历史记录
            self.enhanced_fallback_manager.fallback_history = []
            # 重置所有熔断器
            for target in list(self.enhanced_fallback_manager.circuit_breakers.keys()):
                self.enhanced_fallback_manager.reset_circuit_breaker(target)
        elif self.fallback_manager:
            self.fallback_manager.clear_sessions()

    def update_fallback_config(self, **config_kwargs) -> None:
        """
        更新降级配置

        Args:
            **config_kwargs: 配置参数
        """
        if not self.use_enhanced_fallback and self.fallback_manager:
            # 更新配置
            for key, value in config_kwargs.items():
                if hasattr(self.fallback_config, key):
                    setattr(self.fallback_config, key, value)

            # 重新创建降级管理器
            self.fallback_manager = create_fallback_manager(
                self.fallback_config, 
                owner_client=self.primary_client
            )

    def get_fallback_sessions(self, limit: Optional[int] = None):
        """
        获取降级会话记录

        Args:
            limit: 限制返回数量

        Returns:
            降级会话记录列表
        """
        if self.use_enhanced_fallback and self.enhanced_fallback_manager:
            return self.enhanced_fallback_manager.get_fallback_history(limit or 10)
        elif self.fallback_manager:
            return self.fallback_manager.get_sessions(limit)
        else:
            return []

    def is_fallback_enabled(self) -> bool:
        """
        检查降级是否启用

        Returns:
            bool: 是否启用降级
        """
        if self.use_enhanced_fallback:
            return True  # EnhancedFallbackManager 总是启用的
        elif self.fallback_manager:
            return self.fallback_manager.is_enabled()
        else:
            return False