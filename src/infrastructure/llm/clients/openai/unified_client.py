"""OpenAI 统一客户端 - 简化版本"""

from typing import Dict, Any, List, Generator, AsyncGenerator, Optional, cast, Sequence

from langchain_core.messages import BaseMessage

from ..base import BaseLLMClient
from ...models import LLMResponse
from ...exceptions import LLMCallError
from .config import OpenAIConfig
from .langchain_client import LangChainChatClient
from .responses_client import LightweightResponsesClient
from .interfaces import BaseOpenAIClient


class OpenAIUnifiedClient(BaseLLMClient):
    """OpenAI 统一客户端 - 简化版本"""
    
    def __init__(self, config: OpenAIConfig) -> None:
        """
        初始化统一客户端
        
        Args:
            config: OpenAI 配置
        """
        super().__init__(config)
        self._config: OpenAIConfig = config  # 明确指定类型
        self._client: Optional[BaseOpenAIClient] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """根据配置初始化客户端"""
        if self._config.is_chat_completion():
            # 使用 LangChain Chat 客户端
            self._client = LangChainChatClient(self._config)
        elif self._config.is_responses_api():
            # 使用轻量级 Responses 客户端
            self._client = LightweightResponsesClient(self._config)
        else:
            raise ValueError(f"不支持的 API 格式: {self._config.api_format}")
    
    def _get_client(self) -> BaseOpenAIClient:
        """获取客户端实例，确保不为 None"""
        if self._client is None:
            raise RuntimeError("客户端未初始化")
        return self._client
    
    def _do_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行生成操作"""
        client = self._get_client()
        return client.generate(messages, **parameters, **kwargs)
    
    async def _do_generate_async(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        client = self._get_client()
        return await client.generate_async(messages, **parameters, **kwargs)
    
    def _do_stream_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> Generator[str, None, None]:
        """执行流式生成操作"""
        client = self._get_client()
        result = client.stream_generate(messages, **parameters, **kwargs)
        return cast(Generator[str, None, None], result)
    
    async def _do_stream_generate_async(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        client = self._get_client()
        async_gen_coroutine = client.stream_generate_async(
            messages, **parameters, **kwargs
        )
        async_gen = await async_gen_coroutine
        async for chunk in async_gen:
            yield chunk
    
    def get_token_count(self, text: str) -> int:
        """计算文本 token 数量"""
        client = self._get_client()
        result = client.get_token_count(text)
        return cast(int, result)
    
    def get_messages_token_count(self, messages: Sequence[BaseMessage]) -> int:
        """计算消息列表 token 数量"""
        client = self._get_client()
        result = client.get_messages_token_count(messages)
        return cast(int, result)
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        client = self._get_client()
        result = client.supports_function_calling()
        return cast(bool, result)
    
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
        self._config.api_format = api_format
        
        # 重新初始化客户端
        self._initialize_client()
    
    def get_current_api_format(self) -> str:
        """
        获取当前使用的 API 格式
        
        Returns:
            str: 当前 API 格式
        """
        return self._config.api_format
    
    def get_supported_api_formats(self) -> List[str]:
        """
        获取支持的 API 格式列表
        
        Returns:
            List[str]: 支持的 API 格式列表
        """
        return ["chat_completion", "responses"]
    
    def generate_with_fallback(
        self,
        messages: Sequence[BaseMessage],
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
        return self.generate(messages, parameters, **kwargs)
    
    async def generate_with_fallback_async(
        self,
        messages: Sequence[BaseMessage],
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
        return await self.generate_async(messages, parameters, **kwargs)
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        获取客户端信息
        
        Returns:
            Dict[str, Any]: 客户端信息
        """
        return {
            "api_format": self.get_current_api_format(),
            "model_name": self._config.model_name,
            "base_url": self._config.base_url,
            "supports_function_calling": self.supports_function_calling(),
            "client_type": type(self._client).__name__ if self._client else None,
        }
    
    def reset_conversation_history(self) -> None:
        """
        重置对话历史（仅对 Responses API 有效）
        """
        if self._config.is_responses_api() and isinstance(self._client, LightweightResponsesClient):
            self._client._conversation_history.clear()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        获取对话历史（仅对 Responses API 有效）
        
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        if self._config.is_responses_api() and isinstance(self._client, LightweightResponsesClient):
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
            if not self._config.model_name:
                return False
            
            if not self._config.api_key:
                return False
            
            # 检查 API 格式
            if self._config.api_format not in self.get_supported_api_formats():
                return False
            
            # 检查参数范围
            if not 0.0 <= self._config.temperature <= 2.0:
                return False
            
            if self._config.max_tokens is not None and self._config.max_tokens <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_estimated_cost(self, messages: Sequence[BaseMessage]) -> Optional[float]:
        """
        估算请求成本（简化版本）
        
        Args:
            messages: 消息列表
            
        Returns:
            Optional[float]: 估算成本（美元），如果无法估算则返回 None
        """
        try:
            # 获取 token 数量
            token_count = self.get_messages_token_count(messages)
            
            # 简化的成本计算（基于 GPT-4 的定价）
            # 实际实现应该根据具体模型和定价来计算
            if "gpt-4" in self._config.model_name.lower():
                input_cost_per_1k = 0.03  # GPT-4 输入成本
                output_cost_per_1k = 0.06  # GPT-4 输出成本
            elif "gpt-3.5" in self._config.model_name.lower():
                input_cost_per_1k = 0.0015  # GPT-3.5 输入成本
                output_cost_per_1k = 0.002  # GPT-3.5 输出成本
            else:
                # 未知模型，无法估算
                return None
            
            # 估算输出 token 数量（通常是输入的 1/3 到 1/2）
            estimated_output_tokens = max(token_count // 3, 100)
            
            # 计算总成本
            input_cost = (token_count / 1000) * input_cost_per_1k
            output_cost = (estimated_output_tokens / 1000) * output_cost_per_1k
            total_cost = input_cost + output_cost
            
            return round(total_cost, 6)
            
        except Exception:
            return None