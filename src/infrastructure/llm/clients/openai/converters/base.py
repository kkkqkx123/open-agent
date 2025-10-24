"""消息格式转换器基类"""

from abc import ABC, abstractmethod
from typing import List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

from ....models import LLMResponse


class MessageConverter(ABC):
    """消息格式转换器基类"""

    @abstractmethod
    def to_api_format(self, messages: List["BaseMessage"]) -> Any:
        """
        转换为API特定格式

        Args:
            messages: LangChain消息列表

        Returns:
            Any: API特定格式的消息
        """
        pass

    @abstractmethod
    def from_api_format(self, api_response: Any) -> LLMResponse:
        """
        从API响应转换为统一格式

        Args:
            api_response: API响应

        Returns:
            LLMResponse: 统一格式的响应
        """
        pass

    def _extract_content(self, response: Any) -> str:
        """
        提取响应内容，处理多种内容格式

        Args:
            response: API响应

        Returns:
            str: 提取的文本内容
        """
        # 默认实现，子类可以重写
        if hasattr(response, "content"):
            content = response.content

            # 如果内容是字符串，直接返回
            if isinstance(content, str):
                return content

            # 如果内容是列表，提取文本内容
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                    # 忽略其他类型的元素
                return "".join(text_parts)

            # 其他类型转换为字符串
            return str(content)

        return str(response)

    def _extract_token_usage(self, response: Any) -> Any:
        """
        提取Token使用情况

        Args:
            response: API响应

        Returns:
            Any: Token使用情况
        """
        # 默认实现，子类应该重写
        from ....models import TokenUsage

        return TokenUsage()

    def _extract_function_call(self, response: Any) -> Any:
        """
        提取函数调用信息

        Args:
            response: API响应

        Returns:
            Any: 函数调用信息
        """
        # 默认实现，子类可以重写
        return None

    def _extract_finish_reason(self, response: Any) -> Any:
        """
        提取完成原因

        Args:
            response: API响应

        Returns:
            Any: 完成原因
        """
        # 默认实现，子类可以重写
        return None
