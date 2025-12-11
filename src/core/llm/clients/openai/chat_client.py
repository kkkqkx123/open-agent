"""基于基础设施层的 Chat Completions 客户端"""

from typing import List, Dict, Any, Generator, AsyncGenerator, Sequence, Optional

from src.interfaces.messages import IBaseMessage
from src.interfaces.llm.http_client import ILLMHttpClient

from src.interfaces.llm import LLMResponse
from ..base import BaseLLMClient


class ChatClient(BaseLLMClient):
    """基于基础设施层的 Chat Completions 客户端"""
    
    def __init__(self, config: Any) -> None:
        """
        初始化 Chat 客户端
        
        Args:
            config: OpenAI 配置
        """
        super().__init__(config)
        self._http_client: Optional[ILLMHttpClient] = None
        # 延迟导入基础设施层组件，避免循环依赖
        self._response_converter: Optional[Any] = None
        self._message_converter: Optional[Any] = None
        self._token_parser: Optional[Any] = None
        self._error_handler: Optional[Any] = None
    
    def _get_infrastructure_components(self) -> tuple[Any, Any, Any, Any]:
        """获取基础设施层组件（延迟初始化）"""
        if self._response_converter is None:
            from src.infrastructure.llm.converters.message import MessageConverter
            from src.infrastructure.llm.token_calculators.token_response_parser import get_token_response_parser
            
            self._response_converter = MessageConverter()
            self._message_converter = MessageConverter()
            self._token_parser = get_token_response_parser()
            self._error_handler = self._create_error_handler()
        
        # 确保所有组件都已初始化，返回类型
        assert self._response_converter is not None
        assert self._message_converter is not None
        assert self._token_parser is not None
        assert self._error_handler is not None
        return (self._response_converter, self._message_converter,
                self._token_parser, self._error_handler)
    
    def _create_error_handler(self) -> Any:
        """创建错误处理器"""
        # 简单的错误处理器实现
        class SimpleErrorHandler:
            def handle_api_error(self, error_response: Dict[str, Any], provider: str) -> str:
                """处理API错误"""
                error_info = error_response.get("error", {})
                message = error_info.get("message", "未知错误")
                return f"API错误 ({provider}): {message}"
            
            def handle_network_error(self, error: Exception, provider: str) -> str:
                """处理网络错误"""
                return f"网络错误 ({provider}): {str(error)}"
        
        return SimpleErrorHandler()
    
    def set_http_client(self, http_client: ILLMHttpClient) -> None:
        """设置HTTP客户端
        
        Args:
            http_client: HTTP客户端实例
        """
        self._http_client = http_client
    
    async def _do_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        merged_params = parameters.copy()
        merged_params.update(kwargs)
        return await self.generate_async(messages, **merged_params)
    
    def _do_stream_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        return self.stream_generate(messages, parameters, **kwargs)
    
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
        
        # 获取基础设施层组件
        response_converter, message_converter, token_parser, error_handler = self._get_infrastructure_components()
        
        try:
            # 使用基础设施层的消息转换器
            openai_messages = []
            for message in messages:
                openai_msg = message_converter.from_base_message(message, "openai")
                openai_messages.append(openai_msg)
            
            # 准备请求参数
            request_params = self._prepare_request_params(**kwargs)
            
            # 调用基础设施层HTTP客户端
            response = await self._http_client.chat_completion(
                messages=openai_messages,
                **request_params
            )
            
            # 使用基础设施层的响应转换器
            base_message = response_converter.to_base_message(response, "openai")
            
            # 创建LLMResponse
            from src.infrastructure.llm.models import TokenUsage
            token_usage = token_parser.parse_response(response, "openai") or TokenUsage()
            
            # 确保内容是字符串类型
            content = base_message.content if hasattr(base_message, 'content') else str(base_message)
            if isinstance(content, list):
                # 如果是列表，提取文本内容
                content = " ".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                    if isinstance(item, (dict, str))
                )
            elif not isinstance(content, str):
                content = str(content)
            
            return LLMResponse(
                content=content,
                model=response.get("model", "unknown"),
                finish_reason=self._extract_finish_reason(response),
                tokens_used=token_usage.total_tokens,
                metadata={
                    "response_id": response.get("id"),
                    "object": response.get("object"),
                    "created": response.get("created"),
                }
            )
            
        except Exception as e:
            # 使用基础设施层的错误处理器
            raise self._handle_error_with_infrastructure(e)
    
    def _extract_finish_reason(self, response: Dict[str, Any]) -> Optional[str]:
        """提取完成原因"""
        choices = response.get("choices", [])
        if choices:
            finish_reason = choices[0].get("finish_reason")
            if isinstance(finish_reason, str):
                return finish_reason
        return None
    
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
        chat_params: Dict[str, Any] = getattr(self.config, 'get_chat_completion_params', lambda: {})()
        params.update(chat_params)
        
        # 添加传入的参数
        params.update(kwargs)
        
        return params
    
    async def stream_generate(  # type: ignore[override]
        self, messages: Sequence[IBaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        流式生成（异步）
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
        """
        if self._http_client is None:
            raise RuntimeError("HTTP客户端未设置")
        
        # 获取基础设施层组件
        response_converter, message_converter, token_parser, error_handler = self._get_infrastructure_components()
        
        try:
            # 使用基础设施层的消息转换器
            openai_messages = []
            for message in messages:
                openai_msg = message_converter.from_base_message(message, "openai")
                openai_messages.append(openai_msg)
            
            # 准备请求参数
            merged_params = parameters or {}
            request_params = self._prepare_request_params(**merged_params)
            request_params.update(kwargs)
            request_params["stream"] = True
            
            # 调用基础设施层HTTP客户端流式接口
            generator_coro = self._http_client.stream_chat_completion(
                messages=openai_messages,
                **request_params
            )
            generator = await generator_coro
            async for chunk in generator:
                if chunk.get("choices"):
                    delta = chunk["choices"][0].get("delta", {})
                    if delta.get("content"):
                        yield delta["content"]
                        
        except Exception as e:
            # 使用基础设施层的错误处理器
            raise self._handle_error_with_infrastructure(e)
    
    async def stream_generate_async(  # type: ignore[override]
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
         
         # 获取基础设施层组件
         response_converter, message_converter, token_parser, error_handler = self._get_infrastructure_components()
         
         try:
             # 使用基础设施层的消息转换器
             openai_messages = []
             for message in messages:
                 openai_msg = message_converter.from_base_message(message, "openai")
                 openai_messages.append(openai_msg)
             
             # 准备请求参数
             request_params = self._prepare_request_params(**kwargs)
             request_params["stream"] = True
             
             # 调用基础设施层HTTP客户端异步流式接口
             generator_coro = self._http_client.async_stream_chat_completion(
                 messages=openai_messages,
                 **request_params
             )
             generator = await generator_coro
             async for chunk in generator:
                 if chunk.get("choices"):
                     delta = chunk["choices"][0].get("delta", {})
                     if delta.get("content"):
                         yield delta["content"]
                         
         except Exception as e:
             # 使用基础设施层的错误处理器
             raise self._handle_error_with_infrastructure(e)
    
    
    def supports_function_calling(self) -> bool:
        """
        检查是否支持函数调用
        
        Returns:
            bool: 是否支持函数调用
        """
        # 从配置中读取是否支持函数调用
        return getattr(self.config, 'function_calling_supported', True)
    
    def _handle_error_with_infrastructure(self, error: Exception) -> Exception:
        """
        使用基础设施层处理错误
        
        Args:
            error: 原始错误
            
        Returns:
            Exception: 处理后的错误
        """
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
        
        # 确保基础设施层组件已初始化
        response_converter, message_converter, token_parser, error_handler = self._get_infrastructure_components()
        
        # 使用基础设施层的错误处理器获取友好的错误消息
        try:
            # 尝试从错误中提取 HTTP 响应信息
            response = getattr(error, "response", None)
            if response is not None:
                # 如果有 HTTP 响应，使用基础设施层的错误处理器
                error_response = {
                    "error": {
                        "type": self._get_error_type_from_status_code(response.status_code),
                        "message": str(error)
                    }
                }
                friendly_message = error_handler.handle_api_error(error_response, "openai")
            else:
                # 网络错误或其他错误
                friendly_message = error_handler.handle_network_error(error, "openai")
        except Exception:
            # 如果错误处理器失败，使用原始错误消息
            friendly_message = str(error)
        
        # 根据错误类型创建相应的异常
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
                        auth_error = LLMAuthenticationError(friendly_message)
                        auth_error.original_error = error
                        return auth_error
                    elif status_code == 429:
                        retry_after = None
                        headers = getattr(response, "headers", None)
                        if headers and "retry-after" in headers:
                            retry_after = int(headers["retry-after"])
                        rate_error = LLMRateLimitError(
                            friendly_message, retry_after=retry_after
                        )
                        rate_error.original_error = error
                        return rate_error
                    elif status_code == 404:
                        model_error = LLMModelNotFoundError(self.config.model_name)
                        model_error.original_error = error
                        return model_error
                    elif status_code == 400:
                        request_error = LLMInvalidRequestError(friendly_message)
                        request_error.original_error = error
                        return request_error
                    elif status_code in [500, 502, 503]:
                        service_error = LLMServiceUnavailableError(friendly_message)
                        service_error.original_error = error
                        return service_error
        except (AttributeError, ValueError, TypeError):
            # 如果访问属性时出错，忽略并继续执行其他错误检查
            pass
        
        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            timeout_error = LLMTimeoutError(friendly_message, timeout=self.config.timeout)
            timeout_error.original_error = error
            return timeout_error
        elif "rate limit" in error_str or "too many requests" in error_str:
            rate_error = LLMRateLimitError(friendly_message)
            rate_error.original_error = error
            return rate_error
        elif (
            "authentication" in error_str
            or "unauthorized" in error_str
            or "invalid api key" in error_str
        ):
            auth_error = LLMAuthenticationError(friendly_message)
            auth_error.original_error = error
            return auth_error
        elif "model not found" in error_str or "not found" in error_str:
            model_error = LLMModelNotFoundError(self.config.model_name)
            model_error.original_error = error
            return model_error
        elif "token" in error_str and "limit" in error_str:
            token_error = LLMTokenLimitError(friendly_message)
            token_error.original_error = error
            return token_error
        elif "content filter" in error_str or "content policy" in error_str:
            content_error = LLMContentFilterError(friendly_message)
            content_error.original_error = error
            return content_error
        elif "service unavailable" in error_str or "503" in error_str:
            service_error = LLMServiceUnavailableError(friendly_message)
            service_error.original_error = error
            return service_error
        elif "invalid request" in error_str or "bad request" in error_str:
            request_error = LLMInvalidRequestError(friendly_message)
            request_error.original_error = error
            return request_error
        else:
            call_error = LLMCallError(friendly_message)
            call_error.original_error = error
            return call_error
    
    def _get_error_type_from_status_code(self, status_code: int) -> str:
        """根据 HTTP 状态码获取错误类型"""
        status_code_to_error_type = {
            400: "invalid_request_error",
            401: "authentication_error",
            403: "permission_error",
            404: "not_found_error",
            429: "rate_limit_error",
            500: "api_error",
            502: "api_error",
            503: "overloaded_error",
            504: "timeout_error"
        }
        return status_code_to_error_type.get(status_code, "unknown_error")
