"""轻量级 Responses API 客户端"""

import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Generator, Sequence

from src.interfaces.messages import IBaseMessage

from src.interfaces.llm import LLMResponse
from src.infrastructure.llm.http_client.openai_http_client import OpenAIHttpClient
from ..base import BaseLLMClient


class ResponsesClient(BaseLLMClient):
    """轻量级 Responses API 客户端"""
    
    def __init__(self, config: Any) -> None:
        """
        初始化 Responses API 客户端
        
        Args:
            config: OpenAI 配置
        """
        super().__init__(config)
        self._conversation_history: List[Dict[str, Any]] = []
        
        # 延迟导入基础设施层组件，避免循环依赖
        self._http_client: Optional[Any] = None
        self._message_converter: Optional[Any] = None
        self._stream_utils: Optional[Any] = None
        self._error_handler: Optional[Any] = None
        self._token_parser: Optional[Any] = None
        self._response_converter: Optional[Any] = None
        
        # 初始化基础设施层HTTP客户端
        self._http_client = OpenAIHttpClient(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            api_format="responses"
        )
    
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
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        return getattr(self.config, 'function_calling_supported', False)
    
    def _get_infrastructure_components(self) -> tuple[Any, Any, Any, Any, Any]:
        """获取基础设施层组件（延迟初始化）"""
        if self._message_converter is None:
            from src.infrastructure.llm.converters.message import MessageConverter
            from src.infrastructure.llm.token_calculators.token_response_parser import get_token_response_parser
            
            self._message_converter = MessageConverter()
            self._stream_utils = self._create_stream_utils()
            self._error_handler = self._create_error_handler()
            self._token_parser = get_token_response_parser()
            self._response_converter = MessageConverter()
        
        # 确保所有组件都已初始化
        assert self._message_converter is not None
        assert self._stream_utils is not None
        assert self._error_handler is not None
        assert self._token_parser is not None
        assert self._response_converter is not None
        return (self._message_converter, self._stream_utils, self._error_handler,
                self._token_parser, self._response_converter)
    
    def _create_stream_utils(self) -> Any:
        """创建流式工具"""
        # 简单的流式工具实现
        class SimpleStreamUtils:
            def parse_stream_event(self, chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                """解析流式事件"""
                if isinstance(chunk, dict):
                    return chunk
                return None
        
        return SimpleStreamUtils()
    
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
        # 获取基础设施层组件
        message_converter, stream_utils, error_handler, token_parser, response_converter = self._get_infrastructure_components()
        
        # 转换消息为 input 格式
        input_text = self._messages_to_input(messages)
        
        # 获取之前的响应 ID（如果有）
        previous_response_id = self._get_previous_response_id()
        
        # 构建请求载荷
        payload = self._build_payload(input_text, previous_response_id, **kwargs)
        
        try:
            # 使用基础设施层的 HTTP 客户端发送请求
            assert self._http_client is not None
            response = await self._http_client.post("responses", payload)
            api_response = response.json()
            
            # 转换响应格式
            llm_response = self._convert_responses_response(api_response)
            
            # 更新对话历史
            self._update_conversation_history(api_response)
            
            return llm_response
            
        except Exception as e:
            # 使用基础设施层的错误处理器
            raise self._handle_error_with_infrastructure(e)
    
    async def stream_generate(  # type: ignore[override]
        self, messages: Sequence[IBaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        流式生成文本响应（异步）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
        """
        async for chunk in self.stream_generate_async(messages, **kwargs):
            yield chunk
    
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
        # 获取基础设施层组件
        message_converter, stream_utils, error_handler, token_parser, response_converter = self._get_infrastructure_components()
        
        # 转换消息为 input 格式
        input_text = self._messages_to_input(messages)
        
        # 获取之前的响应 ID（如果有）
        previous_response_id = self._get_previous_response_id()
        
        # 构建请求载荷
        payload = self._build_payload(input_text, previous_response_id, stream=True, **kwargs)
        
        try:
            # 使用基础设施层的 HTTP 客户端发送异步流式请求
            assert self._http_client is not None
            async for chunk in self._http_client.stream_post("responses", payload):
                # 使用基础设施层的流式工具解析事件
                event = stream_utils.parse_stream_event(chunk)
                if event and event.get("type") == "done":
                    break
                
                # 提取文本内容
                content = self._extract_stream_content(event) if event else ""
                if content:
                    yield content
                                   
        except Exception as e:
            # 使用基础设施层的错误处理器
            raise self._handle_error_with_infrastructure(e)
    
    
    def _get_previous_response_id(self) -> Optional[str]:
        """
        获取之前的响应 ID（用于对话上下文）
        
        Returns:
            Optional[str]: 之前的响应 ID
        """
        if self._conversation_history:
            return self._conversation_history[-1].get("id")
        return None
    
    def _update_conversation_history(self, response: Dict[str, Any]) -> None:
        """
        更新对话历史
        
        Args:
            response: API 响应
        """
        self._conversation_history.append(response)
        
        # 限制历史记录长度
        max_history = 10
        if len(self._conversation_history) > max_history:
            self._conversation_history = self._conversation_history[-max_history:]
    
    def _messages_to_input(self, messages: Sequence[IBaseMessage]) -> str:
        """
        将消息列表转换为 input 字符串
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 转换后的 input 字符串
        """
        # 获取基础设施层组件
        message_converter, stream_utils, error_handler, token_parser, response_converter = self._get_infrastructure_components()
        
        # 使用基础设施层的消息转换器
        input_parts = []
        for message in messages:
            # 转换为OpenAI Responses格式
            openai_responses_msg = message_converter.from_base_message(message, "openai-responses")
            
            # 提取内容
            if isinstance(openai_responses_msg, dict):
                content = openai_responses_msg.get("content", "")
                if isinstance(content, list):
                    # 多模态内容，提取文本
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "input_text":
                                text_parts.append(item.get("text", ""))
                            elif item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            else:
                                text_parts.append(str(item))
                        else:
                            text_parts.append(str(item))
                    content = " ".join(text_parts)
                elif not isinstance(content, str):
                    content = str(content)
                
                # 添加角色前缀
                role = openai_responses_msg.get("role", "user")
                if role == "system":
                    input_parts.append(f"System: {content}")
                elif role == "user":
                    input_parts.append(f"User: {content}")
                elif role == "assistant":
                    input_parts.append(f"Assistant: {content}")
                else:
                    input_parts.append(content)
            else:
                input_parts.append(str(openai_responses_msg))
        
        return "\n".join(input_parts)
    
    def _build_payload(
        self, 
        input_text: str, 
        previous_response_id: Optional[str] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        构建请求载荷
        
        Args:
            input_text: 输入文本
            previous_response_id: 之前的响应 ID
            stream: 是否流式
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 请求载荷
        """
        # 基础载荷
        payload = {
            "model": self.config.model_name,
            "input": input_text,
        }
        
        # 添加之前的响应 ID
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        
        # 添加流式选项
        if stream:
            payload["stream"] = True
        
        # 添加 Responses API 特定参数
        responses_params = self.config.get_responses_params()
        payload.update(responses_params)
        
        # 添加其他参数
        payload.update(kwargs)
        
        return payload
    
    def _convert_responses_response(self, response: Dict[str, Any]) -> LLMResponse:
        """
        转换 Responses API 响应为统一格式
        
        Args:
            response: Responses API 响应
            
        Returns:
            LLMResponse: 统一格式的响应
        """
        # 提取输出内容
        content = self._extract_output_text(response)
        
        # 提取 Token 使用情况
        token_usage = self._extract_responses_token_usage(response)
        
        # 提取函数调用
        function_call = self._extract_responses_function_call(response)
        
        # 提取完成原因
        finish_reason = self._extract_responses_finish_reason(response)
        
        # 创建响应对象 - 使用接口定义的LLMResponse结构
        return LLMResponse(
            content=content,
            model=response.get("model", "unknown"),
            finish_reason=finish_reason,
            tokens_used=token_usage.total_tokens if token_usage else None,
            metadata={
                "response_id": response.get("id"),
                "object": response.get("object"),
                "created_at": response.get("created_at"),
                "output_items": response.get("output", []),
            },
        )
    
    def _extract_output_text(self, response: Dict[str, Any]) -> str:
        """提取 Responses API 输出文本"""
        output_items = response.get("output", [])
        
        for item in output_items:
            if item.get("type") == "message":
                content = item.get("content", [])
                for content_item in content:
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text", "")
                        return str(text) if text is not None else ""
        
        return ""
    
    def _extract_responses_token_usage(self, response: Dict[str, Any]) -> Optional[Any]:
        """提取 Responses API Token 使用情况"""
        # 获取基础设施层组件
        message_converter, stream_utils, error_handler, token_parser, response_converter = self._get_infrastructure_components()
        
        try:
            # 使用基础设施层的 Token 响应解析器
            token_usage = token_parser.parse_response(response, "openai")
            
            if token_usage is None:
                # 回退到基本实现
                return self._extract_responses_token_usage_fallback(response)
            
            return token_usage
            
        except Exception as e:
            # 如果使用基础设施层解析器失败，回退到基本实现
            from src.interfaces.dependency_injection import get_logger
            logger = get_logger(__name__)
            logger.warning(f"使用基础设施层Token解析器失败，回退到基本实现: {e}")
            return self._extract_responses_token_usage_fallback(response)
    
    def _extract_responses_token_usage_fallback(self, response: Dict[str, Any]) -> Any:
        """Token提取的回退实现"""
        from src.infrastructure.llm.models import TokenUsage
        
        usage = response.get("usage", {})

        # 提取基础token信息
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # 创建TokenUsage对象
        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        # 提取详细的token信息（如果可用）
        prompt_details = usage.get("prompt_tokens_details", {})
        completion_details = usage.get("completion_tokens_details", {})
        
        # 添加API响应中的缓存token统计信息（从OpenAI API响应中提取，用于计费统计）
        token_usage.cached_tokens = prompt_details.get("cached_tokens", 0)
        token_usage.cached_prompt_tokens = token_usage.cached_tokens  # OpenAI中缓存token主要是prompt
        
        # 添加音频token信息
        token_usage.prompt_audio_tokens = prompt_details.get("audio_tokens", 0)
        token_usage.completion_audio_tokens = completion_details.get("audio_tokens", 0)
        
        # 添加推理token信息
        token_usage.reasoning_tokens = completion_details.get("reasoning_tokens", 0)
        
        # 添加预测token信息
        token_usage.accepted_prediction_tokens = completion_details.get("accepted_prediction_tokens", 0)
        token_usage.rejected_prediction_tokens = completion_details.get("rejected_prediction_tokens", 0)

        return token_usage
    
    def _extract_responses_function_call(
        self, response: Dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """提取 Responses API 函数调用信息"""
        output_items = response.get("output", [])
        
        for item in output_items:
            if item.get("type") == "function_call":
                return {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "arguments": item.get("arguments"),
                }
        
        return None
    
    def _extract_responses_finish_reason(self, response: Dict[str, Any]) -> Optional[str]:
        """提取 Responses API 完成原因"""
        return response.get("status") or response.get("finish_reason")
    
    def _extract_stream_content(self, chunk: Dict[str, Any]) -> str:
        """
        从流式响应块中提取文本内容
        
        Args:
            chunk: 流式响应块
            
        Returns:
            str: 提取的文本内容
        """
        if not chunk:
            return ""
            
        # 检查是否是完成信号
        if chunk.get("type") == "done":
            return ""
        
        # 提取输出内容
        output_items = chunk.get("output", [])
        for item in output_items:
            if item.get("type") == "message":
                content = item.get("content", [])
                for content_item in content:
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text", "")
                        # 确保返回的是字符串类型
                        return str(text) if text is not None else ""
        
        return ""
    
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
        
        # 获取基础设施层组件
        message_converter, stream_utils, error_handler, token_parser, response_converter = self._get_infrastructure_components()
        
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
