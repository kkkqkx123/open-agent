"""Anthropic HTTP客户端实现

实现Anthropic Claude API的HTTP通信，支持长文本和工具调用。
"""

import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Union, Sequence
from httpx import Response

from src.interfaces.llm.http_client import ILLMHttpClient
from src.infrastructure.llm.http_client.base_http_client import BaseHttpClient
from src.infrastructure.llm.converters.providers.anthropic import AnthropicProvider
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.interfaces.dependency_injection import get_logger
from src.interfaces.messages import IBaseMessage


class AnthropicHttpClient(BaseHttpClient, ILLMHttpClient):
    """Anthropic HTTP客户端
    
    实现Anthropic Claude API的HTTP通信，支持：
    - 长文本处理
    - 流式响应
    - 工具调用
    - 系统提示
    """
    
    # 支持的模型列表
    SUPPORTED_MODELS = [
        # Claude 3.5系列
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        
        # Claude 4系列
        "claude-4.1-opus",
        "claude-4.0-sonnet", 
        
        # 4.5系列
        "claude-4.5-opus",
        "claude-4.5-sonnet",
        "claude-4.5-haiku"
    ]
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any
    ):
        """初始化Anthropic HTTP客户端
        
        Args:
            api_key: Anthropic API密钥
            base_url: 基础URL（可选，默认使用官方API）
            **kwargs: 其他参数传递给BaseHttpClient
        """
        # 设置默认基础URL
        if base_url is None:
            base_url = "https://api.anthropic.com"
        
        # 设置默认请求头
        default_headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        super().__init__(base_url=base_url, default_headers=default_headers, **kwargs)
        
        # 初始化格式转换器
        self.format_utils = AnthropicProvider()
        self.api_key = api_key
        
        self.logger.info("初始化Anthropic HTTP客户端")
    
    async def chat_completions(
        self,
        messages: Sequence["IBaseMessage"],
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """调用Anthropic Messages API
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 请求参数
            stream: 是否流式响应
            
        Returns:
            Union[LLMResponse, AsyncGenerator[str, None]]: 响应对象或流式生成器
        """
        # 准备参数
        request_params = parameters or {}
        request_params["model"] = model
        request_params["stream"] = stream
        
        # 验证模型
        if model not in self.SUPPORTED_MODELS:
            self.logger.warning(f"模型 {model} 不在支持列表中，但仍会尝试调用")
        
        try:
            # 转换请求格式
            request_data = self.format_utils.convert_request(messages, request_params)
            
            self.logger.debug(
                f"调用Anthropic Messages API",
                extra={
                    "model": model,
                    "message_count": len(messages),
                    "stream": stream,
                    "parameters": list(request_params.keys())
                }
            )
            
            if stream:
                return self._stream_anthropic_response(request_data)
            else:
                response = await self.post("messages", request_data)
                return self._convert_anthropic_response(response, model)
                
        except Exception as e:
            self.logger.error(f"Anthropic API调用失败: {e}")
            raise
    
    async def _stream_anthropic_response(
        self, request_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """处理Anthropic流式响应
        
        Args:
            request_data: 请求数据
            
        Yields:
            str: 流式响应数据片段
        """
        try:
            async for chunk in self.stream_post("messages", request_data):
                # Anthropic流式响应格式
                if chunk.startswith("data: "):
                    data_str = chunk[6:]  # 移除 "data: " 前缀
                    
                    # 跳过事件标记
                    if data_str.startswith("event: "):
                        continue
                    
                    try:
                        data = json.loads(data_str)
                        # 提取内容
                        content = self._extract_content_from_anthropic_stream(data)
                        if content:
                            yield content
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"解析Anthropic流式数据失败: {e}, 数据: {data_str}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"处理Anthropic流式响应失败: {e}")
            raise
    
    def _convert_anthropic_response(self, response: Response, model: str) -> LLMResponse:
        """转换Anthropic响应
        
        Args:
            response: HTTP响应对象
            model: 模型名称
            
        Returns:
            LLMResponse: LLM响应对象
        """
        try:
            data = response.json()
            
            # 使用格式转换器转换响应
            message = self.format_utils.convert_response(data)
            
            # 提取token使用情况
            usage = data.get("usage", {})
            token_usage = TokenUsage(
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            )
            
            # 提取停止原因
            stop_reason = data.get("stop_reason")
            
            # 确保内容是字符串类型
            content_value = message.content if hasattr(message, 'content') else str(message)
            content_str = content_value if isinstance(content_value, str) else str(content_value)
            
            return LLMResponse(
                content=content_str,
                message=message,
                token_usage=token_usage,
                model=model,
                finish_reason=stop_reason,
                metadata={
                    "id": data.get("id"),
                    "type": data.get("type"),
                    "role": data.get("role"),
                    "usage": usage
                }
            )
            
        except Exception as e:
            self.logger.error(f"转换Anthropic响应失败: {e}")
            raise
    
    def _extract_content_from_anthropic_stream(self, data: Dict[str, Any]) -> Optional[str]:
        """从Anthropic流式响应中提取内容
        
        Args:
            data: 流式响应数据
            
        Returns:
            Optional[str]: 提取的内容
        """
        try:
            # 检查是否为内容块
            if data.get("type") == "content_block_delta":
                delta = data.get("delta", {})
                return delta.get("text") or None
            
            # 检查是否为消息开始
            elif data.get("type") == "message_start":
                message = data.get("message", {})
                content = message.get("content", [])
                if content and isinstance(content, list):
                    return content[0].get("text", "") or None
            
            return None
            
        except Exception as e:
            self.logger.warning(f"提取Anthropic流式内容失败: {e}")
            return None
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return "anthropic"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型名称列表
        """
        return self.SUPPORTED_MODELS.copy()