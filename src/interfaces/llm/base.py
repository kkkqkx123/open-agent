"""LLM基础接口定义"""

from abc import ABC, abstractmethod
from typing import (
    Dict,
    Any,
    Optional,
    List,
    AsyncGenerator,
    Generator,
    Sequence,
    TYPE_CHECKING,
)
from dataclasses import dataclass

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from ...interfaces.messages import IBaseMessage
    from .http_client import ILLMHttpClient


@dataclass
class LLMResponse:
    """LLM响应数据模型"""
    
    content: str  # 响应内容
    model: Optional[str] = None  # 使用的模型名称
    finish_reason: Optional[str] = None  # 完成原因（stop/length/tool_calls等）
    tokens_used: Optional[int] = None  # 使用的token数量
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据


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
    async def generate(
        self,
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        生成文本响应（异步）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成文本响应（异步）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
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
    
    def supports_jsonl(self) -> bool:
        """
        检查是否支持JSONL格式

        Returns:
            bool: 是否支持JSONL格式
        """
        return False
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        pass
    
    def set_http_client(self, http_client: "ILLMHttpClient") -> None:
        """设置HTTP客户端
        
        Args:
            http_client: HTTP客户端实例
        """
        pass