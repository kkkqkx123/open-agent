"""LLM错误处理器"""

import json
import re
from typing import Dict, Any, Optional, Type, Union, Callable
from abc import ABC, abstractmethod

from .exceptions import (
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
    LLMConfigurationError
)


class IErrorHandler(ABC):
    """错误处理器接口"""
    
    @abstractmethod
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> LLMCallError:
        """
        处理错误
        
        Args:
            error: 原始错误
            context: 错误上下文
            
        Returns:
            LLMCallError: 处理后的错误
        """
        pass
    
    @abstractmethod
    def is_retryable(self, error: LLMCallError) -> bool:
        """
        判断错误是否可重试
        
        Args:
            error: 错误对象
            
        Returns:
            bool: 是否可重试
        """
        pass


class BaseErrorHandler(IErrorHandler):
    """基础错误处理器"""
    
    def __init__(self) -> None:
        """初始化错误处理器"""
        self._error_mappings = self._init_error_mappings()
        self._custom_error_handlers = self._init_custom_handlers()
        self._retryable_errors = {
            LLMTimeoutError,
            LLMRateLimitError,
            LLMServiceUnavailableError
        }
    
    def _init_error_mappings(self) -> Dict[Type[Exception], Type[LLMCallError]]:
        """初始化错误映射"""
        return {
            # 超时错误
            TimeoutError: LLMTimeoutError,
            
            # 连接错误
            ConnectionError: LLMServiceUnavailableError,
            
            # HTTP错误
            # 这些将在子类中具体实现
        }
    
    def _init_custom_handlers(self) -> Dict[Type[Exception], Callable[[Exception], LLMCallError]]:
        """初始化自定义错误处理器"""
        return {}
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> LLMCallError:
        """
        处理错误
        
        Args:
            error: 原始错误
            context: 错误上下文
            
        Returns:
            LLMCallError: 处理后的错误
        """
        # 首先尝试自定义错误处理器
        error_type = type(error)
        if error_type in self._custom_error_handlers:
            handler = self._custom_error_handlers[error_type]
            return handler(error)
        
        # 然后尝试类型映射
        if error_type in self._error_mappings:
            llm_error_class = self._error_mappings[error_type]
            return llm_error_class(str(error))
        
        # 尝试基于错误消息的映射
        return self._handle_error_by_message(error, context)
    
    def is_retryable(self, error: LLMCallError) -> bool:
        """
        判断错误是否可重试
        
        Args:
            error: 错误对象
            
        Returns:
            bool: 是否可重试
        """
        return type(error) in self._retryable_errors
    
    def _handle_error_by_message(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> LLMCallError:
        """
        基于错误消息处理错误
        
        Args:
            error: 原始错误
            context: 错误上下文
            
        Returns:
            LLMCallError: 处理后的错误
        """
        error_str = str(error).lower()
        
        # 超时错误
        if any(keyword in error_str for keyword in ["timeout", "timed out", "time out"]):
            return LLMTimeoutError(str(error))
        
        # 频率限制错误
        if any(keyword in error_str for keyword in ["rate limit", "too many requests", "rate_limit_exceeded"]):
            return LLMRateLimitError(str(error))
        
        # 认证错误
        if any(keyword in error_str for keyword in ["authentication", "unauthorized", "invalid api key", "forbidden"]):
            return LLMAuthenticationError(str(error))
        
        # 模型未找到错误
        if any(keyword in error_str for keyword in ["model not found", "not found", "invalid model"]):
            return LLMModelNotFoundError("unknown")
        
        # Token限制错误
        if any(keyword in error_str for keyword in ["token", "limit", "too long"]):
            return LLMTokenLimitError(str(error))
        
        # 内容过滤错误
        if any(keyword in error_str for keyword in ["content filter", "content policy", "blocked", "safety"]):
            return LLMContentFilterError(str(error))
        
        # 服务不可用错误
        if any(keyword in error_str for keyword in ["service unavailable", "503", "502", "500"]):
            return LLMServiceUnavailableError(str(error))
        
        # 无效请求错误
        if any(keyword in error_str for keyword in ["invalid request", "bad request", "400"]):
            return LLMInvalidRequestError(str(error))
        
        # 默认为通用调用错误
        return LLMCallError(str(error))


class OpenAIErrorHandler(BaseErrorHandler):
    """OpenAI错误处理器"""
    
    def _init_custom_handlers(self) -> Dict[Type[Exception], Callable[[Exception], LLMCallError]]:
        """初始化OpenAI特定的自定义错误处理器"""
        handlers = super()._init_custom_handlers()
        
        # OpenAI特定错误处理器
        try:
            from openai import OpenAIError
            handlers[OpenAIError] = self._handle_openai_error
        except ImportError:
            pass
        
        return handlers
    
    def _handle_openai_error(self, error: Exception) -> LLMCallError:
        """处理OpenAI特定错误"""
        try:
            # 尝试解析OpenAI错误
            # 使用更安全的方式检查属性
            error_str = str(error).lower()
            
            # 基于错误消息判断
            if "401" in error_str or "unauthorized" in error_str or "authentication" in error_str:
                return LLMAuthenticationError("OpenAI API密钥无效")
            elif "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                return LLMRateLimitError("OpenAI API频率限制")
            elif "404" in error_str or "not found" in error_str:
                return LLMModelNotFoundError("OpenAI模型未找到")
            elif "400" in error_str or "bad request" in error_str:
                return LLMInvalidRequestError("OpenAI API请求无效")
            elif "500" in error_str or "502" in error_str or "503" in error_str or "service unavailable" in error_str:
                return LLMServiceUnavailableError("OpenAI服务不可用")
            
            # 基于错误消息判断
            return super()._handle_error_by_message(error)
            
        except Exception:
            # 如果解析失败，返回通用错误
            return LLMCallError(str(error))


class GeminiErrorHandler(BaseErrorHandler):
    """Gemini错误处理器"""
    
    def _init_error_mappings(self) -> Dict[Type[Exception], Type[LLMCallError]]:
        """初始化Gemini特定的错误映射"""
        mappings = super()._init_error_mappings()
        
        # Gemini特定错误
        # 注意：由于项目使用 langchain-google-genai 而不是直接的 google-generativeai，
        # 我们无法直接导入 Gemini 特定的异常类，因此依赖基于错误消息的处理
        # 如果需要更精确的错误处理，可以考虑添加 google-generativeai 依赖
        
        return mappings
    
    def _handle_error_by_message(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> LLMCallError:
        """处理Gemini特定错误"""
        error_str = str(error).lower()
        
        # Gemini特定错误处理
        if any(keyword in error_str for keyword in ["permission", "forbidden", "permission_denied"]):
            return LLMAuthenticationError("Gemini API权限不足")
        
        if any(keyword in error_str for keyword in ["quota", "billing", "usage"]):
            return LLMRateLimitError("Gemini API配额限制")
        
        # 调用父类方法
        return super()._handle_error_by_message(error, context)


class AnthropicErrorHandler(BaseErrorHandler):
    """Anthropic错误处理器"""
    
    def _init_custom_handlers(self) -> Dict[Type[Exception], Callable[[Exception], LLMCallError]]:
        """初始化Anthropic特定的自定义错误处理器"""
        handlers = super()._init_custom_handlers()
        
        # Anthropic特定错误处理器
        try:
            from anthropic import APIError
            handlers[APIError] = self._handle_anthropic_error
        except ImportError:
            pass
        
        return handlers
    
    def _handle_anthropic_error(self, error: Exception) -> LLMCallError:
        """处理Anthropic特定错误"""
        try:
            # 尝试解析Anthropic错误
            # 使用更安全的方式检查属性
            error_str = str(error).lower()
            
            # 基于错误消息判断
            if "401" in error_str or "403" in error_str or "unauthorized" in error_str or "forbidden" in error_str:
                return LLMAuthenticationError("Anthropic API密钥无效或权限不足")
            elif "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                return LLMRateLimitError("Anthropic API频率限制")
            elif "404" in error_str or "not found" in error_str:
                return LLMModelNotFoundError("Anthropic模型未找到")
            elif "400" in error_str or "bad request" in error_str:
                return LLMInvalidRequestError("Anthropic API请求无效")
            elif "500" in error_str or "502" in error_str or "503" in error_str or "service unavailable" in error_str:
                return LLMServiceUnavailableError("Anthropic服务不可用")
            
            # 基于错误消息判断
            return super()._handle_error_by_message(error)
            
        except Exception:
            # 如果解析失败，返回通用错误
            return LLMCallError(str(error))


class ErrorHandlerFactory:
    """错误处理器工厂"""
    
    @staticmethod
    def create_handler(model_type: str) -> IErrorHandler:
        """
        创建错误处理器
        
        Args:
            model_type: 模型类型
            
        Returns:
            IErrorHandler: 错误处理器实例
        """
        if model_type == "openai":
            return OpenAIErrorHandler()
        elif model_type == "gemini":
            return GeminiErrorHandler()
        elif model_type in ["anthropic", "claude"]:
            return AnthropicErrorHandler()
        else:
            # 默认使用基础错误处理器
            return BaseErrorHandler()
    
    @staticmethod
    def get_supported_types() -> list[str]:
        """
        获取支持的模型类型
        
        Returns:
            list[str]: 支持的模型类型列表
        """
        return ["openai", "gemini", "anthropic", "claude"]


class ErrorContext:
    """错误上下文"""
    
    def __init__(self, model_name: str, model_type: str, request_id: Optional[str] = None) -> None:
        """
        初始化错误上下文
        
        Args:
            model_name: 模型名称
            model_type: 模型类型
            request_id: 请求ID
        """
        self.model_name = model_name
        self.model_type = model_type
        self.request_id = request_id
        self.timestamp = None
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }