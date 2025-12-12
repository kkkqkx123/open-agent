"""OpenAI 统一客户端 - 简化版本"""

from typing import Dict, Any, List, Generator, AsyncGenerator, Optional, cast, Sequence

from src.interfaces.messages import IBaseMessage

from ..base import BaseLLMClient
from src.interfaces.llm import LLMResponse
from src.interfaces.llm.exceptions import LLMCallError
from src.core.config.models import OpenAIConfig
from .chat_client import ChatClient
from .responses_client import ResponsesClient


class OpenAIClient(BaseLLMClient[OpenAIConfig]):
    """OpenAI 统一客户端 - 简化版本"""
    
    def __init__(self, config: OpenAIConfig) -> None:
        """
        初始化统一客户端
        
        Args:
            config: OpenAI 配置
        """
        super().__init__(config)
        self._client: Optional[BaseLLMClient] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """根据配置初始化客户端"""
        api_format = getattr(self.config, 'api_format', 'chat_completion')
        if api_format == 'chat_completion':
            # 使用 Chat 客户端
            self._client = ChatClient(self.config)
        elif api_format == 'responses':
            # 使用轻量级 Responses 客户端
            self._client = ResponsesClient(self.config)
        else:
            raise ValueError(f"不支持的 API 格式: {api_format}")
    
    def _get_client(self) -> BaseLLMClient:
        """获取客户端实例，确保不为 None"""
        if self._client is None:
            raise RuntimeError("客户端未初始化")
        return self._client
    
    async def _do_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        client = self._get_client()
        return await client.generate(messages, parameters, **kwargs)
    
    def _do_stream_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        async def _async_generator() -> AsyncGenerator[str, None]:
            client = self._get_client()
            async for chunk in client.stream_generate(messages, parameters, **kwargs):
                yield chunk

        return _async_generator()
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        client = self._get_client()
        return client.supports_function_calling()
    
    def switch_api_format(self, api_format: str) -> None:
        """
        切换 API 格式
        
        Args:
            api_format: 新的 API 格式
            
        Raises:
            ValueError: 不支持的 API 格式
        """
        if api_format not in ["chat_completion", "responses"]:
            raise ValueError(f"不支持的 API 格式: {api_format}")
        
        # 更新配置
        self.config.api_format = api_format
        
        # 重新初始化客户端
        self._initialize_client()
    
    def get_current_api_format(self) -> str:
        """
        获取当前使用的 API 格式
        
        Returns:
            str: 当前 API 格式
        """
        return getattr(self.config, 'api_format', 'chat_completion')
    
    def get_supported_api_formats(self) -> List[str]:
        """
        获取支持的 API 格式列表
        
        Returns:
            List[str]: 支持的 API 格式列表
        """
        return ["chat_completion", "responses"]
    
    async def generate_with_fallback(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        带降级的生成（简化版本）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
            
        Raises:
            LLMCallError: 所有 API 格式都失败
        """
        # 简化版本：直接使用当前格式
        # 如果需要降级功能，可以在这里实现
        return await self._do_generate_async(messages, parameters or {}, **kwargs)
    
    async def generate_with_fallback_async(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        带降级的异步生成（简化版本）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
            
        Raises:
            LLMCallError: 所有 API 格式都失败
        """
        # 简化版本：直接使用当前格式
        # 如果需要降级功能，可以在这里实现
        return await self._do_generate_async(messages, parameters or {}, **kwargs)
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        获取客户端信息
        
        Returns:
            Dict[str, Any]: 客户端信息
        """
        return {
            "api_format": self.get_current_api_format(),
            "model_name": self.config.model_name,
            "base_url": self.config.base_url,
            "supports_function_calling": self.supports_function_calling(),
            "client_type": type(self._client).__name__ if self._client else None,
        }
    
    def reset_conversation_history(self) -> None:
        """
        重置对话历史（仅对 Responses API 有效）
        """
        if self.config and hasattr(self.config, 'api_format') and self.config.api_format == 'responses' and isinstance(self._client, ResponsesClient):
            self._client._conversation_history.clear()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        获取对话历史（仅对 Responses API 有效）
        
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        if self.config and hasattr(self.config, 'api_format') and self.config.api_format == 'responses' and isinstance(self._client, ResponsesClient):
            return self._client._conversation_history.copy()
        return []
    
    def validate_config(self) -> bool:
        """
        验证配置
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必需的配置项
            if not self.config.model_name:
                return False
            
            if not self.config.api_key:
                return False
            
            # 检查 API 格式
            api_format = getattr(self.config, 'api_format', 'chat_completion')
            if api_format not in self.get_supported_api_formats():
                return False
            
            # 检查参数范围
            if not 0.0 <= self.config.temperature <= 2.0:
                return False
            
            if self.config.max_tokens is not None and self.config.max_tokens <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    