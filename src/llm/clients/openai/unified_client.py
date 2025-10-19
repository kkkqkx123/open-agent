"""OpenAI统一客户端，支持多种API格式"""

from typing import Dict, Any, List, Generator, AsyncGenerator, Optional, Union, cast

from langchain_core.messages import BaseMessage

from ..base import BaseLLMClient
from ...models import LLMResponse
from ...exceptions import LLMCallError
from .adapters.chat_completion import ChatCompletionAdapter
from .adapters.responses_api import ResponsesAPIAdapter
from .adapters.base import APIFormatAdapter
from .config import OpenAIConfig


class OpenAIUnifiedClient(BaseLLMClient):
    """OpenAI统一客户端，支持多种API格式"""

    def __init__(self, config: OpenAIConfig) -> None:
        """
        初始化统一客户端

        Args:
            config: OpenAI配置
        """
        super().__init__(config)
        self._adapter: Optional[APIFormatAdapter] = None
        self._initialize_adapter()

    def _initialize_adapter(self) -> None:
        """根据配置初始化适配器"""
        api_format = getattr(self.config, "api_format", "chat_completion")

        if api_format == "chat_completion":
            self._adapter = ChatCompletionAdapter(self.config)
        elif api_format == "responses":
            self._adapter = ResponsesAPIAdapter(self.config)
        else:
            raise ValueError(f"不支持的API格式: {api_format}")

    def _get_adapter(self) -> APIFormatAdapter:
        """获取适配器实例，确保不为None"""
        if self._adapter is None:
            raise RuntimeError("适配器未初始化")
        return self._adapter

    def _do_generate(
        self, messages: List[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行生成操作"""
        adapter = self._get_adapter()
        return adapter.generate(messages, **parameters, **kwargs)

    async def _do_generate_async(
        self, messages: List[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        adapter = self._get_adapter()
        return await adapter.generate_async(messages, **parameters, **kwargs)

    def _do_stream_generate(
        self, messages: List[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> Generator[str, None, None]:
        """执行流式生成操作"""
        adapter = self._get_adapter()
        result = adapter.stream_generate(messages, **parameters, **kwargs)
        return cast(Generator[str, None, None], result)

    async def _do_stream_generate_async(
        self, messages: List[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        adapter = self._get_adapter()
        async_gen_coroutine = adapter.stream_generate_async(
            messages, **parameters, **kwargs
        )
        async_gen = await async_gen_coroutine
        async for chunk in async_gen:
            yield chunk

    def get_token_count(self, text: str) -> int:
        """计算文本token数量"""
        adapter = self._get_adapter()
        result = adapter.get_token_count(text)
        return cast(int, result)

    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表token数量"""
        adapter = self._get_adapter()
        result = adapter.get_messages_token_count(messages)
        return cast(int, result)

    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        adapter = self._get_adapter()
        result = adapter.supports_function_calling()
        return cast(bool, result)

    def switch_api_format(self, api_format: str) -> None:
        """
        切换API格式

        Args:
            api_format: 新的API格式

        Raises:
            ValueError: 不支持的API格式
            AttributeError: 配置不支持API格式切换
        """
        if hasattr(self.config, "api_format"):
            # 类型转换，确保配置是OpenAIConfig
            openai_config = cast(OpenAIConfig, self.config)
            openai_config.api_format = api_format
            self._initialize_adapter()
        else:
            raise AttributeError("配置不支持API格式切换")

    def get_current_api_format(self) -> str:
        """
        获取当前使用的API格式

        Returns:
            str: 当前API格式
        """
        return getattr(self.config, "api_format", "chat_completion")

    def get_supported_api_formats(self) -> List[str]:
        """
        获取支持的API格式列表

        Returns:
            List[str]: 支持的API格式列表
        """
        return ["chat_completion", "responses"]

    def generate_with_fallback(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        带降级的生成

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应

        Raises:
            LLMCallError: 所有API格式都失败
        """
        if not getattr(self.config, "fallback_enabled", False):
            # 如果未启用降级，直接使用当前格式
            return self.generate(messages, parameters, **kwargs)

        # 获取降级格式列表
        openai_config = cast(OpenAIConfig, self.config)
        fallback_formats = openai_config.get_fallback_formats()

        # 尝试当前格式
        try:
            return self.generate(messages, parameters, **kwargs)
        except LLMCallError as e:
            # 记录错误
            current_format = self.get_current_api_format()
            print(f"API格式 {current_format} 失败: {e}")

            # 尝试降级格式
            for fallback_format in fallback_formats:
                try:
                    # 切换到降级格式
                    original_format = self.get_current_api_format()
                    self.switch_api_format(fallback_format)

                    # 尝试生成
                    response = self.generate(messages, parameters, **kwargs)

                    # 恢复原始格式
                    self.switch_api_format(original_format)

                    return response
                except LLMCallError as fallback_error:
                    print(f"降级格式 {fallback_format} 也失败: {fallback_error}")
                    continue

            # 所有格式都失败，恢复原始格式并抛出错误
            self.switch_api_format(current_format)
            raise LLMCallError("所有API格式都失败")

    async def generate_with_fallback_async(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        带降级的异步生成

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应

        Raises:
            LLMCallError: 所有API格式都失败
        """
        if not getattr(self.config, "fallback_enabled", False):
            # 如果未启用降级，直接使用当前格式
            return await self.generate_async(messages, parameters, **kwargs)

        # 获取降级格式列表
        openai_config = cast(OpenAIConfig, self.config)
        fallback_formats = openai_config.get_fallback_formats()

        # 尝试当前格式
        try:
            return await self.generate_async(messages, parameters, **kwargs)
        except LLMCallError as e:
            # 记录错误
            current_format = self.get_current_api_format()
            print(f"API格式 {current_format} 失败: {e}")

            # 尝试降级格式
            for fallback_format in fallback_formats:
                try:
                    # 切换到降级格式
                    original_format = self.get_current_api_format()
                    self.switch_api_format(fallback_format)

                    # 尝试生成
                    response = await self.generate_async(messages, parameters, **kwargs)

                    # 恢复原始格式
                    self.switch_api_format(original_format)

                    return response
                except LLMCallError as fallback_error:
                    print(f"降级格式 {fallback_format} 也失败: {fallback_error}")
                    continue

            # 所有格式都失败，恢复原始格式并抛出错误
            self.switch_api_format(current_format)
            raise LLMCallError("所有API格式都失败")
