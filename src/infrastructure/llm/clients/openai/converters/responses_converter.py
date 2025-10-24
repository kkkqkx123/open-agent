"""Responses API格式转换器"""

from typing import Any, Optional

from langchain_core.messages import BaseMessage  # type: ignore
from ....models import LLMResponse, TokenUsage
from .base import MessageConverter


class ResponsesConverter(MessageConverter):
    """Responses API格式转换器"""

    def messages_to_input(self, messages: list[BaseMessage]) -> str:
        """
        将消息列表转换为input字符串

        Args:
            messages: LangChain消息列表

        Returns:
            str: 转换后的input字符串
        """
        # 简单实现：连接所有消息内容
        # 实际实现可能需要更复杂的逻辑
        input_parts = []

        for message in messages:
            if hasattr(message, "content"):
                content = str(message.content)
                if hasattr(message, "type"):
                    if message.type == "system":
                        input_parts.append(f"System: {content}")
                    elif message.type == "human":
                        input_parts.append(f"User: {content}")
                    elif message.type == "ai":
                        input_parts.append(f"Assistant: {content}")
                else:
                    # 根据消息类型判断
                    if hasattr(message, 'type'):
                        if message.type == "system":
                            input_parts.append(f"System: {content}")
                        elif message.type == "human":
                            input_parts.append(f"User: {content}")
                        elif message.type == "ai":
                            input_parts.append(f"Assistant: {content}")
                        else:
                            input_parts.append(content)
                    else:
                        input_parts.append(content)

        return "\n".join(input_parts)

    def to_api_format(self, messages: list[BaseMessage]) -> str:
        """
        转换为Responses API格式

        Args:
            messages: LangChain消息列表

        Returns:
            str: Responses API的input格式
        """
        return self.messages_to_input(messages)

    def from_api_format(self, api_response: dict[str, Any]) -> LLMResponse:
        """
        从Responses API响应转换为统一格式

        Args:
            api_response: Responses API响应

        Returns:
            LLMResponse: 统一格式的响应
        """
        # 提取输出内容
        content = self._extract_output_text(api_response)

        # 提取Token使用情况
        token_usage = self._extract_token_usage(api_response)

        # 提取函数调用
        function_call = self._extract_function_call(api_response)

        # 提取完成原因
        finish_reason = self._extract_finish_reason(api_response)

        # 创建LangChain消息
        try:
            from langchain_core.messages import AIMessage
            message = AIMessage(content=content)
        except ImportError:
            # 如果无法导入langchain，使用domain层的BaseMessage
            from src.domain.prompts.agent_state import BaseMessage
            message = BaseMessage(content=content, type="ai")

        # 确保消息对象兼容LLMResponse期望的类型
        # 使用类型转换来处理不同类型的BaseMessage
        return LLMResponse(
            content=content,
            message=message, # type: ignore
            token_usage=token_usage,
            model=api_response.get("model", "unknown"),
            finish_reason=finish_reason,
            function_call=function_call,
            metadata={
                "response_id": api_response.get("id"),
                "object": api_response.get("object"),
                "created_at": api_response.get("created_at"),
                "output_items": api_response.get("output", []),
            },
        )

    def _extract_output_text(self, response: dict[str, Any]) -> str:
        """
        提取输出文本

        Args:
            response: Responses API响应

        Returns:
            str: 输出文本
        """
        output_items = response.get("output", [])

        for item in output_items:
            if item.get("type") == "message":
                content = item.get("content", [])
                for content_item in content:
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text", "")
                        return str(text) if text is not None else ""

        return ""

    def _extract_token_usage(self, response: dict[str, Any]) -> TokenUsage:
        """
        提取Token使用情况

        Args:
            response: Responses API响应

        Returns:
            TokenUsage: Token使用情况
        """
        # Responses API的Token使用情况可能在不同的字段中
        usage = response.get("usage", {})

        return TokenUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    def _extract_function_call(
        self, response: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        提取函数调用信息

        Args:
            response: Responses API响应

        Returns:
            Optional[dict[str, Any]]: 函数调用信息
        """
        output_items = response.get("output", [])

        for item in output_items:
            if item.get("type") == "function_call":
                return {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "arguments": item.get("arguments"),
                }

        return None

    def _extract_finish_reason(self, response: dict[str, Any]) -> Optional[str]:
        """
        提取完成原因

        Args:
            response: Responses API响应

        Returns:
            Optional[str]: 完成原因
        """
        # Responses API可能使用不同的字段名
        return response.get("status") or response.get("finish_reason")
