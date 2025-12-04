"""基于基础设施层的 Chat Completions 客户端"""

from typing import List, Dict, Any, Generator, AsyncGenerator, Sequence

from src.interfaces.messages import IBaseMessage
from src.interfaces.llm.http_client import ILLMHttpClient

from .interfaces import ChatCompletionClient
from .utils import ResponseConverter
from src.interfaces.llm import LLMResponse


class ChatClient(ChatCompletionClient):
    """基于基础设施层的 Chat Completions 客户端"""
    
    def __init__(self, config: Any) -> None:
        """
        初始化 Chat 客户端
        
        Args:
            config: OpenAI 配置
        """
        super().__init__(config)
        self._http_client: Optional[ILLMHttpClient] = None
        self._converter = ResponseConverter()
    
    def set_http_client(self, http_client: ILLMHttpClient) -> None:
        """设置HTTP客户端
        
        Args:
            http_client: HTTP客户端实例
        """
        self._http_client = http_client
    
    async def generate_async(
        self, messages: Sequence[IBaseMessage], **kwargs: Any
    ) -> LLMResponse:
        """
        异步生成响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        if self._http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        try:
            # 转换消息格式
            openai_messages = self._convert_messages_to_openai_format(messages)
            
            # 准备请求参数
            request_params = self._prepare_request_params(**kwargs)
            
            # 调用基础设施层HTTP客户端
            response = await self._http_client.chat_completion(
                messages=openai_messages,
                **request_params
            )
            
            # 转换响应格式
            return self._converter.convert_openai_response(response)
            
        except Exception as e:
            # 错误处理
            raise self._handle_error(e)
    
    def _convert_messages_to_openai_format(self, messages: Sequence[IBaseMessage]) -> List[Dict[str, Any]]:
        """转换消息为OpenAI格式
        
        Args:
            messages: 消息列表
            
        Returns:
            List[Dict[str, Any]]: OpenAI格式的消息列表
        """
        openai_messages = []
        
        for message in messages:
            openai_message = {
                "role": self._get_message_role(message),
                "content": self._get_message_content(message)
            }
            
            # 添加名称（如果有）
            if hasattr(message, 'name') and message.name:
                openai_message["name"] = message.name
            
            openai_messages.append(openai_message)
        
        return openai_messages
    
    def _get_message_role(self, message: IBaseMessage) -> str:
        """获取消息角色"""
        if hasattr(message, 'type'):
            if message.type == "system":
                return "system"
            elif message.type == "human":
                return "user"
            elif message.type == "ai":
                return "assistant"
            elif message.type == "tool":
                return "tool"
        
        # 根据类名判断
        message_class = message.__class__.__name__.lower()
        if "system" in message_class:
            return "system"
        elif "human" in message_class or "user" in message_class:
            return "user"
        elif "ai" in message_class or "assistant" in message_class:
            return "assistant"
        elif "tool" in message_class:
            return "tool"
        
        # 默认为用户消息
        return "user"
    
    def _get_message_content(self, message: IBaseMessage) -> Any:
        """获取消息内容"""
        content = getattr(message, 'content', '')
        
        # 如果内容是字符串，直接返回
        if isinstance(content, str):
            return content
        
        # 如果内容是列表，返回原样（OpenAI支持多模态内容）
        if isinstance(content, list):
            return content
        
        # 其他类型转换为字符串
        return str(content)
    
    def _prepare_request_params(self, **kwargs: Any) -> Dict[str, Any]:
        """准备请求参数
        
        Args:
            **kwargs: 额外参数
            
        Returns:
            Dict[str, Any]: 请求参数
        """
        # 基础参数
        params = {
            "model": self.config.model_name,
            "temperature": self.config.temperature,
        }
        
        # 可选参数
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
        
        if self.config.top_p != 1.0:
            params["top_p"] = self.config.top_p
        
        # 从配置中获取其他参数
        chat_params = getattr(self.config, 'get_chat_completion_params', lambda: {})()
        params.update(chat_params)
        
        # 添加传入的参数
        params.update(kwargs)
        
        return params
    
    def stream_generate(
        self, messages: Sequence[IBaseMessage], **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        同步流式生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
        """
        if self._http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        try:
            # 转换消息格式
            openai_messages = self._convert_messages_to_openai_format(messages)
            
            # 准备请求参数
            request_params = self._prepare_request_params(**kwargs)
            request_params["stream"] = True
            
            # 调用基础设施层HTTP客户端流式接口
            for chunk in self._http_client.stream_chat_completion(
                messages=openai_messages,
                **request_params
            ):
                if chunk.get("choices"):
                    delta = chunk["choices"][0].get("delta", {})
                    if delta.get("content"):
                        yield delta["content"]
                        
        except Exception as e:
            # 错误处理
            raise self._handle_error(e)
    
    async def stream_generate_async(
        self, messages: Sequence[IBaseMessage], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
        """
        if self._http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        try:
            # 转换消息格式
            openai_messages = self._convert_messages_to_openai_format(messages)
            
            # 准备请求参数
            request_params = self._prepare_request_params(**kwargs)
            request_params["stream"] = True
            
            # 调用基础设施层HTTP客户端异步流式接口
            async for chunk in self._http_client.async_stream_chat_completion(
                messages=openai_messages,
                **request_params
            ):
                if chunk.get("choices"):
                    delta = chunk["choices"][0].get("delta", {})
                    if delta.get("content"):
                        yield delta["content"]
                        
        except Exception as e:
            # 错误处理
            raise self._handle_error(e)
    
    
    def supports_function_calling(self) -> bool:
        """
        检查是否支持函数调用
        
        Returns:
            bool: 是否支持函数调用
        """
        # 从配置中读取是否支持函数调用
        return getattr(self.config, 'function_calling_supported', True)
    
    def _handle_error(self, error: Exception) -> Exception:
        """
        处理错误
        
        Args:
            error: 原始错误
            
        Returns:
            Exception: 处理后的错误
        """
        from ....common.exceptions.llm import (
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
        
        error_str = str(error).lower()
        
        # 尝试从错误中提取更多信息
        try:
            # 检查是否有 response 属性
            response = getattr(error, "response", None)
            if response is not None:
                # 检查是否有 status_code 属性
                status_code = getattr(response, "status_code", None)
                if status_code is not None:
                    if status_code == 401:
                        auth_error = LLMAuthenticationError("OpenAI API 密钥无效")
                        auth_error.original_error = error
                        return auth_error
                    elif status_code == 429:
                        retry_after = None
                        headers = getattr(response, "headers", None)
                        if headers and "retry-after" in headers:
                            retry_after = int(headers["retry-after"])
                        rate_error = LLMRateLimitError(
                            "OpenAI API 频率限制", retry_after=retry_after
                        )
                        rate_error.original_error = error
                        return rate_error
                    elif status_code == 404:
                        model_error = LLMModelNotFoundError(self.config.model_name)
                        model_error.original_error = error
                        return model_error
                    elif status_code == 400:
                        request_error = LLMInvalidRequestError("OpenAI API 请求无效")
                        request_error.original_error = error
                        return request_error
                    elif status_code in [500, 502, 503]:
                        service_error = LLMServiceUnavailableError("OpenAI 服务不可用")
                        service_error.original_error = error
                        return service_error
        except (AttributeError, ValueError, TypeError):
            # 如果访问属性时出错，忽略并继续执行其他错误检查
            pass
        
        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            timeout_error = LLMTimeoutError(str(error), timeout=self.config.timeout)
            timeout_error.original_error = error
            return timeout_error
        elif "rate limit" in error_str or "too many requests" in error_str:
            rate_error = LLMRateLimitError(str(error))
            rate_error.original_error = error
            return rate_error
        elif (
            "authentication" in error_str
            or "unauthorized" in error_str
            or "invalid api key" in error_str
        ):
            auth_error = LLMAuthenticationError(str(error))
            auth_error.original_error = error
            return auth_error
        elif "model not found" in error_str or "not found" in error_str:
            model_error = LLMModelNotFoundError(self.config.model_name)
            model_error.original_error = error
            return model_error
        elif "token" in error_str and "limit" in error_str:
            token_error = LLMTokenLimitError(str(error))
            token_error.original_error = error
            return token_error
        elif "content filter" in error_str or "content policy" in error_str:
            content_error = LLMContentFilterError(str(error))
            content_error.original_error = error
            return content_error
        elif "service unavailable" in error_str or "503" in error_str:
            service_error = LLMServiceUnavailableError(str(error))
            service_error.original_error = error
            return service_error
        elif "invalid request" in error_str or "bad request" in error_str:
            request_error = LLMInvalidRequestError(str(error))
            request_error.original_error = error
            return request_error
        else:
            call_error = LLMCallError(str(error))
            call_error.original_error = error
            return call_error
