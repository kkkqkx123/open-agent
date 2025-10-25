"""Chat Completion API适配器"""

from typing import Dict, Any, Generator, AsyncGenerator, List, Optional

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from .base import APIFormatAdapter
from ..converters.chat_completion_converter import ChatCompletionConverter
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


class ChatCompletionAdapter(APIFormatAdapter):
    """Chat Completion API适配器"""

    def __init__(self, config: Any) -> None:
        """
        初始化Chat Completion适配器

        Args:
            config: OpenAI配置
        """
        super().__init__(config)
        self.converter: ChatCompletionConverter = ChatCompletionConverter()
        self._client: Optional[ChatOpenAI] = None

    def initialize_client(self) -> None:
        """初始化LangChain ChatOpenAI客户端"""
        if self._client is None:
            # 获取解析后的HTTP标头
            resolved_headers = self.config.get_resolved_headers()

            # 准备模型参数
            model_kwargs: Dict[str, Any] = {}

            # 基础参数
            if self.config.max_tokens is not None:
                model_kwargs["max_tokens"] = self.config.max_tokens
            if self.config.max_completion_tokens is not None:
                model_kwargs["max_completion_tokens"] = (
                    self.config.max_completion_tokens
                )

            # 惩罚参数
            if self.config.frequency_penalty != 0.0:
                model_kwargs["frequency_penalty"] = self.config.frequency_penalty
            if self.config.presence_penalty != 0.0:
                model_kwargs["presence_penalty"] = self.config.presence_penalty

            # 停止序列
            if self.config.stop is not None:
                model_kwargs["stop"] = self.config.stop

            # 采样参数
            if self.config.top_logprobs is not None:
                model_kwargs["logprobs"] = self.config.top_logprobs

            # 工具调用参数
            if self.config.tools:
                model_kwargs["functions"] = self.config.tools
                if self.config.function_call is not None:
                    model_kwargs["function_call"] = self.config.function_call
            if self.config.tool_choice is not None:
                model_kwargs["tool_choice"] = self.config.tool_choice

            # 响应格式
            if self.config.response_format is not None:
                model_kwargs["response_format"] = self.config.response_format

            # 流式选项
            if self.config.stream_options is not None:
                model_kwargs["stream_options"] = self.config.stream_options

            # 服务层
            if self.config.service_tier is not None:
                model_kwargs["service_tier"] = self.config.service_tier

            # 安全标识符
            if self.config.safety_identifier is not None:
                model_kwargs["safety_identifier"] = self.config.safety_identifier

            # 存储选项
            if self.config.store:
                model_kwargs["store"] = self.config.store

            # 推理参数
            if self.config.reasoning is not None:
                model_kwargs["reasoning"] = self.config.reasoning

            # 详细程度
            if self.config.verbosity is not None:
                model_kwargs["verbosity"] = self.config.verbosity

            # 网络搜索选项
            if self.config.web_search_options is not None:
                model_kwargs["web_search_options"] = self.config.web_search_options

            # 种子
            if self.config.seed is not None:
                model_kwargs["seed"] = self.config.seed

            # 用户标识
            if self.config.user is not None:
                model_kwargs["user"] = self.config.user

            # 转换 api_key 为 SecretStr 类型
            api_key = SecretStr(self.config.api_key) if self.config.api_key else None

            # 构建超时配置
            timeout_config = getattr(self.config, 'timeout_config', None)
            if timeout_config and hasattr(timeout_config, 'get_client_timeout_kwargs'):
                # 使用新的超时配置
                timeout_kwargs = timeout_config.get_client_timeout_kwargs()
                # LangChain OpenAI客户端接受一个整体超时值
                timeout_value = timeout_kwargs.get('request_timeout', self.config.timeout)
            else:
                # 使用旧的超时配置
                timeout_value = self.config.timeout
            
            self._client = ChatOpenAI(
                model=self.config.model_name,
                api_key=api_key,
                base_url=self.config.base_url,
                organization=getattr(self.config, "organization", None),
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                timeout=timeout_value,
                max_retries=self.config.max_retries,
                model_kwargs=model_kwargs,
            )

    def generate(self, messages: List[BaseMessage], **kwargs: Any) -> Any:
        """生成响应"""
        self.initialize_client()

        try:
            # 调用ChatOpenAI
            if self._client is None:
                raise ValueError("客户端未初始化")
            response = self._client.invoke(messages, **kwargs)

            # 转换响应格式
            return self.converter.from_api_format(response)

        except Exception as e:
            # 错误处理
            raise self._handle_openai_error(e)

    async def generate_async(self, messages: List[BaseMessage], **kwargs: Any) -> Any:
        """异步生成响应"""
        self.initialize_client()

        try:
            # 调用ChatOpenAI
            if self._client is None:
                raise ValueError("客户端未初始化")
            response = await self._client.ainvoke(messages, **kwargs)

            # 转换响应格式
            return self.converter.from_api_format(response)

        except Exception as e:
            # 错误处理
            raise self._handle_openai_error(e)

    def stream_generate(
        self, messages: List[BaseMessage], **kwargs: Any
    ) -> Generator[str, None, None]:
        """流式生成"""
        self.initialize_client()

        try:
            # 流式生成
            if self._client is None:
                raise ValueError("客户端未初始化")
            stream = self._client.stream(messages, **kwargs)

            # 收集完整响应
            for chunk in stream:
                if chunk.content:
                    # 使用_extract_content方法确保返回字符串类型
                    content = self.converter._extract_content(chunk)
                    if content:
                        yield content

        except Exception as e:
            # 错误处理
            raise self._handle_openai_error(e)

    async def stream_generate_async(
        self, messages: List[BaseMessage], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """异步流式生成"""
        self.initialize_client()

        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 异步流式生成
                if self._client is None:
                    raise ValueError("客户端未初始化")
                stream = self._client.astream(messages, **kwargs)

                # 收集完整响应
                async for chunk in stream:
                    if chunk.content:
                        # 使用_extract_content方法确保返回字符串类型
                        content = self.converter._extract_content(chunk)
                        if content:
                            yield content

            except Exception as e:
                # 错误处理
                raise self._handle_openai_error(e)

        return _async_generator()

    def get_token_count(self, text: str) -> int:
        """计算文本token数量"""
        from ....token_counter import TokenCounterFactory

        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        return counter.count_tokens(text)

    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表token数量"""
        from ....token_counter import TokenCounterFactory

        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        return counter.count_messages_tokens(messages)

    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        return True

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
