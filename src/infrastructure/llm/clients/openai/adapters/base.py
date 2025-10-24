"""API格式适配器基类"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, AsyncGenerator, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ....models import LLMResponse
    from langchain_core.messages import BaseMessage # type: ignore


class APIFormatAdapter(ABC):
    """API格式适配器基类"""

    def __init__(self, config: Any) -> None:
        """
        初始化适配器

        Args:
            config: OpenAI配置
        """
        self.config = config
        self._client: Any = None

    @abstractmethod
    def initialize_client(self) -> None:
        """初始化底层客户端"""
        pass

    @abstractmethod
    def generate(self, messages: List["BaseMessage"], **kwargs: Any) -> "LLMResponse":
        """同步生成响应"""
        pass

    @abstractmethod
    async def generate_async(
        self, messages: List["BaseMessage"], **kwargs: Any
    ) -> "LLMResponse":
        """异步生成响应"""
        pass

    @abstractmethod
    def stream_generate(
        self, messages: List["BaseMessage"], **kwargs: Any
    ) -> Generator[str, None, None]:
        """同步流式生成"""
        pass

    @abstractmethod
    async def stream_generate_async(
        self, messages: List["BaseMessage"], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """异步流式生成"""
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """计算文本token数量"""
        pass

    @abstractmethod
    def get_messages_token_count(self, messages: List["BaseMessage"]) -> int:
        """计算消息列表token数量"""
        pass

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """是否支持函数调用"""
        pass

    def _handle_error(self, error: Exception) -> Exception:
        """
        处理API错误

        Args:
            error: 原始错误

        Returns:
            Exception: 处理后的错误
        """
        # 默认实现，子类可以重写
        return error

    def _merge_parameters(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并参数

        Args:
            parameters: 传入的参数

        Returns:
            Dict[str, Any]: 合并后的参数
        """
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