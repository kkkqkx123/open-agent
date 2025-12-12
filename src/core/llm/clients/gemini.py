"""Gemini客户端实现"""

from typing import Dict, Any, Optional, List, AsyncGenerator, Union, Sequence

from src.interfaces.messages import IBaseMessage
from src.infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage
from src.interfaces.llm.http_client import ILLMHttpClient

from .base import BaseLLMClient
from src.interfaces.llm import LLMResponse
from src.infrastructure.llm.models import TokenUsage
from src.core.config.models import GeminiConfig
from src.interfaces.llm.exceptions import (
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
)

class GeminiClient(BaseLLMClient[GeminiConfig]):
    """Gemini客户端实现"""

    def __init__(self, config: GeminiConfig) -> None:
        """
        初始化Gemini客户端

        Args:
            config: Gemini配置
        """
        super().__init__(config)
        self._http_client: Optional[ILLMHttpClient] = None
    
    def set_http_client(self, http_client: ILLMHttpClient) -> None:
        """设置HTTP客户端
        
        Args:
            http_client: HTTP客户端实例
        """
        self._http_client = http_client

    def _convert_messages(self, messages: Sequence[IBaseMessage]) -> List[IBaseMessage]:
        """转换消息格式以适应Gemini API"""
        converted_messages: List[IBaseMessage] = []

        for message in messages:
            if isinstance(message, SystemMessage):
                # Gemini不直接支持系统消息，将其转换为用户消息
                converted_messages.append(
                    HumanMessage(content=f"系统指令: {message.content}")
                )
            else:
                converted_messages.append(message)

        return converted_messages

    async def _do_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        if self._http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        try:
            # 转换消息格式
            converted_messages = self._convert_messages_to_gemini_format(messages)

            # 准备请求参数
            request_params = self._prepare_request_params(parameters, **kwargs)

            # 调用基础设施层HTTP客户端
            response = await self._http_client.generate_content(
                contents=converted_messages,
                **request_params
            )

            # 提取Token使用情况
            token_usage = self._extract_token_usage(response)

            # 提取函数调用信息
            function_call = self._extract_function_call(response)

            # 创建响应对象
            return self._create_response(
                content=self._extract_content(response),
                message=response,
                token_usage=token_usage,
                finish_reason=self._extract_finish_reason(response),
                function_call=function_call,
            )

        except Exception as e:
            # 处理Gemini特定错误
            raise self._handle_gemini_error(e)
    
    def _convert_messages_to_gemini_format(self, messages: Sequence[IBaseMessage]) -> List[Dict[str, Any]]:
        """转换消息为Gemini格式
        
        Args:
            messages: 消息列表
            
        Returns:
            List[Dict[str, Any]]: Gemini格式的消息列表
        """
        gemini_messages = []
        system_instruction = None
        
        for message in messages:
            if isinstance(message, SystemMessage):
                # Gemini将系统指令作为单独的参数
                system_instruction = message.content
            else:
                gemini_message = {
                    "role": self._get_message_role(message),
                    "parts": [{"text": str(message.content)}]
                }
                gemini_messages.append(gemini_message)
        
        # 如果有系统指令，将其添加到第一个用户消息中
        if system_instruction and gemini_messages:
            first_message = gemini_messages[0]
            if first_message["role"] == "user":
                parts = first_message["parts"]
                if isinstance(parts, list):
                    parts.insert(0, {
                        "text": f"系统指令: {system_instruction}"
                    })
        
        return gemini_messages
    
    def _get_message_role(self, message: IBaseMessage) -> str:
        """获取消息角色"""
        if isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, AIMessage):
            return "model"
        else:
            # 根据类型属性判断
            if hasattr(message, 'type'):
                if message.type == "human":
                    return "user"
                elif message.type == "ai":
                    return "model"
            
            # 默认为用户消息
            return "user"
    
    def _prepare_request_params(self, parameters: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """准备请求参数
        
        Args:
            parameters: 合并后的参数
            **kwargs: 额外参数
            
        Returns:
            Dict[str, Any]: 请求参数
        """
        # 基础参数
        params = {
            "model": self.config.model_name,
            "temperature": self.config.temperature,
        }
        
        # 从配置中获取Gemini特定参数
        if self.config.max_output_tokens:
            params["max_output_tokens"] = self.config.max_output_tokens
        
        if self.config.top_p != 1.0:
            params["top_p"] = self.config.top_p
        
        if self.config.top_k:
            params["top_k"] = self.config.top_k
        
        if self.config.stop_sequences:
            params["stop_sequences"] = self.config.stop_sequences
        
        if self.config.candidate_count:
            params["candidate_count"] = self.config.candidate_count
        
        if self.config.response_mime_type:
            params["response_mime_type"] = self.config.response_mime_type
        
        if self.config.thinking_config:
            params["thinking_config"] = self.config.thinking_config
        
        if self.config.safety_settings:
            params["safety_settings"] = self.config.safety_settings
        
        # 工具调用参数
        if self.config.tools:
            params["tools"] = self.config.tools
            if self.config.tool_choice:
                params["tool_choice"] = self.config.tool_choice
        
        # 缓存参数
        if self.config.content_cache_enabled and self.config.content_cache_display_name:
            params["cached_content"] = self.config.content_cache_display_name
        
        # 添加传入的参数
        params.update(parameters)
        params.update(kwargs)
        
        return params


    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # 从配置中读取是否支持函数调用
        return getattr(self.config, 'function_calling_supported', True)

    def _extract_token_usage(self, response: Any) -> TokenUsage:
        """提取Token使用情况 - 使用基础设施层的TokenResponseParser"""
        try:
            # 导入基础设施层的Token响应解析器
            from src.infrastructure.llm.token_calculators.token_response_parser import get_token_response_parser
            
            # 将响应转换为字典格式（如果需要）
            if hasattr(response, 'dict'):
                response_dict = response.dict()
            elif hasattr(response, '__dict__'):
                response_dict = response.__dict__
            else:
                response_dict = response
            
            # 使用基础设施层的解析器
            parser = get_token_response_parser()
            token_usage = parser.parse_response(response_dict, "gemini")
            
            # 如果解析失败，返回空的TokenUsage
            if token_usage is None:
                return TokenUsage()
            
            return token_usage
            
        except Exception as e:
            # 如果使用基础设施层解析器失败，回退到基本实现
            from src.interfaces.dependency_injection import get_logger
            logger = get_logger(__name__)
            logger.warning(f"使用基础设施层Token解析器失败，回退到基本实现: {e}")
            return self._extract_token_usage_fallback(response)
    
    def _extract_token_usage_fallback(self, response: Any) -> TokenUsage:
        """Token提取的回退实现"""
        token_usage = TokenUsage()
        
        # 基本的token提取逻辑
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            token_usage.prompt_tokens = usage.get("input_tokens", 0)
            token_usage.completion_tokens = usage.get("output_tokens", 0)
            token_usage.total_tokens = usage.get("total_tokens", 0)
        
        return token_usage

    def _extract_function_call(self, response: Any) -> Optional[Dict[str, Any]]:
        """提取函数调用信息"""
        return self._extract_function_call_enhanced(response)

    def _extract_finish_reason(self, response: Any) -> Optional[str]:
        """提取完成原因"""
        if hasattr(response, "response_metadata") and response.response_metadata:
            metadata = response.response_metadata
            finish_reason = metadata.get("finish_reason")
            if isinstance(finish_reason, str):
                return finish_reason
        return None

    def _extract_content(self, response: Any) -> str:
        """提取响应内容，处理多种内容格式"""
        content = response.content

        # 如果内容是字符串，直接返回
        if isinstance(content, str):
            return content

        # 如果内容是列表，提取文本内容
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                # 忽略其他类型的元素
            return "".join(text_parts)

        # 其他类型转换为字符串
        return str(content)

    def _handle_gemini_error(self, error: Exception) -> LLMCallError:
        """处理Gemini特定错误"""
        error_str = str(error).lower()

        # 尝试从错误中提取更多信息
        try:
            # 检查是否有response属性
            response = getattr(error, "response", None)
            if response is not None:
                # 检查是否有status_code属性
                status_code = getattr(response, "status_code", None)
                if status_code is not None:
                    if status_code == 401 or status_code == 403:
                        return self._create_enhanced_error(
                            LLMAuthenticationError,
                            "Gemini API密钥无效或权限不足",
                            error
                        )
                    elif status_code == 429:
                        retry_after = None
                        headers = getattr(response, "headers", None)
                        if headers and "retry-after" in headers:
                            retry_after = int(headers["retry-after"])
                        return self._create_enhanced_error(
                            LLMRateLimitError,
                            "Gemini API频率限制",
                            error,
                            retry_after=retry_after
                        )
                    elif status_code == 404:
                        return self._create_enhanced_error(
                            LLMModelNotFoundError,
                            f"模型未找到: {self.config.model_name}",
                            error
                        )
                    elif status_code == 400:
                        return self._create_enhanced_error(
                            LLMInvalidRequestError,
                            "Gemini API请求无效",
                            error
                        )
                    elif status_code == 500 or status_code == 502 or status_code == 503:
                        return self._create_enhanced_error(
                            LLMServiceUnavailableError,
                            "Gemini服务不可用",
                            error
                        )
        except (AttributeError, ValueError, TypeError):
            # 如果访问属性时出错，忽略并继续执行其他错误检查
            pass

        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            return self._create_enhanced_error(
                LLMTimeoutError,
                f"请求超时: {str(error)}",
                error,
                timeout=self.config.timeout
            )
        elif (
            "rate limit" in error_str
            or "quota" in error_str
            or "too many requests" in error_str
        ):
            return self._create_enhanced_error(
                LLMRateLimitError,
                f"API频率限制: {str(error)}",
                error
            )
        elif (
            "permission" in error_str
            or "forbidden" in error_str
            or "authentication" in error_str
        ):
            return self._create_enhanced_error(
                LLMAuthenticationError,
                f"认证错误: {str(error)}",
                error
            )
        elif "model not found" in error_str or "not found" in error_str:
            return self._create_enhanced_error(
                LLMModelNotFoundError,
                f"模型未找到: {self.config.model_name}",
                error
            )
        elif "token" in error_str and "limit" in error_str:
            return self._create_enhanced_error(
                LLMTokenLimitError,
                f"Token限制: {str(error)}",
                error
            )
        elif (
            "content filter" in error_str
            or "safety" in error_str
            or "blocked" in error_str
        ):
            return self._create_enhanced_error(
                LLMContentFilterError,
                f"内容过滤: {str(error)}",
                error
            )
        elif "service unavailable" in error_str or "503" in error_str:
            return self._create_enhanced_error(
                LLMServiceUnavailableError,
                f"服务不可用: {str(error)}",
                error
            )
        elif "invalid request" in error_str or "bad request" in error_str:
            return self._create_enhanced_error(
                LLMInvalidRequestError,
                f"无效请求: {str(error)}",
                error
            )
        else:
            return self._create_enhanced_error(
                LLMCallError,
                f"Gemini API错误: {str(error)}",
                error
            )

    def _do_stream_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        if self._http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        http_client = self._http_client
        
        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 转换消息格式
                converted_messages = self._convert_messages_to_gemini_format(messages)

                # 准备请求参数
                request_params = self._prepare_request_params(parameters, **kwargs)

                # 异步流式生成
                # stream_generate_content 返回 Coroutine[Any, Any, AsyncGenerator]，需要await
                generator_coro = http_client.stream_generate_content(
                    contents=converted_messages,
                    **request_params
                )
                generator = await generator_coro
                async for chunk in generator:
                    if chunk.get("candidates"):
                        candidate = chunk["candidates"][0]
                        if candidate.get("content"):
                            parts = candidate["content"].get("parts", [])
                            for part in parts:
                                if part.get("text"):
                                    yield part["text"]

            except Exception as e:
                # 处理Gemini特定错误
                raise self._handle_gemini_error(e)

        return _async_generator()
