"""Anthropic客户端实现"""

from typing import Dict, Any, Optional, List, AsyncGenerator, Generator, Union, Sequence

from src.interfaces.messages import IBaseMessage
from src.infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage
from src.interfaces.llm.http_client import ILLMHttpClient

from .base import BaseLLMClient
from src.interfaces.llm import LLMResponse
from src.infrastructure.llm.models import TokenUsage
from src.core.config.models import AnthropicConfig
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

class AnthropicClient(BaseLLMClient[AnthropicConfig]):
    """Anthropic客户端实现"""

    def __init__(self, config: AnthropicConfig) -> None:
        """
        初始化Anthropic客户端

        Args:
            config: Anthropic配置
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
        """转换消息格式以适应Anthropic API"""
        # Anthropic支持系统消息，但需要特殊处理
        converted_messages = []
        system_message = None

        for message in messages:
            if isinstance(message, SystemMessage):
                # 保存系统消息，稍后单独处理
                system_message = message
            else:
                converted_messages.append(message)

        # 如果有系统消息，将其添加到第一条消息之前
        if system_message and converted_messages:
            # Anthropic要求系统消息在第一条消息之前
            # 这里我们将其作为第一条消息的前缀
            first_message = converted_messages[0]
            if isinstance(first_message, HumanMessage):
                # 创建新的HumanMessage而不是直接修改content属性（content是只读属性）
                new_content = (
                    f"{system_message.content}\n\n{first_message.content}"
                )
                converted_messages[0] = HumanMessage(content=new_content)

        return converted_messages

    async def _do_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        http_client = self._http_client
        if http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        try:
            # 转换消息格式
            converted_messages, system_message = self._convert_messages_to_anthropic_format(messages)

            # 准备请求参数
            request_params = self._prepare_request_params(parameters, **kwargs)
            
            # 添加系统消息到请求参数
            if system_message:
                request_params["system"] = system_message

            # 调用HTTP客户端的chat_completions方法
            response = await http_client.chat_completions(
                messages=converted_messages,
                model=self.config.model_name,
                parameters=request_params,
                stream=False
            )

            # 提取Token使用情况
            token_usage = self._extract_token_usage(response)

            # 提取函数调用信息
            function_call = self._extract_function_call(response)

            # 处理content可能是列表的情况
            content = self._extract_content(response)

            # 创建响应对象
            return self._create_response(
                content=content,
                message=response,
                token_usage=token_usage,
                finish_reason=self._extract_finish_reason(response),
                function_call=function_call,
            )

        except Exception as e:
            # 处理Anthropic特定错误
            raise self._handle_anthropic_error(e)
    
    def _convert_messages_to_anthropic_format(self, messages: Sequence[IBaseMessage]) -> tuple[List[IBaseMessage], Optional[str]]:
        """转换消息为Anthropic格式，返回IBaseMessage序列
        
        Args:
            messages: 消息列表
            
        Returns:
            tuple[List[IBaseMessage], Optional[str]]: (消息列表, 系统消息)
        """
        anthropic_messages = []
        system_message = None

        for message in messages:
            if isinstance(message, SystemMessage):
                # Anthropic支持系统消息，但作为单独参数
                system_message = str(message.content)
            else:
                anthropic_messages.append(message)

        return anthropic_messages, system_message
    
    def _get_message_role(self, message: IBaseMessage) -> str:
        """获取消息角色"""
        if isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, AIMessage):
            return "assistant"
        else:
            # 根据类型属性判断
            if hasattr(message, 'type'):
                if message.type == "human":
                    return "user"
                elif message.type == "ai":
                    return "assistant"
                elif message.type == "tool":
                    return "tool"
            
            # 默认为用户消息
            return "user"
    
    def _get_message_content(self, message: IBaseMessage) -> Any:
        """获取消息内容"""
        content = getattr(message, 'content', '')
        
        # 如果内容是字符串，直接返回
        if isinstance(content, str):
            return content
        
        # 如果内容是列表，返回原样（Anthropic支持多模态内容）
        if isinstance(content, list):
            return content
        
        # 其他类型转换为字符串
        return str(content)
    
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
            "max_tokens": self.config.max_tokens or 1024,  # Anthropic需要max_tokens
        }
        
        # 从配置中获取Anthropic特定参数
        if self.config.top_p != 1.0:
            params["top_p"] = self.config.top_p
        
        if self.config.stop_sequences:
            params["stop_sequences"] = self.config.stop_sequences
        
        if self.config.thinking_config:
            params["thinking_config"] = self.config.thinking_config
        
        if self.config.response_format:
            params["response_format"] = self.config.response_format
        
        if self.config.metadata:
            params["metadata"] = self.config.metadata
        
        if self.config.user:
            params["user"] = self.config.user
        
        # 工具调用参数
        if self.config.tools:
            params["tools"] = self.config.tools
            if self.config.tool_choice:
                params["tool_choice"] = self.config.tool_choice
        
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
            token_usage = parser.parse_response(response_dict, "anthropic")
            
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

    def _extract_content(self, response: Any) -> str:
        """提取响应内容
        
        Args:
            response: LLM响应对象
            
        Returns:
            str: 响应内容字符串
        """
        if hasattr(response, "content"):
            content = response.content
            # 如果content是列表，提取第一个元素的文本
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, "text"):
                    return first_item.text
                elif isinstance(first_item, dict) and "text" in first_item:
                    return first_item["text"]
            # 如果content是字符串，直接返回
            elif isinstance(content, str):
                return content
        
        # 如果没有content属性，尝试其他可能的属性
        if hasattr(response, "text"):
            return response.text
        
        # 如果response本身是字符串
        if isinstance(response, str):
            return response
        
        return ""

    def _extract_finish_reason(self, response: Any) -> Optional[str]:
        """提取完成原因"""
        if hasattr(response, "response_metadata") and response.response_metadata:
            metadata = response.response_metadata
            if isinstance(metadata, dict) and "finish_reason" in metadata:
                finish_reason = metadata.get("finish_reason")
                if isinstance(finish_reason, str):
                    return finish_reason
        return None

    def _handle_anthropic_error(self, error: Exception) -> LLMCallError:
        """处理Anthropic特定错误"""
        error_str = str(error).lower()

        # 尝试从错误中提取更多信息
        response = getattr(error, "response", None)
        if response:
            status_code = getattr(response, "status_code", None)
            if status_code:
                if status_code == 401 or status_code == 403:
                    return self._create_enhanced_error(
                        LLMAuthenticationError,
                        "Anthropic API密钥无效或权限不足",
                        error
                    )
                elif status_code == 429:
                    retry_after = None
                    headers = getattr(response, "headers", {})
                    if "retry-after" in headers:
                        retry_after = int(headers["retry-after"])
                    return self._create_enhanced_error(
                        LLMRateLimitError,
                        "Anthropic API频率限制",
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
                        "Anthropic API请求无效",
                        error
                    )
                elif status_code == 500 or status_code == 502 or status_code == 503:
                    return self._create_enhanced_error(
                        LLMServiceUnavailableError,
                        "Anthropic服务不可用",
                        error
                    )

        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            return self._create_enhanced_error(
                LLMTimeoutError,
                f"请求超时: {str(error)}",
                error,
                timeout=self.config.timeout
            )
        elif "rate limit" in error_str or "too many requests" in error_str:
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
        elif "content filter" in error_str or "content policy" in error_str:
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
                f"Anthropic API错误: {str(error)}",
                error
            )

    def _do_stream_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        http_client = self._http_client
        if http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 转换消息格式
                converted_messages, system_message = self._convert_messages_to_anthropic_format(messages)

                # 准备请求参数
                request_params = self._prepare_request_params(parameters, **kwargs)
                
                # 添加系统消息到请求参数
                if system_message:
                    request_params["system"] = system_message

                # 异步流式生成 - 使用chat_completions方法的stream参数
                response = await http_client.chat_completions(
                    messages=converted_messages,
                    model=self.config.model_name,
                    parameters=request_params,
                    stream=True
                )
                
                # 如果response是异步生成器，则迭代它
                if hasattr(response, "__aiter__"):
                    async for chunk in response:  # type: ignore
                        # 处理不同的chunk格式
                        if isinstance(chunk, str):
                            if chunk:
                                yield chunk
                        elif isinstance(chunk, dict):
                            if chunk.get("type") == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                        elif hasattr(chunk, "content"):
                            # 处理对象形式的响应
                            content = chunk.content
                            if isinstance(content, str):
                                if content:
                                    yield content

            except Exception as e:
                # 处理Anthropic特定错误
                raise self._handle_anthropic_error(e)

        return _async_generator()