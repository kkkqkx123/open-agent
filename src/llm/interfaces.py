"""LLM模块核心接口定义"""

from abc import ABC, abstractmethod
from typing import (
    Dict,
    Any,
    Optional,
    List,
    AsyncGenerator,
    Union,
    Coroutine,
    Generator,
)
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .models import LLMResponse, TokenUsage


class ILLMClient(ABC):
    """LLM客户端接口"""

    @abstractmethod
    def __init__(self, config: Any) -> None:
        """
        初始化客户端

        Args:
            config: 客户端配置
        """
        pass

    @abstractmethod
    def generate(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
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
        pass

    @abstractmethod
    async def generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
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
        pass

    @abstractmethod
    def stream_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
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
        pass

    @abstractmethod
    def stream_generate(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
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
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """
        计算文本的token数量

        Args:
            text: 输入文本

        Returns:
            int: token数量
        """
        pass

    @abstractmethod
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """
        计算消息列表的token数量

        Args:
            messages: 消息列表

        Returns:
            int: token数量
        """
        pass

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """
        检查是否支持函数调用

        Returns:
            bool: 是否支持函数调用
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        pass


class ILLMCallHook(ABC):
    """LLM调用钩子接口"""

    @abstractmethod
    def before_call(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """
        调用前的钩子

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
        """
        pass

    @abstractmethod
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """
        调用后的钩子

        Args:
            response: 生成的响应
            messages: 原始消息列表
            parameters: 生成参数
            **kwargs: 其他参数
        """
        pass

    @abstractmethod
    def on_error(
        self,
        error: Exception,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[LLMResponse]:
        """
        错误处理钩子

        Args:
            error: 发生的错误
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            Optional[LLMResponse]: 如果可以恢复，返回替代响应；否则返回None
        """
        pass


class ILLMClientFactory(ABC):
    """LLM客户端工厂接口"""

    @abstractmethod
    def create_client(self, config: Dict[str, Any]) -> ILLMClient:
        """
        创建LLM客户端实例

        Args:
            config: 客户端配置

        Returns:
            ILLMClient: 客户端实例
        """
        pass

    @abstractmethod
    def get_cached_client(self, model_name: str) -> Optional[ILLMClient]:
        """
        获取缓存的客户端实例

        Args:
            model_name: 模型名称

        Returns:
            Optional[ILLMClient]: 缓存的客户端实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def cache_client(self, model_name: str, client: ILLMClient) -> None:
        """
        缓存客户端实例

        Args:
            model_name: 模型名称
            client: 客户端实例
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """清除所有缓存的客户端实例"""
        pass
