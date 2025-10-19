"""Chat Completion格式转换器"""

from typing import Any, Optional

from langchain_core.messages import BaseMessage  # type: ignore
from ....models import LLMResponse, TokenUsage
from .base import MessageConverter


class ChatCompletionConverter(MessageConverter):
    """Chat Completion格式转换器"""

    def to_api_format(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """
        转换为Chat Completion API格式

        Args:
            messages: LangChain消息列表

        Returns:
            list[BaseMessage]: Chat Completion API直接使用LangChain消息格式
        """
        # Chat Completion API直接使用LangChain消息格式
        return messages

    def from_api_format(self, api_response: Any) -> LLMResponse:
        """
        从Chat Completion响应转换为统一格式

        Args:
            api_response: Chat Completion API响应

        Returns:
            LLMResponse: 统一格式的响应
        """
        # 提取Token使用情况
        token_usage = self._extract_token_usage(api_response)

        # 提取函数调用信息
        function_call = self._extract_function_call(api_response)

        # 提取完成原因
        finish_reason = self._extract_finish_reason(api_response)

        # 提取内容
        content = self._extract_content(api_response)

        # 创建响应对象
        return LLMResponse(
            content=content,
            message=api_response,
            token_usage=token_usage,
            model=getattr(api_response, "model", "unknown"),
            finish_reason=finish_reason,
            function_call=function_call,
            metadata=getattr(api_response, "response_metadata", {}),
        )

    def _extract_token_usage(self, response: Any) -> TokenUsage:
        """
        提取Token使用情况

        Args:
            response: Chat Completion响应

        Returns:
            TokenUsage: Token使用情况
        """
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            return TokenUsage(
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
        elif hasattr(response, "response_metadata") and response.response_metadata:
            metadata = response.response_metadata
            if "token_usage" in metadata:
                usage = metadata["token_usage"]
                return TokenUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                )

        return TokenUsage()

    def _extract_function_call(self, response: Any) -> Optional[dict[str, Any]]:
        """
        提取函数调用信息

        Args:
            response: Chat Completion响应

        Returns:
            Optional[dict[str, Any]]: 函数调用信息
        """
        if (
            hasattr(response, "additional_kwargs")
            and "function_call" in response.additional_kwargs
        ):
            function_call = response.additional_kwargs["function_call"]
            if isinstance(function_call, dict):
                return function_call
        return None

    def _extract_finish_reason(self, response: Any) -> Optional[str]:
        """
        提取完成原因

        Args:
            response: Chat Completion响应

        Returns:
            Optional[str]: 完成原因
        """
        if hasattr(response, "response_metadata") and response.response_metadata:
            metadata = response.response_metadata
            finish_reason = metadata.get("finish_reason")
            if isinstance(finish_reason, str):
                return finish_reason
        return None
