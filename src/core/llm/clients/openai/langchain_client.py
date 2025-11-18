"""基于 LangChain 的 Chat Completions 客户端"""

from typing import List, Dict, Any, Generator, AsyncGenerator, Sequence

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from .interfaces import ChatCompletionClient
from .utils import ResponseConverter
from ...models import LLMResponse


class LangChainChatClient(ChatCompletionClient):
    """基于 LangChain 的 Chat Completions 客户端"""
    
    def __init__(self, config) -> None:
        """
        初始化 LangChain Chat 客户端
        
        Args:
            config: OpenAI 配置
        """
        super().__init__(config)
        self._client: ChatOpenAI = self._create_client()
        self._converter = ResponseConverter()
    
    def _create_client(self) -> ChatOpenAI:
        """创建 LangChain ChatOpenAI 客户端"""
        # 获取 Chat Completions 特定参数
        chat_params = self.config.get_chat_completion_params()
        
        # 转换 api_key 为 SecretStr 类型
        api_key = SecretStr(self.config.api_key) if self.config.api_key else None
        
        # 构建超时配置
        timeout_config = getattr(self.config, 'timeout_config', None)
        if timeout_config and hasattr(timeout_config, 'get_client_timeout_kwargs'):
            # 使用新的超时配置
            timeout_kwargs = timeout_config.get_client_timeout_kwargs()
            timeout_value = timeout_kwargs.get('request_timeout', self.config.timeout)
        else:
            # 使用旧的超时配置
            timeout_value = self.config.timeout
        
        # 创建 ChatOpenAI 客户端
        # 提取ChatOpenAI直接支持的参数
        direct_params = {}
        
        # 基础参数
        if 'top_p' in chat_params:
            direct_params['top_p'] = chat_params['top_p']
        if 'frequency_penalty' in chat_params:
            direct_params['frequency_penalty'] = chat_params['frequency_penalty']
        if 'presence_penalty' in chat_params:
            direct_params['presence_penalty'] = chat_params['presence_penalty']
        if 'stop' in chat_params:
            direct_params['stop'] = chat_params['stop']
        
        # 高级参数
        if 'top_logprobs' in chat_params:
            direct_params['top_logprobs'] = chat_params['top_logprobs']
        if 'service_tier' in chat_params:
            direct_params['service_tier'] = chat_params['service_tier']
        if 'safety_identifier' in chat_params:
            direct_params['safety_identifier'] = chat_params['safety_identifier']
        if 'seed' in chat_params:
            direct_params['seed'] = chat_params['seed']
        if 'user' in chat_params:
            direct_params['user'] = chat_params['user']
        
        # 工具调用参数
        if 'tool_choice' in chat_params:
            direct_params['tool_choice'] = chat_params['tool_choice']
        if 'tools' in chat_params:
            direct_params['tools'] = chat_params['tools']
        
        # 响应格式参数
        if 'response_format' in chat_params:
            direct_params['response_format'] = chat_params['response_format']
        
        # 流式选项
        if 'stream_options' in chat_params:
            direct_params['stream_options'] = chat_params['stream_options']
        
        # 其他特殊参数放入model_kwargs
        model_kwargs = {k: v for k, v in chat_params.items() 
                       if k not in ['temperature', 'model', 'api_key', 'base_url', 'timeout', 'max_retries',
                                   'top_p', 'frequency_penalty', 'presence_penalty', 'stop',
                                   'top_logprobs', 'service_tier', 'safety_identifier', 'seed', 'user',
                                   'tool_choice', 'tools', 'response_format', 'stream_options']}
        
        return ChatOpenAI(
            model=self.config.model_name,
            api_key=api_key,
            base_url=self.config.base_url,
            temperature=self.config.temperature,
            timeout=timeout_value,
            max_retries=self.config.max_retries,
            **direct_params,
            model_kwargs=model_kwargs,
        )
    
    def generate(self, messages: Sequence[BaseMessage], **kwargs: Any) -> LLMResponse:
        """
        同步生成响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        try:
            # 调用 LangChain ChatOpenAI
            response = self._client.invoke(list(messages), **kwargs)
            
            # 转换响应格式
            return self._converter.convert_langchain_response(response)
            
        except Exception as e:
            # 错误处理
            raise self._handle_error(e)
    
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
        try:
            # 调用 LangChain ChatOpenAI 异步方法
            response = await self._client.ainvoke(list(messages), **kwargs)
            
            # 转换响应格式
            return self._converter.convert_langchain_response(response)
            
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
        try:
            # 流式生成
            stream = self._client.stream(list(messages), **kwargs)
            
            # 收集完整响应
            for chunk in stream:
                if chunk.content:
                    # 提取内容
                    content = self._converter._extract_content(chunk)
                    if content:
                        yield content
                        
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
        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 异步流式生成
                stream = self._client.astream(list(messages), **kwargs)
                
                # 收集完整响应
                async for chunk in stream:
                    if chunk.content:
                        # 提取内容
                        content = self._converter._extract_content(chunk)
                        if content:
                            yield content
                            
            except Exception as e:
                # 错误处理
                raise self._handle_error(e)
        
        return _async_generator()
    
    
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
        from ...exceptions import (
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
                        llm_error = LLMAuthenticationError("OpenAI API 密钥无效")
                        llm_error.original_error = error
                        return llm_error
                    elif status_code == 429:
                        retry_after = None
                        headers = getattr(response, "headers", None)
                        if headers and "retry-after" in headers:
                            retry_after = int(headers["retry-after"])
                        llm_error = LLMRateLimitError(
                            "OpenAI API 频率限制", retry_after=retry_after
                        )
                        llm_error.original_error = error
                        return llm_error
                    elif status_code == 404:
                        llm_error = LLMModelNotFoundError(self.config.model_name)
                        llm_error.original_error = error
                        return llm_error
                    elif status_code == 400:
                        llm_error = LLMInvalidRequestError("OpenAI API 请求无效")
                        llm_error.original_error = error
                        return llm_error
                    elif status_code in [500, 502, 503]:
                        llm_error = LLMServiceUnavailableError("OpenAI 服务不可用")
                        llm_error.original_error = error
                        return llm_error
        except (AttributeError, ValueError, TypeError):
            # 如果访问属性时出错，忽略并继续执行其他错误检查
            pass
        
        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            llm_error = LLMTimeoutError(str(error), timeout=self.config.timeout)
            llm_error.original_error = error
            return llm_error
        elif "rate limit" in error_str or "too many requests" in error_str:
            llm_error = LLMRateLimitError(str(error))
            llm_error.original_error = error
            return llm_error
        elif (
            "authentication" in error_str
            or "unauthorized" in error_str
            or "invalid api key" in error_str
        ):
            llm_error = LLMAuthenticationError(str(error))
            llm_error.original_error = error
            return llm_error
        elif "model not found" in error_str or "not found" in error_str:
            llm_error = LLMModelNotFoundError(self.config.model_name)
            llm_error.original_error = error
            return llm_error
        elif "token" in error_str and "limit" in error_str:
            llm_error = LLMTokenLimitError(str(error))
            llm_error.original_error = error
            return llm_error
        elif "content filter" in error_str or "content policy" in error_str:
            llm_error = LLMContentFilterError(str(error))
            llm_error.original_error = error
            return llm_error
        elif "service unavailable" in error_str or "503" in error_str:
            llm_error = LLMServiceUnavailableError(str(error))
            llm_error.original_error = error
            return llm_error
        elif "invalid request" in error_str or "bad request" in error_str:
            llm_error = LLMInvalidRequestError(str(error))
            llm_error.original_error = error
            return llm_error
        else:
            llm_error = LLMCallError(str(error))
            llm_error.original_error = error
            return llm_error