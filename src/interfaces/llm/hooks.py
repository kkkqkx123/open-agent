"""LLM钩子接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Sequence, TYPE_CHECKING
from .base import LLMResponse

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage


class ILLMCallHook(ABC):
    """LLM调用钩子接口"""

    @abstractmethod
    def before_call(
        self,
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
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
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
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
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
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