"""OpenAI 客户端接口定义"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, AsyncGenerator, Optional, Sequence

from langchain_core.messages import BaseMessage
from ...models import LLMResponse


class BaseOpenAIClient(ABC):
    """OpenAI 客户端基类接口"""
    
    def __init__(self, config) -> None:
        """
        初始化客户端
        
        Args:
            config: OpenAI 配置
        """
        self.config = config
    
    @abstractmethod
    def generate(self, messages: Sequence[BaseMessage], **kwargs: Any) -> LLMResponse:
        """
        同步生成响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        pass
    
    @abstractmethod
    async def generate_async(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> LLMResponse:
        """
        异步生成响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        pass
    
    @abstractmethod
    def stream_generate(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        同步流式生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
        """
        pass
    
    @abstractmethod
    async def stream_generate_async(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
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


class ChatCompletionClient(BaseOpenAIClient):
    """Chat Completions API 客户端接口"""
    
    def supports_function_calling(self) -> bool:
        """Chat Completions API 支持函数调用"""
        return True


class ResponsesAPIClient(BaseOpenAIClient):
    """Responses API 客户端接口"""
    
    def supports_function_calling(self) -> bool:
        """Responses API 支持函数调用"""
        return True
    
    @abstractmethod
    def _get_previous_response_id(self) -> Optional[str]:
        """
        获取之前的响应 ID（用于对话上下文）
        
        Returns:
            Optional[str]: 之前的响应 ID
        """
        pass
    
    @abstractmethod
    def _update_conversation_history(self, response: Dict[str, Any]) -> None:
        """
        更新对话历史
        
        Args:
            response: API 响应
        """
        pass
    
    @abstractmethod
    def _messages_to_input(self, messages: List[BaseMessage]) -> str:
        """
        将消息列表转换为 input 字符串
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 转换后的 input 字符串
        """
        pass