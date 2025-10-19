"""Gemini客户端实现"""

import json
import time
from typing import Dict, Any, Optional, List, AsyncGenerator, Generator
import asyncio

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from .base import BaseLLMClient
from ..models import LLMResponse, TokenUsage
from ..config import GeminiConfig
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


class GeminiClient(BaseLLMClient):
    """Gemini客户端实现"""
    
    def __init__(self, config: GeminiConfig) -> None:
        """
        初始化Gemini客户端
        
        Args:
            config: Gemini配置
        """
        super().__init__(config)
        
        # 获取解析后的HTTP标头
        resolved_headers = config.get_resolved_headers()
        
        # 创建LangChain ChatGoogleGenerativeAI实例
        # 准备模型参数
        model_kwargs = {}
        
        # 基础参数
        if config.max_tokens is not None:
            model_kwargs["max_tokens"] = config.max_tokens
        if config.max_output_tokens is not None:
            model_kwargs["max_output_tokens"] = config.max_output_tokens
        
        # 采样参数
        if config.top_p is not None:
            model_kwargs["top_p"] = config.top_p
        if config.top_k is not None:
            model_kwargs["top_k"] = config.top_k
        
        # 停止序列
        if config.stop_sequences is not None:
            model_kwargs["stop_sequences"] = config.stop_sequences
        
        # 候选数量
        if config.candidate_count is not None:
            model_kwargs["candidate_count"] = config.candidate_count
        
        # 系统指令
        if config.system_instruction is not None:
            model_kwargs["system_instruction"] = config.system_instruction
        
        # 响应MIME类型
        if config.response_mime_type is not None:
            model_kwargs["response_mime_type"] = config.response_mime_type
        
        # 思考配置
        if config.thinking_config is not None:
            model_kwargs["thinking_config"] = config.thinking_config
        
        # 安全设置
        if config.safety_settings is not None:
            model_kwargs["safety_settings"] = config.safety_settings
        
        # 工具调用参数
        if config.tools:
            model_kwargs["tools"] = config.tools
            if config.tool_choice is not None:
                model_kwargs["tool_choice"] = config.tool_choice
        
        # 用户标识
        if config.user is not None:
            model_kwargs["user"] = config.user
        
        self._client = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.api_key,
            temperature=config.temperature,
            timeout=config.timeout,
            max_retries=config.max_retries,
            request_timeout=config.timeout,
            **model_kwargs
        )
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """转换消息格式以适应Gemini API"""
        converted_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                # Gemini不直接支持系统消息，将其转换为用户消息
                converted_messages.append(
                    HumanMessage(content=f"系统指令: {message.content}")
                )
            else:
                converted_messages.append(message)
        
        return converted_messages
    
    def _do_generate(
       self,
       messages: List[BaseMessage],
       parameters: Dict[str, Any],
       **kwargs: Any
   ) -> LLMResponse:
        """执行生成操作"""
        try:
            # 转换消息格式
            converted_messages = self._convert_messages(messages)
            
            # 调用Gemini API
            response = self._client.invoke(converted_messages, **parameters)
            
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
            # 处理Gemini特定错误
            raise self._handle_gemini_error(e)
    
    async def _do_generate_async(
       self,
       messages: List[BaseMessage],
       parameters: Dict[str, Any],
       **kwargs: Any
   ) -> LLMResponse:
        """执行异步生成操作"""
        try:
            # 转换消息格式
            converted_messages = self._convert_messages(messages)
            
            # 调用Gemini API
            response = await self._client.ainvoke(converted_messages, **parameters)
            
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
            # 处理Gemini特定错误
            raise self._handle_gemini_error(e)
    
    def get_token_count(self, text: str) -> int:
        """计算文本的token数量"""
        from ..token_counter import TokenCounterFactory
        
        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("gemini", self.config.model_name)
        return counter.count_tokens(text)
    
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表的token数量"""
        from ..token_counter import TokenCounterFactory
        
        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("gemini", self.config.model_name)
        return counter.count_messages_tokens(messages)
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # Gemini支持函数调用
        return True
    
    def _extract_token_usage(self, response: Any) -> TokenUsage:
        """提取Token使用情况"""
        # Gemini可能不提供详细的token使用情况
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
            return response.additional_kwargs['function_call']
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
    
    def _handle_gemini_error(self, error: Exception) -> LLMCallError:
        """处理Gemini特定错误"""
        error_str = str(error).lower()
        
        # 尝试从错误中提取更多信息
        try:
            # 检查是否有response属性
            response = getattr(error, 'response', None)
            if response is not None:
                # 检查是否有status_code属性
                status_code = getattr(response, 'status_code', None)
                if status_code is not None:
                    if status_code == 401 or status_code == 403:
                        return LLMAuthenticationError("Gemini API密钥无效或权限不足")
                    elif status_code == 429:
                        retry_after = None
                        headers = getattr(response, 'headers', None)
                        if headers and 'retry-after' in headers:
                            retry_after = int(headers['retry-after'])
                        return LLMRateLimitError("Gemini API频率限制", retry_after=retry_after)
                    elif status_code == 404:
                        return LLMModelNotFoundError(self.config.model_name)
                    elif status_code == 400:
                        return LLMInvalidRequestError("Gemini API请求无效")
                    elif status_code == 500 or status_code == 502 or status_code == 503:
                        return LLMServiceUnavailableError("Gemini服务不可用")
        except (AttributeError, ValueError, TypeError):
            # 如果访问属性时出错，忽略并继续执行其他错误检查
            pass
        
        # 根据错误消息判断
        if "timeout" in error_str or "timed out" in error_str:
            return LLMTimeoutError(str(error), timeout=self.config.timeout)
        elif "rate limit" in error_str or "quota" in error_str or "too many requests" in error_str:
            return LLMRateLimitError(str(error))
        elif "permission" in error_str or "forbidden" in error_str or "authentication" in error_str:
            return LLMAuthenticationError(str(error))
        elif "model not found" in error_str or "not found" in error_str:
            return LLMModelNotFoundError(self.config.model_name)
        elif "token" in error_str and "limit" in error_str:
            return LLMTokenLimitError(str(error))
        elif "content filter" in error_str or "safety" in error_str or "blocked" in error_str:
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
            # 转换消息格式
            converted_messages = self._convert_messages(messages)
            
            # 流式生成
            stream = self._client.stream(converted_messages, **parameters)
            
            # 收集完整响应
            for chunk in stream:
                if chunk.content:
                    # 使用_extract_content方法确保返回字符串类型
                    content = self._extract_content(chunk)
                    if content:
                        yield content
                    
        except Exception as e:
            # 处理Gemini特定错误
            raise self._handle_gemini_error(e)

    def _do_stream_generate_async(
       self,
       messages: List[BaseMessage],
       parameters: Dict[str, Any],
       **kwargs: Any
   ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        async def _async_generator() -> AsyncGenerator[str, None]:
           try:
               # 转换消息格式
               converted_messages = self._convert_messages(messages)
               
               # 异步流式生成
               stream = self._client.astream(converted_messages, **parameters)
               
               # 收集完整响应
               async for chunk in stream:
                   if chunk.content:
                        # 使用_extract_content方法确保返回字符串类型
                        content = self._extract_content(chunk)
                        if content:
                            yield content
                       
           except Exception as e:
               # 处理Gemini特定错误
               raise self._handle_gemini_error(e)
        
        return _async_generator()