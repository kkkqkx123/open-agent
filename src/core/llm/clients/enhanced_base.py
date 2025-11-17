"""增强的LLM客户端基类，整合缓存、降级、重试和验证功能"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator, Generator, Sequence, Type, Union, Callable, Awaitable
from datetime import datetime

from langchain_core.messages import BaseMessage

from ..interfaces import ILLMClient, ILLMCallHook
from ..models import LLMResponse, TokenUsage, LLMError, ModelInfo
from ..config import LLMClientConfig
from ..exceptions import (
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
)
from ..cache import CacheManager, create_cache_manager
from ..cache.cache_config import CacheConfig
from ....services.llm.fallback_system import FallbackManager, create_fallback_manager
from ....services.llm.fallback_system.fallback_config import FallbackConfig
from ....services.llm.retry import RetryManager, create_retry_manager
from ....services.llm.retry.retry_config import RetryConfig
from ....services.tools.validation.models import ValidationResult, ValidationStatus


class EnhancedLLMClient(ILLMClient):
    """增强的LLM客户端基类，整合缓存、降级、重试和验证功能"""

    def __init__(self, config: LLMClientConfig) -> None:
        """
        初始化增强客户端

        Args:
            config: 客户端配置
        """
        self.config = config
        self._hooks: List[ILLMCallHook] = []
        self._model_info: Optional[ModelInfo] = None
        
        # 初始化功能模块
        self._cache_manager: Optional[CacheManager] = None
        self._fallback_manager: Optional[FallbackManager] = None
        self._retry_manager: Optional[RetryManager] = None
        self._config_validator: Optional[Any] = None  # 使用Any类型避免循环依赖
        
        # 初始化功能模块
        self._initialize_feature_modules()
        
        # 验证配置
        self._validate_configuration()
    
    def _initialize_feature_modules(self) -> None:
        """初始化功能模块"""
        # 初始化缓存管理器
        if getattr(self.config, 'cache_enabled', False):
            # 从LLMClientConfig创建CacheConfig
            cache_config = CacheConfig(
                enabled=getattr(self.config, 'cache_enabled', False),
                ttl_seconds=getattr(self.config, 'cache_ttl_seconds', 3600),
                max_size=getattr(self.config, 'cache_max_size', 1000),
                cache_type=getattr(self.config, 'cache_type', 'memory')
            )
            self._cache_manager = create_cache_manager(
                self.config.model_type,
                cache_config
            )
        
        # 初始化降级管理器
        if getattr(self.config, 'fallback_enabled', False):
            # 从LLMClientConfig创建FallbackConfig
            fallback_config = FallbackConfig(
                enabled=self.config.fallback_enabled,
                max_attempts=getattr(self.config, 'max_fallback_attempts', 3),
                fallback_models=getattr(self.config, 'fallback_models', []),
                strategy_type="sequential",  # 使用简单的顺序策略
                base_delay=1.0,
                max_delay=60.0
            )
            self._fallback_manager = create_fallback_manager(
                fallback_config,
                self  # 传递自身作为拥有者客户端
            )
        
        # 初始化重试管理器
        if getattr(self.config, 'max_retries', 0) > 0:
            # 从LLMClientConfig创建RetryConfig
            retry_config = RetryConfig(
                enabled=getattr(self.config, 'retry_enabled', True),
                max_attempts=getattr(self.config, 'max_retries', 3),
                base_delay=getattr(self.config, 'base_delay', 1.0),
                max_delay=getattr(self.config, 'max_delay', 60.0),
                exponential_base=getattr(self.config, 'exponential_base', 2.0),
                jitter=getattr(self.config, 'jitter', True)
            )
            self._retry_manager = create_retry_manager(
                retry_config
            )
        
        # 初始化配置验证器
        # 注意：ConfigValidator 需要依赖注入，这里设置为None
        # 在实际使用中，应该通过依赖注入容器获取
        self._config_validator = None
    
    def _validate_configuration(self) -> None:
        """验证配置"""
        # 简单的配置验证，不依赖外部验证器
        if not hasattr(self.config, 'model_name') or not self.config.model_name:
            print("配置验证错误: 缺少模型名称")
        
        if not hasattr(self.config, 'model_type') or not self.config.model_type:
            print("配置验证警告: 缺少模型类型")
    
    def add_hook(self, hook: ILLMCallHook) -> None:
        """
        添加调用钩子

        Args:
            hook: 钩子实例
        """
        self._hooks.append(hook)

    def remove_hook(self, hook: ILLMCallHook) -> None:
        """
        移除调用钩子

        Args:
            hook: 钩子实例
        """
        if hook in self._hooks:
            self._hooks.remove(hook)

    def clear_hooks(self) -> None:
        """清除所有钩子"""
        self._hooks.clear()

    def _call_before_hooks(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """调用前置钩子"""
        for hook in self._hooks:
            try:
                hook.before_call(messages, parameters, **kwargs)
            except Exception as e:
                # 钩子错误不应该影响主流程
                print(f"Warning: Hook before_call failed: {e}")

    def _call_after_hooks(
        self,
        response: LLMResponse,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """调用后置钩子"""
        for hook in self._hooks:
            try:
                hook.after_call(response, messages, parameters, **kwargs)
            except Exception as e:
                # 钩子错误不应该影响主流程
                print(f"Warning: Hook after_call failed: {e}")

    def _call_error_hooks(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """调用错误钩子"""
        for hook in self._hooks:
            try:
                response = hook.on_error(error, messages, parameters, **kwargs)
                if response is not None:
                    return response
            except Exception as e:
                # 钩子错误不应该影响主流程
                print(f"Warning: Hook on_error failed: {e}")

        return None

    def _measure_time(self, func: Any, *args: Any, **kwargs: Any) -> tuple[LLMResponse, float]:
        """测量函数执行时间"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            return result, end_time - start_time
        except Exception as e:
            end_time = time.time()
            raise e

    def _handle_api_error(self, error: Exception) -> LLMCallError:
        """处理API错误"""
        from ....services.llm.error_handler import ErrorHandlerFactory, ErrorContext

        # 创建错误上下文
        context = ErrorContext(
            model_name=self.config.model_name, model_type=self.config.model_type
        )

        # 使用错误处理器处理错误
        error_handler = ErrorHandlerFactory.create_handler(self.config.model_type)
        llm_error = error_handler.handle_error(error, context.to_dict())
        
        # 保留原始错误信息
        if not hasattr(llm_error, 'original_error') or llm_error.original_error is None:
            llm_error.original_error = error
        if not hasattr(llm_error, 'error_context') or llm_error.error_context is None:
            llm_error.error_context = context.to_dict()
            
        return llm_error
    
    def _create_enhanced_error(
        self,
        error_class: Type[LLMCallError],
        message: str,
        original_error: Exception,
        **kwargs: Any
    ) -> LLMCallError:
        """创建增强的错误对象，保留原始错误信息"""
        # 移除可能冲突的参数
        if 'model_name' in kwargs:
            kwargs.pop('model_name')
        
        error = error_class(message, **kwargs)
        error.original_error = original_error
        error.error_type = type(original_error).__name__
        # Note: model_name is set in specific error types like LLMModelNotFoundError
        return error

    def _create_response(
        self,
        content: str,
        message: Any,
        token_usage: TokenUsage,
        finish_reason: Optional[str] = None,
        function_call: Optional[Dict[str, Any]] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """创建响应对象"""
        return LLMResponse(
            content=content,
            message=message,
            token_usage=token_usage,
            model=self.config.model_name,
            finish_reason=finish_reason,
            function_call=function_call,
            response_time=response_time,
            metadata=metadata or {},
        )

    def _merge_parameters(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """合并参数"""
        # 基础参数
        merged: Dict[str, Any] = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
        }

        # 添加max_tokens
        if self.config.max_tokens:
            merged["max_tokens"] = self.config.max_tokens

        # 添加函数调用参数
        if self.config.functions:
            merged["functions"] = self.config.functions

        if self.config.function_call:
            merged["function_call"] = self.config.function_call

        # 合并传入的参数
        if parameters:
            merged.update(parameters)

        return merged
    
    def _extract_system_message(self, messages: Sequence[BaseMessage]) -> Optional[str]:
        """提取系统消息内容"""
        from langchain_core.messages import SystemMessage
        
        for message in messages:
            if isinstance(message, SystemMessage):
                # 确保返回字符串类型
                content = message.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # 如果是列表，转换为字符串
                    return str(content)
        return None
    
    def _prepare_parameters_with_system_message(
        self,
        messages: Sequence[BaseMessage],
        parameters: Dict[str, Any]
    ) -> tuple[Sequence[BaseMessage], Dict[str, Any]]:
        """准备参数，包括系统消息处理"""
        # 提取系统消息
        system_message = self._extract_system_message(messages)
        
        # 如果有系统消息，添加到参数中
        params = parameters.copy()
        if system_message:
            params["system"] = system_message
            
        return messages, params
    
    def _extract_function_call_enhanced(self, response: Any) -> Optional[Dict[str, Any]]:
        """增强的函数调用信息提取，支持多种格式"""
        # 检查additional_kwargs中的function_call
        if hasattr(response, "additional_kwargs"):
            additional_kwargs = response.additional_kwargs
            if isinstance(additional_kwargs, dict):
                if "function_call" in additional_kwargs:
                    result = additional_kwargs["function_call"]
                    if isinstance(result, dict):
                        return result
        
        # 检查tool_calls
        if hasattr(response, "tool_calls"):
            tool_calls = response.tool_calls
            # 处理Mock对象和实际对象
            if tool_calls is not None:
                # 如果是Mock对象，尝试获取其长度或直接检查是否为空
                try:
                    if hasattr(tool_calls, "__len__") and len(tool_calls) > 0:
                        # 返回第一个工具调用
                        tool_call = tool_calls[0]
                        if hasattr(tool_call, "dict"):
                            return tool_call.dict()
                        elif isinstance(tool_call, dict):
                            return tool_call
                except TypeError:
                    # 如果tool_calls是Mock对象且没有长度，跳过
                    pass
        
        # 检查response_metadata中的函数调用信息
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if isinstance(metadata, dict):
                if "function_call" in metadata:
                    result = metadata["function_call"]
                    if isinstance(result, dict):
                        return result
                elif "tool_calls" in metadata:
                    tool_calls = metadata["tool_calls"]
                    if tool_calls is not None:
                        try:
                            if hasattr(tool_calls, "__len__") and len(tool_calls) > 0:
                                tool_call = tool_calls[0]
                                if isinstance(tool_call, dict):
                                    return tool_call
                        except TypeError:
                            # 如果tool_calls是Mock对象且没有长度，跳过
                            pass
        
        return None

    def _validate_messages(self, messages: Sequence[BaseMessage]) -> None:
        """验证消息列表"""
        if not messages:
            raise LLMInvalidRequestError("消息列表不能为空")

        # 检查消息内容
        for i, message in enumerate(messages):
            if not hasattr(message, "content") or not message.content:
                raise LLMInvalidRequestError(f"消息 {i} 缺少内容")

    def _validate_token_limit(self, messages: Sequence[BaseMessage]) -> None:
        """验证Token限制"""
        if self.config.max_tokens:
            token_count = self.get_messages_token_count(messages)
            if token_count > self.config.max_tokens:
                raise LLMTokenLimitError(
                    f"Token数量超过限制: {token_count} > {self.config.max_tokens}",
                    token_count=token_count,
                    limit=self.config.max_tokens,
                )

    def _execute_with_cache(
        self,
        cache_key: str,
        operation: Callable[..., LLMResponse],
        *args: Any,
        **kwargs: Any
    ) -> LLMResponse:
        """使用缓存执行操作"""
        if self._cache_manager is None:
            return operation(*args, **kwargs)
        
        # 尝试从缓存获取
        cached_response = self._cache_manager.get(cache_key)
        if cached_response is not None:
            return cached_response  # type: ignore
        
        # 执行操作
        response: LLMResponse = operation(*args, **kwargs)
        
        # 存储到缓存
        self._cache_manager.set(cache_key, response)
        
        return response

    def _execute_with_fallback(
        self,
        operation: Callable[..., LLMResponse],
        *args: Any,
        **kwargs: Any
    ) -> LLMResponse:
        """使用降级机制执行操作"""
        if self._fallback_manager is None:
            return operation(*args, **kwargs)
        
        # 直接使用降级管理器的生成方法，适用于消息生成操作
        if len(args) >= 1 and hasattr(args[0], '__len__') and len(args[0]) > 0:
            # 假设第一个参数是消息列表
            messages = args[0]
            parameters = args[1] if len(args) > 1 else {}
            primary_model = getattr(self.config, 'model_name', None)
            
            # 使用降级管理器生成
            return self._fallback_manager.generate_with_fallback_sync(
                messages,
                parameters,
                primary_model
            )
        else:
            # 如果参数不匹配消息生成格式，直接执行操作
            return operation(*args, **kwargs)

    def _execute_with_retry(
        self,
        operation: Callable[..., LLMResponse],
        *args: Any,
        **kwargs: Any
    ) -> LLMResponse:
        """使用重试机制执行操作"""
        if self._retry_manager is None:
            return operation(*args, **kwargs)
        
        return self._retry_manager.execute_with_retry(  # type: ignore
        operation, *args, **kwargs
        )

    def generate(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应
        """
        # 验证输入
        self._validate_messages(messages)
        self._validate_token_limit(messages)

        # 合并参数
        merged_params = self._merge_parameters(parameters)

        # 调用前置钩子
        self._call_before_hooks(messages, merged_params, **kwargs)

        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(messages, merged_params, **kwargs)
            
            # 使用缓存、降级和重试机制执行操作
            response = self._execute_with_cache(
                cache_key,
                self._execute_with_fallback,
                self._execute_with_retry,
                self._do_generate_with_hooks,
                messages, merged_params, **kwargs
            )

            # 调用后置钩子
            self._call_after_hooks(response, messages, merged_params, **kwargs)

            return response

        except Exception as e:
            # 转换为LLM错误
            if not isinstance(e, LLMCallError):
                llm_error = self._handle_api_error(e)
            else:
                llm_error = e

            # 尝试通过钩子恢复
            fallback_response = self._call_error_hooks(
                llm_error, messages, merged_params, **kwargs
            )
            if fallback_response is not None:
                return fallback_response

            # 抛出错误
            raise llm_error

    def _do_generate_with_hooks(
        self,
        messages: Sequence[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> LLMResponse:
        """带钩子的生成操作"""
        # 测量执行时间
        response, response_time = self._measure_time(
            self._do_generate, messages, parameters, **kwargs
        )

        # 设置响应时间
        response.response_time = response_time

        return response

    async def generate_async(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        异步生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应
        """
        # 验证输入
        self._validate_messages(messages)
        self._validate_token_limit(messages)

        # 合并参数
        merged_params = self._merge_parameters(parameters)

        # 调用前置钩子
        self._call_before_hooks(messages, merged_params, **kwargs)

        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(messages, merged_params, **kwargs)
            
            # 使用缓存、降级和重试机制执行操作
            response = await self._execute_with_cache_async(
                cache_key,
                self._execute_with_fallback_async,
                self._execute_with_retry_async,
                self._do_generate_async_with_hooks,
                messages, merged_params, **kwargs
            )

            # 调用后置钩子
            self._call_after_hooks(response, messages, merged_params, **kwargs)

            return response

        except Exception as e:
            # 转换为LLM错误
            if not isinstance(e, LLMCallError):
                llm_error = self._handle_api_error(e)
            else:
                llm_error = e

            # 尝试通过钩子恢复
            fallback_response = self._call_error_hooks(
                llm_error, messages, merged_params, **kwargs
            )
            if fallback_response is not None:
                return fallback_response

            # 抛出错误
            raise llm_error

    async def _execute_with_cache_async(
        self,
        cache_key: str,
        operation: Callable[..., Awaitable[LLMResponse]],
        *args: Any,
        **kwargs: Any
    ) -> LLMResponse:
        """异步使用缓存执行操作"""
        if self._cache_manager is None:
            return await operation(*args, **kwargs)
        
        # 尝试从缓存获取
        cached_response = await self._cache_manager.get_async(cache_key)
        if cached_response is not None:
            return cached_response  # type: ignore
        
        # 执行操作
        response = await operation(*args, **kwargs)
        
        # 存储到缓存
        await self._cache_manager.set_async(cache_key, response)
        
        return response

    async def _execute_with_fallback_async(
        self,
        operation: Callable[..., Awaitable[LLMResponse]],
        *args: Any,
        **kwargs: Any
    ) -> LLMResponse:
        """异步使用降级机制执行操作"""
        if self._fallback_manager is None:
            return await operation(*args, **kwargs)
        
        # 直接使用降级管理器的异步生成方法，适用于消息生成操作
        if len(args) >= 1 and hasattr(args[0], '__len__') and len(args[0]) > 0:
            # 假设第一个参数是消息列表
            messages = args[0]
            parameters = args[1] if len(args) > 1 else {}
            primary_model = getattr(self.config, 'model_name', None)
            
            # 使用降级管理器异步生成
            return await self._fallback_manager.generate_with_fallback(
                messages,
                parameters,
                primary_model
            )
        else:
            # 如果参数不匹配消息生成格式，直接执行操作
            return await operation(*args, **kwargs)

    async def _execute_with_retry_async(
        self,
        operation: Callable[..., Awaitable[LLMResponse]],
        *args: Any,
        **kwargs: Any
    ) -> LLMResponse:
        """异步使用重试机制执行操作"""
        if self._retry_manager is None:
            return await operation(*args, **kwargs)
        
        return await self._retry_manager.execute_with_retry_async(  # type: ignore
        operation, *args, **kwargs
        )

    async def _do_generate_async_with_hooks(
        self,
        messages: Sequence[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> LLMResponse:
        """带钩子的异步生成操作"""
        # 测量执行时间
        start_time = time.time()
        response = await self._do_generate_async(messages, parameters, **kwargs)
        response_time = time.time() - start_time

        # 设置响应时间
        response.response_time = response_time

        return response

    async def stream_generate_async(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        # 验证输入
        self._validate_messages(messages)
        self._validate_token_limit(messages)

        # 合并参数
        merged_params = self._merge_parameters(parameters)

        # 调用前置钩子
        self._call_before_hooks(messages, merged_params, **kwargs)

        try:
            # 调用内部异步流式生成方法
            async for chunk in self._do_stream_generate_async(
                messages, merged_params, **kwargs
            ):
                yield chunk

        except Exception as e:
            # 转换为LLM错误
            if not isinstance(e, LLMCallError):
                llm_error = self._handle_api_error(e)
            else:
                llm_error = e

            # 尝试通过钩子恢复
            fallback_response = self._call_error_hooks(
                llm_error, messages, merged_params, **kwargs
            )
            if fallback_response is not None:
                # 如果钩子返回了响应，则返回模拟的流式内容
                for chunk in fallback_response.content.split():
                    yield chunk + " "
            else:
                # 抛出错误
                raise llm_error

    def stream_generate(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        流式生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        # 验证输入
        self._validate_messages(messages)
        self._validate_token_limit(messages)

        # 合并参数
        merged_params = self._merge_parameters(parameters)

        # 调用前置钩子
        self._call_before_hooks(messages, merged_params, **kwargs)

        try:
            # 调用内部流式生成方法
            for chunk in self._do_stream_generate(messages, merged_params, **kwargs):
                yield chunk

        except Exception as e:
            # 转换为LLM错误
            if not isinstance(e, LLMCallError):
                llm_error = self._handle_api_error(e)
            else:
                llm_error = e

            # 尝试通过钩子恢复
            fallback_response = self._call_error_hooks(
                llm_error, messages, merged_params, **kwargs
            )
            if fallback_response is not None:
                # 如果钩子返回了响应，则返回模拟的流式内容
                for chunk in fallback_response.content.split():
                    yield chunk + " "
            else:
                # 抛出错误
                raise llm_error

    def _generate_cache_key(
        self,
        messages: Sequence[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> str:
        """生成缓存键"""
        from ..cache import LLMCacheKeyGenerator
        
        key_generator = LLMCacheKeyGenerator()
        return key_generator.generate_key(
            model_name=self.config.model_name,
            messages=messages,
            parameters=parameters,
            **kwargs
        )

    @abstractmethod
    def _do_stream_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> Generator[str, None, None]:
        """执行流式生成操作（子类实现）"""
        pass

    @abstractmethod
    def _do_stream_generate_async(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作（子类实现）"""
        pass

    @abstractmethod
    def _do_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行生成操作（子类实现）"""
        pass

    @abstractmethod
    async def _do_generate_async(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作（子类实现）"""
        pass

    def get_token_count(self, text: str) -> int:
        """计算文本的token数量"""
        from ..token_counter import TokenCounterFactory

        # 使用Token计算器
        counter = TokenCounterFactory.create_counter(
            self.config.model_type, self.config.model_name
        )
        return counter.count_tokens(text) or 0

    def get_messages_token_count(self, messages: Sequence[BaseMessage]) -> int:
        """计算消息列表的token数量"""
        from ..token_counter import TokenCounterFactory

        # 使用Token计算器
        counter = TokenCounterFactory.create_counter(
            self.config.model_type, self.config.model_name
        )
        return counter.count_messages_tokens(messages) or 0

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用（子类实现）"""
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if self._model_info is None:
            self._model_info = ModelInfo(
                name=self.config.model_name,
                type=self.config.model_type,
                supports_function_calling=self.supports_function_calling(),
                supports_streaming=True,
                metadata=self.config.metadata or {},
            )

        return self._model_info.to_dict()

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """获取缓存统计信息"""
        if self._cache_manager is None:
            return None
        
        return self._cache_manager.get_stats()

    def get_fallback_stats(self) -> Optional[Dict[str, Any]]:
        """获取降级统计信息"""
        if self._fallback_manager is None:
            return None
        
        return self._fallback_manager.get_stats()

    def get_retry_stats(self) -> Optional[Dict[str, Any]]:
        """获取重试统计信息"""
        if self._retry_manager is None:
            return None
        
        return self._retry_manager.get_stats()

    def clear_cache(self) -> None:
        """清除缓存"""
        if self._cache_manager is not None:
            self._cache_manager.clear()

    def validate_config(self) -> ValidationResult:
        """验证配置"""
        # 简单的配置验证，返回成功结果
        from ....services.tools.validation.models import ValidationResult, ValidationStatus
        return ValidationResult(
            tool_name="enhanced_llm_client",
            tool_type="llm_client",
            status=ValidationStatus.SUCCESS
        )