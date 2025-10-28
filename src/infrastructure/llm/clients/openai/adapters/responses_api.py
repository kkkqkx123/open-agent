"""Responses API适配器"""

from typing import Dict, Any, Generator, AsyncGenerator, List, Optional, Union, cast
from langchain_core.messages import BaseMessage

from .base import APIFormatAdapter
from ..native_client import OpenAIResponsesClient
from ..converters.responses_converter import ResponsesConverter
from ....exceptions import (
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
from ....models import LLMResponse


class ResponsesAPIAdapter(APIFormatAdapter):
    """Responses API适配器"""

    def __init__(self, config: Any) -> None:
        """
        初始化Responses API适配器

        Args:
            config: OpenAI配置
        """
        super().__init__(config)
        self.converter = ResponsesConverter()
        self._conversation_history: List[Dict[str, Any]] = []
        # 显式声明_client的类型
        self._client: Optional[OpenAIResponsesClient] = None

    def initialize_client(self) -> None:
        """初始化Responses API客户端"""
        if self._client is None:
            self._client = OpenAIResponsesClient(self.config)

    def generate(self, messages: List[BaseMessage], **kwargs: Any) -> LLMResponse:
        """生成响应"""
        self.initialize_client()

        # 转换消息为input格式
        input_text = self.converter.messages_to_input(messages)

        # 获取之前的响应ID（如果有）
        previous_response_id = self._get_previous_response_id()

        try:
            # 调用Responses API
            if self._client is not None:
                api_response = self._client.create_response_sync(
                    input_text=input_text,
                    previous_response_id=previous_response_id,
                    **kwargs,
                )
            else:
                raise LLMCallError("客户端未初始化")

            # 转换响应格式
            llm_response = self.converter.from_api_format(api_response)

            # 更新对话历史
            self._update_conversation_history(api_response)

            return llm_response

        except Exception as e:
            # 错误处理
            raise self._handle_openai_error(e)

    async def generate_async(self, messages: List[BaseMessage], **kwargs: Any) -> LLMResponse:
        """异步生成响应"""
        self.initialize_client()

        # 转换消息为input格式
        input_text = self.converter.messages_to_input(messages)

        # 获取之前的响应ID（如果有）
        previous_response_id = self._get_previous_response_id()

        try:
            # 调用Responses API
            if self._client is not None:
                api_response = await self._client.create_response(
                    input_text=input_text,
                    previous_response_id=previous_response_id,
                    **kwargs,
                )
            else:
                raise LLMCallError("客户端未初始化")

            # 转换响应格式
            llm_response = self.converter.from_api_format(api_response)

            # 更新对话历史
            self._update_conversation_history(api_response)

            return llm_response

        except Exception as e:
            # 错误处理
            raise self._handle_openai_error(e)

    def stream_generate(
        self, messages: List[BaseMessage], **kwargs: Any
    ) -> Generator[str, None, None]:
        """流式生成"""
        self.initialize_client()

        # 转换消息为input格式
        input_text = self.converter.messages_to_input(messages)

        # 获取之前的响应ID（如果有）
        previous_response_id = self._get_previous_response_id()

        try:
            # 调用Responses API流式接口
            if self._client is not None:
                for chunk in self._client.create_stream_response_sync(
                    input_text=input_text,
                    previous_response_id=previous_response_id,
                    **kwargs,
                ):
                    # 提取文本内容
                    content = self._extract_stream_content(chunk)
                    if content:
                        yield content
            else:
                raise LLMCallError("客户端未初始化")

        except Exception as e:
            # 错误处理
            raise self._handle_openai_error(e)

    async def stream_generate_async(
        self, messages: List[BaseMessage], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """异步流式生成"""
        self.initialize_client()

        # 转换消息为input格式
        input_text = self.converter.messages_to_input(messages)

        # 获取之前的响应ID（如果有）
        previous_response_id = self._get_previous_response_id()

        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 调用Responses API流式接口
                if self._client is not None:
                    async for chunk in self._client.create_stream_response(
                        input_text=input_text,
                        previous_response_id=previous_response_id,
                        **kwargs,
                    ):
                        # 提取文本内容
                        content = self._extract_stream_content(chunk)
                        if content:
                            yield content
                else:
                    raise LLMCallError("客户端未初始化")

            except Exception as e:
                # 错误处理
                raise self._handle_openai_error(e)

        return _async_generator()

    def get_token_count(self, text: str) -> int:
        """计算文本token数量"""
        from ....token_counter import TokenCounterFactory

        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        result = counter.count_tokens(text)
        return result if result is not None else 0

    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表token数量"""
        from ....token_counter import TokenCounterFactory

        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        result = counter.count_messages_tokens(messages)
        return result if result is not None else 0

    def supports_function_calling(self) -> bool:
        """Responses API支持函数调用"""
        return True

    def _get_previous_response_id(self) -> Optional[str]:
        """获取之前的响应ID"""
        if self._conversation_history:
            return self._conversation_history[-1].get("id")
        return None

    def _update_conversation_history(self, response: Dict[str, Any]) -> None:
        """更新对话历史"""
        self._conversation_history.append(response)

        # 限制历史记录长度
        max_history = 10
        if len(self._conversation_history) > max_history:
            self._conversation_history = self._conversation_history[-max_history:]

    def _extract_stream_content(self, chunk: Dict[str, Any]) -> str:
        """
        从流式响应块中提取文本内容

        Args:
            chunk: 流式响应块

        Returns:
            str: 提取的文本内容
        """
        # 检查是否是完成信号
        if chunk.get("type") == "done":
            return ""

        # 提取输出内容
        output_items = chunk.get("output", [])
        for item in output_items:
            if item.get("type") == "message":
                content = item.get("content", [])
                for content_item in content:
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text", "")
                        # 确保返回的是字符串类型
                        return str(text) if text is not None else ""

        return ""

    def _handle_openai_error(self, error: Exception) -> LLMCallError:
        """处理OpenAI特定错误"""
        error_str = str(error).lower()

        # 尝试从错误中提取更多信息
        try:
            # 检查是否有response属性
            response = getattr(error, "response", None)
            if response is not None:
                # 检查是否有status_code属性
                status_code = getattr(response, "status_code", None)
                if status_code is not None:
                    if status_code == 401:
                        return LLMAuthenticationError("OpenAI API密钥无效")
                    elif status_code == 429:
                        retry_after = None
                        headers = getattr(response, "headers", None)
                        if headers and "retry-after" in headers:
                            retry_after = int(headers["retry-after"])
                        return LLMRateLimitError(
                            "OpenAI API频率限制", retry_after=retry_after
                        )
                    elif status_code == 404:
                        return LLMModelNotFoundError(self.config.model_name)
                    elif status_code == 400:
                        return LLMInvalidRequestError("OpenAI API请求无效")
                    elif status_code == 500 or status_code == 502 or status_code == 503:
                        return LLMServiceUnavailableError("OpenAI服务不可用")
        except (AttributeError, ValueError, TypeError):
            # 如果访问属性时出错，忽略并继续执行其他错误检查
            pass

        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            return LLMTimeoutError(str(error), timeout=self.config.timeout)
        elif "rate limit" in error_str or "too many requests" in error_str:
            return LLMRateLimitError(str(error))
        elif (
            "authentication" in error_str
            or "unauthorized" in error_str
            or "invalid api key" in error_str
        ):
            return LLMAuthenticationError(str(error))
        elif "model not found" in error_str or "not found" in error_str:
            return LLMModelNotFoundError(self.config.model_name)
        elif "token" in error_str and "limit" in error_str:
            return LLMTokenLimitError(str(error))
        elif "content filter" in error_str or "content policy" in error_str:
            return LLMContentFilterError(str(error))
        elif "service unavailable" in error_str or "503" in error_str:
            return LLMServiceUnavailableError(str(error))
        elif "invalid request" in error_str or "bad request" in error_str:
            return LLMInvalidRequestError(str(error))
        else:
            return LLMCallError(str(error))