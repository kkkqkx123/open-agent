"""轻量级 Responses API 客户端"""

import httpx
import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Generator, Sequence

from langchain_core.messages import BaseMessage

from .interfaces import ResponsesAPIClient
from .utils import ResponseConverter, MessageConverter
from src.interfaces.llm import LLMResponse


class ResponsesClient(ResponsesAPIClient):
    """轻量级 Responses API 客户端"""
    
    def __init__(self, config: Any) -> None:
        """
        初始化 Responses API 客户端
        
        Args:
            config: OpenAI 配置
        """
        super().__init__(config)
        self._converter = ResponseConverter()
        self._message_converter = MessageConverter()
        self._conversation_history: List[Dict[str, Any]] = []
        
        # 设置基础 URL
        self.base_url = (
            config.base_url.rstrip("/")
            if config.base_url
            else "https://api.openai.com/v1"
        )
        
        # 设置 HTTP 标头
        self.headers = config.get_resolved_headers()
    
    async def generate_async(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> LLMResponse:
        """
        异步生成响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        # 转换消息为 input 格式
        input_text = self._messages_to_input(messages)
        
        # 获取之前的响应 ID（如果有）
        previous_response_id = self._get_previous_response_id()
        
        # 构建请求载荷
        payload = self._build_payload(input_text, previous_response_id, **kwargs)
        
        try:
            # 发送异步请求
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/responses",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                api_response = response.json()
            
            # 转换响应格式
            llm_response = self._converter.convert_responses_response(api_response)
            
            # 更新对话历史
            self._update_conversation_history(api_response)
            
            return llm_response
            
        except Exception as e:
            # 错误处理
            raise self._handle_error(e)
    
    def stream_generate(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        同步流式生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
        """
        # 转换消息为 input 格式
        input_text = self._messages_to_input(messages)
        
        # 获取之前的响应 ID（如果有）
        previous_response_id = self._get_previous_response_id()
        
        # 构建请求载荷
        payload = self._build_payload(input_text, previous_response_id, stream=True, **kwargs)
        
        try:
            # 发送流式请求
            with httpx.Client(timeout=self.config.timeout) as client:
                with client.stream(
                    "POST",
                    f"{self.base_url}/responses",
                    headers=self.headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # 移除 "data: " 前缀
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                # 提取文本内容
                                content = self._extract_stream_content(chunk)
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            # 错误处理
            raise self._handle_error(e)
    
    async def stream_generate_async(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应块
        """
        # 转换消息为 input 格式
        input_text = self._messages_to_input(messages)
        
        # 获取之前的响应 ID（如果有）
        previous_response_id = self._get_previous_response_id()
        
        # 构建请求载荷
        payload = self._build_payload(input_text, previous_response_id, stream=True, **kwargs)
        
        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 发送异步流式请求
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/responses",
                        headers=self.headers,
                        json=payload
                    ) as response:
                        response.raise_for_status()
                        
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 "data: " 前缀
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data)
                                    # 提取文本内容
                                    content = self._extract_stream_content(chunk)
                                    if content:
                                        yield content
                                except json.JSONDecodeError:
                                    continue
                                    
            except Exception as e:
                # 错误处理
                raise self._handle_error(e)
        
        return _async_generator()
    
    
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
    
    def _messages_to_input(self, messages: Sequence[BaseMessage]) -> str:
        """
        将消息列表转换为 input 字符串
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 转换后的 input 字符串
        """
        return self._message_converter.messages_to_input(messages)
    
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
    
    def _extract_stream_content(self, chunk: Dict[str, Any]) -> str:
        """
        从流式响应块中提取文本内容
        
        Args:
            chunk: 流式响应块
            
        Returns:
            str: 提取的文本内容
        """
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
