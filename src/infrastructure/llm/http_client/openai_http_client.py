"""OpenAI HTTP客户端实现

实现OpenAI API的HTTP通信，包括Chat Completions和Responses API。
"""

import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Union, Sequence
from httpx import Response

from src.interfaces.llm.http_client import ILLMHttpClient
from src.infrastructure.llm.http_client.base_http_client import BaseHttpClient
from src.infrastructure.llm.converters.openai.openai_format_utils import OpenAIFormatUtils
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.services.logger import get_logger

# 使用 TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage


class OpenAIHttpClient(BaseHttpClient, ILLMHttpClient):
    """OpenAI HTTP客户端
    
    实现OpenAI API的HTTP通信，支持：
    - Chat Completions API
    - Responses API (GPT-5)
    - 流式响应
    - 工具调用
    """
    
    # 支持的模型列表
    SUPPORTED_MODELS = [
        # GPT-4系列
        "gpt-4", "gpt-4-32k", "gpt-4-0613", "gpt-4-32k-0613",
        "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-turbo-preview",
        "gpt-4o", "gpt-4o-2024-05-13", "gpt-4o-2024-08-06",
        "gpt-4o-mini", "gpt-4o-mini-2024-07-18",
        
        # GPT-3.5系列
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613", "gpt-3.5-turbo-0301",
        
        # GPT-5系列（假设的未来模型）
        "gpt-5", "gpt-5-codex", "gpt-5.1",
        
        # 其他模型
        "text-davinci-003", "text-davinci-002", "text-curie-001",
        "text-babbage-001", "text-ada-001"
    ]
    
    def __init__(
        self,
        api_key: str,
        api_version: str = "v1",
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs
    ):
        """初始化OpenAI HTTP客户端
        
        Args:
            api_key: OpenAI API密钥
            api_version: API版本
            base_url: 基础URL（可选，默认使用官方API）
            organization: 组织ID（可选）
            **kwargs: 其他参数传递给BaseHttpClient
        """
        # 设置默认基础URL
        if base_url is None:
            base_url = f"https://api.openai.com/{api_version}"
        
        # 设置默认请求头
        default_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 添加组织头（如果有）
        if organization:
            default_headers["OpenAI-Organization"] = organization
        
        super().__init__(base_url=base_url, default_headers=default_headers, **kwargs)
        
        # 初始化格式转换器
        self.format_utils = OpenAIFormatUtils()
        self.api_version = api_version
        self.api_key = api_key
        
        self.logger.info(f"初始化OpenAI HTTP客户端，API版本: {api_version}")
    
    async def chat_completions(
        self,
        messages: Sequence["IBaseMessage"],
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """调用Chat Completions API
        
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
                f"调用Chat Completions API",
                extra={
                    "model": model,
                    "message_count": len(messages),
                    "stream": stream,
                    "parameters": list(request_params.keys())
                }
            )
            
            if stream:
                return self._stream_chat_response(request_data)
            else:
                response = await self.post("chat/completions", request_data)
                return self._convert_chat_response(response)
                
        except Exception as e:
            self.logger.error(f"Chat Completions API调用失败: {e}")
            raise
    
    async def responses_api(
        self,
        input_text: str,
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """调用Responses API (GPT-5)
        
        Args:
            input_text: 输入文本
            model: 模型名称
            parameters: 请求参数
            stream: 是否流式响应
            
        Returns:
            Union[LLMResponse, AsyncGenerator[str, None]]: 响应对象或流式生成器
        """
        # 准备参数
        request_params = parameters or {}
        request_params["model"] = model
        request_params["input"] = input_text
        request_params["stream"] = stream
        
        try:
            # 构建Responses API请求数据
            request_data = self._build_responses_request(request_params)
            
            self.logger.debug(
                f"调用Responses API",
                extra={
                    "model": model,
                    "stream": stream,
                    "parameters": list(request_params.keys())
                }
            )
            
            if stream:
                return self._stream_responses_response(request_data)
            else:
                response = await self.post("responses", request_data)
                return self._convert_responses_response(response)
                
        except Exception as e:
            self.logger.error(f"Responses API调用失败: {e}")
            raise
    
    async def _stream_chat_response(
        self, request_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """处理Chat Completions流式响应
        
        Args:
            request_data: 请求数据
            
        Yields:
            str: 流式响应数据片段
        """
        try:
            async for chunk in self.stream_post("chat/completions", request_data):
                # 解析SSE格式的数据
                if chunk.startswith("data: "):
                    data_str = chunk[6:]  # 移除 "data: " 前缀
                    
                    # 跳过结束标记
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        # 提取内容
                        content = self._extract_content_from_stream_chunk(data)
                        if content:
                            yield content
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"解析流式数据失败: {e}, 数据: {data_str}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"处理Chat Completions流式响应失败: {e}")
            raise
    
    async def _stream_responses_response(
        self, request_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """处理Responses流式响应
        
        Args:
            request_data: 请求数据
            
        Yields:
            str: 流式响应数据片段
        """
        try:
            async for chunk in self.stream_post("responses", request_data):
                # 解析SSE格式的数据
                if chunk.startswith("data: "):
                    data_str = chunk[6:]  # 移除 "data: " 前缀
                    
                    # 跳过结束标记
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        # 提取内容
                        content = self._extract_content_from_responses_chunk(data)
                        if content:
                            yield content
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"解析Responses流式数据失败: {e}, 数据: {data_str}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"处理Responses流式响应失败: {e}")
            raise
    
    def _convert_chat_response(self, response: Response) -> LLMResponse:
        """转换Chat Completions响应
        
        Args:
            response: HTTP响应对象
            
        Returns:
            LLMResponse: LLM响应对象
        """
        try:
            data = response.json()
            
            # 使用格式转换器转换响应
            message = self.format_utils.convert_response(data)
            
            # 提取token使用情况
            usage_data = data.get("usage", {})
            token_usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
            
            # 提取完成原因
            choices = data.get("choices", [])
            finish_reason = choices[0].get("finish_reason") if choices else None
            
            return LLMResponse(
                content=message.content if hasattr(message, 'content') else str(message),
                message=message,
                token_usage=token_usage,
                model=data.get("model", ""),
                finish_reason=finish_reason,
                metadata={
                    "id": data.get("id", ""),
                    "created": data.get("created"),
                    "system_fingerprint": data.get("system_fingerprint"),
                    "service_tier": data.get("service_tier")
                }
            )
            
        except Exception as e:
            self.logger.error(f"转换Chat Completions响应失败: {e}")
            raise
    
    def _convert_responses_response(self, response: Response) -> LLMResponse:
        """转换Responses API响应
        
        Args:
            response: HTTP响应对象
            
        Returns:
            LLMResponse: LLM响应对象
        """
        try:
            data = response.json()
            
            # 提取基本信息
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Responses API响应中没有choices字段")
            
            choice = choices[0]
            message_data = choice.get("message", {})
            
            # 创建基础设施层消息
            from src.infrastructure.messages import AIMessage
            message = AIMessage(
                content=message_data.get("content", ""),
                additional_kwargs={
                    "finish_reason": choice.get("finish_reason"),
                    "model": data.get("model", ""),
                    "id": data.get("id", ""),
                    "created": data.get("created")
                }
            )
            
            # 提取token使用情况（包含推理token）
            usage_data = data.get("usage", {})
            token_usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                reasoning_tokens=usage_data.get("reasoning_tokens", 0)
            )
            
            return LLMResponse(
                content=message.content,
                message=message,
                token_usage=token_usage,
                model=data.get("model", ""),
                finish_reason=choice.get("finish_reason"),
                metadata={
                    "id": data.get("id", ""),
                    "created": data.get("created"),
                    "object": data.get("object", "")
                }
            )
            
        except Exception as e:
            self.logger.error(f"转换Responses API响应失败: {e}")
            raise
    
    def _build_responses_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """构建Responses API请求数据
        
        Args:
            parameters: 请求参数
            
        Returns:
            Dict[str, Any]: 请求数据
        """
        request_data = {
            "model": parameters["model"],
            "input": parameters["input"],
            "stream": parameters.get("stream", False)
        }
        
        # 处理推理配置
        if "reasoning_effort" in parameters:
            request_data["reasoning"] = {
                "effort": parameters["reasoning_effort"]
            }
        
        # 处理文本配置
        if "verbosity" in parameters:
            request_data["text"] = {
                "verbosity": parameters["verbosity"]
            }
        
        # 处理工具
        if "tools" in parameters:
            request_data["tools"] = self._convert_responses_tools(parameters["tools"])
        
        # 处理对话连续性
        if "previous_response_id" in parameters:
            request_data["previous_response_id"] = parameters["previous_response_id"]
        
        return request_data
    
    def _convert_responses_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换为Responses API工具格式
        
        Args:
            tools: 工具列表
            
        Returns:
            List[Dict[str, Any]]: Responses API格式的工具列表
        """
        responses_tools = []
        
        for tool in tools:
            responses_tool = {
                "type": "custom",
                "name": tool["name"],
                "description": tool.get("description", "")
            }
            
            responses_tools.append(responses_tool)
        
        return responses_tools
    
    def _extract_content_from_stream_chunk(self, data: Dict[str, Any]) -> Optional[str]:
        """从流式响应块中提取内容
        
        Args:
            data: 流式响应数据
            
        Returns:
            Optional[str]: 提取的内容
        """
        try:
            choices = data.get("choices", [])
            if not choices:
                return None
            
            choice = choices[0]
            delta = choice.get("delta", {})
            return delta.get("content")
            
        except Exception as e:
            self.logger.warning(f"提取流式内容失败: {e}")
            return None
    
    def _extract_content_from_responses_chunk(self, data: Dict[str, Any]) -> Optional[str]:
        """从Responses流式响应块中提取内容
        
        Args:
            data: 流式响应数据
            
        Returns:
            Optional[str]: 提取的内容
        """
        try:
            # Responses API的流式格式可能不同
            if "content" in data:
                return data["content"]
            
            choices = data.get("choices", [])
            if not choices:
                return None
            
            choice = choices[0]
            if "content" in choice:
                return choice["content"]
            
            delta = choice.get("delta", {})
            return delta.get("content")
            
        except Exception as e:
            self.logger.warning(f"提取Responses流式内容失败: {e}")
            return None
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return "openai"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型名称列表
        """
        return self.SUPPORTED_MODELS.copy()