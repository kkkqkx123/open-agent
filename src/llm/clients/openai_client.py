"""OpenAI客户端实现"""

import json
import time
from typing import Dict, Any, Optional, List, AsyncGenerator, Generator
import asyncio

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from .base import BaseLLMClient
from ..models import LLMResponse, TokenUsage
from ..config import OpenAIConfig
from ..exceptions import (
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError
)


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端实现"""
    
    def __init__(self, config: OpenAIConfig) -> None:
        """
        初始化OpenAI客户端
        
        Args:
            config: OpenAI配置
        """
        super().__init__(config)
        
        # 获取解析后的HTTP标头
        resolved_headers = config.get_resolved_headers()
        
        # 创建LangChain ChatOpenAI实例
        # 准备模型参数
        model_kwargs: Dict[str, Any] = {}
        if config.max_tokens is not None:
            model_kwargs["max_tokens"] = config.max_tokens
        if config.functions:
            model_kwargs["functions"] = config.functions
            if config.function_call is not None:
                model_kwargs["function_call"] = config.function_call
        
        # 转换 api_key 为 SecretStr 类型
        api_key = SecretStr(config.api_key) if config.api_key else None
        
        self._client = ChatOpenAI(
            model=config.model_name,
            api_key=api_key,
            base_url=config.base_url,
            organization=config.organization,
            temperature=config.temperature,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            timeout=config.timeout,
            max_retries=config.max_retries,
            default_headers=resolved_headers,
            model_kwargs=model_kwargs
        )
    
    def _do_generate(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> LLMResponse:
        """执行生成操作"""
        try:
            # 调用OpenAI API
            response = self._client.invoke(messages, **parameters)
            
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
                function_call=function_call
            )
            
        except Exception as e:
            # 处理OpenAI特定错误
            raise self._handle_openai_error(e)
    
    async def _do_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        try:
            # 调用OpenAI API
            response = await self._client.ainvoke(messages, **parameters)
            
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
                function_call=function_call
            )
            
        except Exception as e:
            # 处理OpenAI特定错误
            raise self._handle_openai_error(e)
    
    
    
    def get_token_count(self, text: str) -> int:
        """计算文本的token数量"""
        from ..token_counter import TokenCounterFactory
        
        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        return counter.count_tokens(text)
    
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表的token数量"""
        from ..token_counter import TokenCounterFactory
        
        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        return counter.count_messages_tokens(messages)
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        return True
    
    def _extract_token_usage(self, response: Any) -> TokenUsage:
        """提取Token使用情况"""
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            return TokenUsage(
                prompt_tokens=usage.get('input_tokens', 0),
                completion_tokens=usage.get('output_tokens', 0),
                total_tokens=usage.get('total_tokens', 0)
            )
        elif hasattr(response, 'response_metadata') and response.response_metadata:
            metadata = response.response_metadata
            if 'token_usage' in metadata:
                usage = metadata['token_usage']
                return TokenUsage(
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0)
                )
        
        # 默认返回0
        return TokenUsage()
    
    def _extract_function_call(self, response: Any) -> Optional[Dict[str, Any]]:
        """提取函数调用信息"""
        if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
            function_call = response.additional_kwargs['function_call']
            if isinstance(function_call, dict):
                return function_call
        return None
    
    def _extract_finish_reason(self, response: Any) -> Optional[str]:
        """提取完成原因"""
        if hasattr(response, 'response_metadata') and response.response_metadata:
            metadata = response.response_metadata
            finish_reason = metadata.get('finish_reason')
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
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                # 忽略其他类型的元素
            return ''.join(text_parts)
        
        # 其他类型转换为字符串
        return str(content)
    
    def _handle_openai_error(self, error: Exception) -> LLMCallError:
        """处理OpenAI特定错误"""
        error_str = str(error).lower()
        
        # 尝试从错误中提取更多信息
        try:
            # 检查是否有response属性
            response = getattr(error, 'response', None)
            if response is not None:
                # 检查是否有status_code属性
                status_code = getattr(response, 'status_code', None)
                if status_code is not None:
                    if status_code == 401:
                        return LLMAuthenticationError("OpenAI API密钥无效")
                    elif status_code == 429:
                        retry_after = None
                        headers = getattr(response, 'headers', None)
                        if headers and 'retry-after' in headers:
                            retry_after = int(headers['retry-after'])
                        return LLMRateLimitError("OpenAI API频率限制", retry_after=retry_after)
                    elif status_code == 404:
                        return LLMModelNotFoundError(self.config.model_name)
                    elif status_code == 400:
                        return LLMInvalidRequestError("OpenAI API请求无效")
                    elif status_code == 500 or status_code == 502 or status_code == 503:
                        return LLMServiceUnavailableError("OpenAI服务不可用")
        except (AttributeError, ValueError, TypeError):
            # 如果访问属性时出错，忽略并继续执行其他错误检查
            pass
        
        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            return LLMTimeoutError(str(error), timeout=self.config.timeout)
        elif "rate limit" in error_str or "too many requests" in error_str:
            return LLMRateLimitError(str(error))
        elif "authentication" in error_str or "unauthorized" in error_str or "invalid api key" in error_str:
            return LLMAuthenticationError(str(error))
        elif "model not found" in error_str or "not found" in error_str:
            return LLMModelNotFoundError(self.config.model_name)
        elif "token" in error_str and "limit" in error_str:
            return LLMTokenLimitError(str(error))
        elif "content filter" in error_str or "content policy" in error_str:
            return LLMContentFilterError(str(error))
        elif "service unavailable" in error_str or "503" in error_str:
            return LLMServiceUnavailableError(str(error))
        elif "invalid request" in error_str or "bad request" in error_str:
            return LLMInvalidRequestError(str(error))
        else:
            return LLMCallError(str(error))
    
    def _do_stream_generate(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> Generator[str, None, None]:
        """执行流式生成操作"""
        try:
            # 流式生成
            stream = self._client.stream(messages, **parameters)
            
            # 收集完整响应
            for chunk in stream:
                if chunk.content:
                    # 使用_extract_content方法确保返回字符串类型
                    content = self._extract_content(chunk)
                    if content:
                        yield content
                    
        except Exception as e:
            # 处理OpenAI特定错误
            raise self._handle_openai_error(e)

    def _do_stream_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 异步流式生成
                stream = self._client.astream(messages, **parameters)
                
                # 收集完整响应
                async for chunk in stream:
                    if chunk.content:
                        # 使用_extract_content方法确保返回字符串类型
                        content = self._extract_content(chunk)
                        if content:
                            yield content
                        
            except Exception as e:
                # 处理OpenAI特定错误
                raise self._handle_openai_error(e)
        
        return _async_generator()