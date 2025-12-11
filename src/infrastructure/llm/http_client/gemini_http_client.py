"""Gemini HTTP客户端实现

实现Google Gemini API的HTTP通信，支持多模态内容和工具调用。
"""

import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Union, Sequence
from httpx import Response

from src.interfaces.llm.http_client import ILLMHttpClient
from src.infrastructure.llm.http_client.base_http_client import BaseHttpClient
from src.infrastructure.llm.converters.providers.gemini import GeminiProvider
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.interfaces.dependency_injection import get_logger
from src.interfaces.messages import IBaseMessage


class GeminiHttpClient(BaseHttpClient, ILLMHttpClient):
    """Gemini HTTP客户端
    
    实现Google Gemini API的HTTP通信，支持：
    - 多模态内容（文本、图像、音频、视频）
    - 流式响应
    - 工具调用
    - 安全设置
    """
    
    # 支持的模型列表
    SUPPORTED_MODELS = [
        # Gemini 2.5系列
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        
        # 3.0系列
        "gemini-3.0-pro", "gemini-3.0-flash"
    ]
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any
    ):
        """初始化Gemini HTTP客户端
        
        Args:
            api_key: Google API密钥
            base_url: 基础URL（可选，默认使用官方API）
            **kwargs: 其他参数传递给BaseHttpClient
        """
        # 设置默认基础URL
        if base_url is None:
            base_url = "https://generativelanguage.googleapis.com/v1"
        
        # 设置默认请求头
        default_headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        super().__init__(base_url=base_url, default_headers=default_headers, **kwargs)
        
        # 初始化格式转换器
        self.format_utils = GeminiProvider()
        self.api_key = api_key
        
        self.logger.info("初始化Gemini HTTP客户端")
    
    async def chat_completions(
        self,
        messages: Sequence["IBaseMessage"],
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """调用Gemini API
        
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
            
            # 构建端点URL
            endpoint = f"models/{model}:generateContent"
            
            self.logger.debug(
                f"调用Gemini API",
                extra={
                    "model": model,
                    "message_count": len(messages),
                    "stream": stream,
                    "parameters": list(request_params.keys())
                }
            )
            
            if stream:
                return self._stream_gemini_response(request_data, endpoint)
            else:
                response = await self.post(endpoint, request_data)
                return self._convert_gemini_response(response, model)
                
        except Exception as e:
            self.logger.error(f"Gemini API调用失败: {e}")
            raise
    
    async def _stream_gemini_response(
        self, request_data: Dict[str, Any], endpoint: str
    ) -> AsyncGenerator[str, None]:
        """处理Gemini流式响应
        
        Args:
            request_data: 请求数据
            endpoint: API端点
            
        Yields:
            str: 流式响应数据片段
        """
        try:
            async for chunk in self.stream_post(endpoint, request_data):
                # Gemini流式响应格式
                if chunk.strip():
                    try:
                        data = json.loads(chunk)
                        # 提取内容
                        content = self._extract_content_from_gemini_stream(data)
                        if content:
                            yield content
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"解析Gemini流式数据失败: {e}, 数据: {chunk}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"处理Gemini流式响应失败: {e}")
            raise
    
    def _convert_gemini_response(self, response: Response, model: str) -> LLMResponse:
        """转换Gemini响应
        
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
            usage_metadata = data.get("usageMetadata", {})
            token_usage = TokenUsage(
                prompt_tokens=usage_metadata.get("promptTokenCount", 0),
                completion_tokens=usage_metadata.get("candidatesTokenCount", 0),
                total_tokens=usage_metadata.get("totalTokenCount", 0)
            )
            
            # 提取完成原因
            candidates = data.get("candidates", [])
            finish_reason = candidates[0].get("finishReason") if candidates else None
            
            # 确保内容是字符串类型
            content_value = message.content if hasattr(message, 'content') else str(message)
            content_str = content_value if isinstance(content_value, str) else str(content_value)
            
            return LLMResponse(
               content=content_str,
               message=message,
               token_usage=token_usage,
               model=model,
               finish_reason=finish_reason,
               metadata={
                   "model_version": data.get("modelVersion"),
                   "usage_metadata": usage_metadata
               }
            )
            
        except Exception as e:
            self.logger.error(f"转换Gemini响应失败: {e}")
            raise
    
    def _extract_content_from_gemini_stream(self, data: Dict[str, Any]) -> Optional[str]:
        """从Gemini流式响应中提取内容
        
        Args:
            data: 流式响应数据
            
        Returns:
            Optional[str]: 提取的内容
        """
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            
            candidate = candidates[0]
            content_parts = candidate.get("content", {}).get("parts", [])
            
            if content_parts:
                return content_parts[0].get("text", "") or None
            
            return None
            
        except Exception as e:
            self.logger.warning(f"提取Gemini流式内容失败: {e}")
            return None
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return "gemini"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型名称列表
        """
        return self.SUPPORTED_MODELS.copy()