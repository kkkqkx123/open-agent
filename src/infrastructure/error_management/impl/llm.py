"""LLM错误处理器"""

import json
import re
from typing import Dict, Any, Optional, Type, Union, Callable, List, Tuple
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

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
    LLMConfigurationError,
)


class IErrorHandler(ABC):
    """错误处理器接口"""

    @abstractmethod
    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> LLMCallError:
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
            LLMServiceUnavailableError,
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

    def _init_custom_handlers(
        self,
    ) -> Dict[Type[Exception], Callable[[Exception], LLMCallError]]:
        """初始化自定义错误处理器"""
        return {}

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> LLMCallError:
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
            # 尝试传递上下文参数，如果处理器不支持则使用旧方式
            try:
                llm_error = handler(error)
            except TypeError:
                llm_error = handler(error)
                # 确保错误对象包含原始错误和上下文
                if not hasattr(llm_error, 'original_error') or llm_error.original_error is None:
                    llm_error.original_error = error
                if not hasattr(llm_error, 'error_context') or llm_error.error_context is None:
                    llm_error.error_context = context
            return llm_error

        # 然后尝试类型映射
        if error_type in self._error_mappings:
            llm_error_class = self._error_mappings[error_type]
            llm_error = llm_error_class(str(error))
            # 确保错误对象包含原始错误和上下文
            if not hasattr(llm_error, 'original_error') or llm_error.original_error is None:
                llm_error.original_error = error
            if not hasattr(llm_error, 'error_context') or llm_error.error_context is None:
                llm_error.error_context = context
            return llm_error

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

    def _handle_error_by_message(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> LLMCallError:
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
        if any(
            keyword in error_str for keyword in ["timeout", "timed out", "time out"]
        ):
            llm_error = LLMTimeoutError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 频率限制错误
        if any(
            keyword in error_str
            for keyword in ["rate limit", "too many requests", "rate_limit_exceeded"]
        ):
            llm_error = LLMRateLimitError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 认证错误
        if any(
            keyword in error_str
            for keyword in [
                "authentication",
                "unauthorized",
                "invalid api key",
                "forbidden",
            ]
        ):
            llm_error = LLMAuthenticationError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 模型未找到错误
        if any(
            keyword in error_str
            for keyword in ["model not found", "not found", "invalid model"]
        ):
            llm_error = LLMModelNotFoundError("unknown")
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # Token限制错误
        if any(keyword in error_str for keyword in ["token", "limit", "too long"]):
            llm_error = LLMTokenLimitError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 内容过滤错误
        if any(
            keyword in error_str
            for keyword in ["content filter", "content policy", "blocked", "safety"]
        ):
            llm_error = LLMContentFilterError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 服务不可用错误
        if any(
            keyword in error_str
            for keyword in ["service unavailable", "503", "502", "500"]
        ):
            llm_error = LLMServiceUnavailableError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 无效请求错误
        if any(
            keyword in error_str
            for keyword in ["invalid request", "bad request", "400"]
        ):
            llm_error = LLMInvalidRequestError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 默认为通用调用错误
        llm_error = LLMCallError(str(error))
        llm_error.original_error = error
        llm_error.error_context = context
        return llm_error


class OpenAIErrorHandler(BaseErrorHandler):
    """OpenAI错误处理器"""

    def _init_custom_handlers(
        self,
    ) -> Dict[Type[Exception], Callable[[Exception], LLMCallError]]:
        """初始化OpenAI特定的自定义错误处理器"""
        handlers = super()._init_custom_handlers()

        # OpenAI特定错误处理器
        try:
            from openai import OpenAIError

            handlers[OpenAIError] = self._handle_openai_error
        except ImportError:
            pass

        return handlers

    def _handle_openai_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> LLMCallError:
        """处理OpenAI特定错误"""
        try:
            # 尝试解析OpenAI错误
            # 使用更安全的方式检查属性
            error_str = str(error).lower()

            # 基于错误消息判断
            if (
                "401" in error_str
                or "unauthorized" in error_str
                or "authentication" in error_str
            ):
                llm_error = LLMAuthenticationError("OpenAI API密钥无效")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif (
                "429" in error_str
                or "rate limit" in error_str
                or "too many requests" in error_str
            ):
                llm_error = LLMRateLimitError("OpenAI API频率限制")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif "404" in error_str or "not found" in error_str:
                llm_error = LLMModelNotFoundError("OpenAI模型未找到")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif "400" in error_str or "bad request" in error_str:
                llm_error = LLMInvalidRequestError("OpenAI API请求无效")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif (
                "500" in error_str
                or "502" in error_str
                or "503" in error_str
                or "service unavailable" in error_str
            ):
                llm_error = LLMServiceUnavailableError("OpenAI服务不可用")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error

            # 基于错误消息判断
            return super()._handle_error_by_message(error, context)

        except Exception:
            # 如果解析失败，返回通用错误
            llm_error = LLMCallError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error


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

    def _handle_error_by_message(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> LLMCallError:
        """处理Gemini特定错误"""
        error_str = str(error).lower()

        # Gemini特定错误处理
        if any(
            keyword in error_str
            for keyword in ["permission", "forbidden", "permission_denied"]
        ):
            llm_error = LLMAuthenticationError("Gemini API权限不足")
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        if any(keyword in error_str for keyword in ["quota", "billing", "usage"]):
            llm_error = LLMRateLimitError("Gemini API配额限制")
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error

        # 调用父类方法
        return super()._handle_error_by_message(error, context)


class AnthropicErrorHandler(BaseErrorHandler):
    """Anthropic错误处理器"""

    def _init_custom_handlers(
        self,
    ) -> Dict[Type[Exception], Callable[[Exception], LLMCallError]]:
        """初始化Anthropic特定的自定义错误处理器"""
        handlers = super()._init_custom_handlers()

        # Anthropic特定错误处理器
        try:
            from anthropic import APIError

            handlers[APIError] = self._handle_anthropic_error
        except ImportError:
            pass

        return handlers

    def _handle_anthropic_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> LLMCallError:
        """处理Anthropic特定错误"""
        try:
            # 尝试解析Anthropic错误
            # 使用更安全的方式检查属性
            error_str = str(error).lower()

            # 基于错误消息判断
            if (
                "401" in error_str
                or "403" in error_str
                or "unauthorized" in error_str
                or "forbidden" in error_str
            ):
                llm_error = LLMAuthenticationError("Anthropic API密钥无效或权限不足")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif (
                "429" in error_str
                or "rate limit" in error_str
                or "too many requests" in error_str
            ):
                llm_error = LLMRateLimitError("Anthropic API频率限制")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif "404" in error_str or "not found" in error_str:
                llm_error = LLMModelNotFoundError("Anthropic模型未找到")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif "400" in error_str or "bad request" in error_str:
                llm_error = LLMInvalidRequestError("Anthropic API请求无效")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error
            elif (
                "500" in error_str
                or "502" in error_str
                or "503" in error_str
                or "service unavailable" in error_str
            ):
                llm_error = LLMServiceUnavailableError("Anthropic服务不可用")
                llm_error.original_error = error
                llm_error.error_context = context
                return llm_error

            # 基于错误消息判断
            return super()._handle_error_by_message(error, context)

        except Exception:
            # 如果解析失败，返回通用错误
            llm_error = LLMCallError(str(error))
            llm_error.original_error = error
            llm_error.error_context = context
            return llm_error


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
    """增强的错误上下文"""

    def __init__(
        self,
        model_name: str,
        model_type: str,
        request_id: Optional[str] = None
    ) -> None:
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
        
        # 增强的上下文信息
        self.request_parameters: Optional[Dict[str, Any]] = None
        self.request_messages: Optional[List[Any]] = None
        self.response_headers: Optional[Dict[str, str]] = None
        self.response_status: Optional[int] = None
        self.response_body: Optional[str] = None
        self.retry_count: int = 0
        self.fallback_attempts: List[str] = []
        self.error_chain: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}

    def set_request_context(
        self,
        parameters: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Any]] = None,
    ) -> None:
        """设置请求上下文"""
        self.request_parameters = parameters
        self.request_messages = messages

    def set_response_context(
        self,
        headers: Optional[Dict[str, str]] = None,
        status: Optional[int] = None,
        body: Optional[str] = None,
    ) -> None:
        """设置响应上下文"""
        self.response_headers = headers
        self.response_status = status
        self.response_body = body

    def add_retry_attempt(self, retry_count: int) -> None:
        """添加重试尝试记录"""
        self.retry_count = retry_count

    def add_fallback_attempt(self, fallback_model: str) -> None:
        """添加降级尝试记录"""
        self.fallback_attempts.append(fallback_model)

    def add_error_to_chain(
        self,
        error: Exception,
        context: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """添加错误到错误链"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        
        # 添加特定错误的额外信息
        if hasattr(error, 'status_code'):
            error_info["status_code"] = getattr(error, 'status_code', None)
        if hasattr(error, 'retry_after'):
            error_info["retry_after"] = getattr(error, 'retry_after', None)
        if hasattr(error, 'error_code'):
            error_info["error_code"] = getattr(error, 'error_code', None)
            
        self.error_chain.append(error_info)

    def set_performance_metrics(
        self,
        response_time: Optional[float] = None,
        token_usage: Optional[Dict[str, int]] = None,
        queue_time: Optional[float] = None,
    ) -> None:
        """设置性能指标"""
        if response_time is not None:
            self.performance_metrics["response_time"] = response_time
        if token_usage is not None:
            self.performance_metrics["token_usage"] = token_usage
        if queue_time is not None:
            self.performance_metrics["queue_time"] = queue_time

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        result = {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "fallback_attempts": self.fallback_attempts,
            "error_chain": self.error_chain,
            "performance_metrics": self.performance_metrics,
        }
        
        # 添加可选的上下文信息（脱敏处理）
        if self.request_parameters:
            # 脱敏处理敏感参数
            sanitized_params = self._sanitize_parameters(self.request_parameters)
            result["request_parameters"] = sanitized_params
            
        if self.request_messages:
            # 只记录消息数量和类型，不记录具体内容
            result["request_messages_summary"] = {
                "count": len(self.request_messages),
                "types": [type(msg).__name__ for msg in self.request_messages],
            }
            
        if self.response_headers:
            # 脱敏处理响应头
            sanitized_headers = self._sanitize_headers(self.response_headers)
            result["response_headers"] = sanitized_headers
            
        if self.response_status is not None:
            result["response_status"] = self.response_status
            
        if self.response_body:
            # 只记录响应体的前100个字符
            result["response_body_preview"] = self.response_body[:100] + "..." if len(self.response_body) > 100 else self.response_body
            
        return result

    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏处理请求参数"""
        sanitized = {}
        sensitive_keys = ["api_key", "authorization", "token", "password", "secret"]
        
        for key, value in parameters.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_parameters(value)
            else:
                sanitized[key] = value
                
        return sanitized

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """脱敏处理HTTP头"""
        sanitized = {}
        sensitive_keys = ["authorization", "x-api-key", "x-goog-api-key", "cookie"]
        
        for key, value in headers.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = "***"
            else:
                sanitized[key] = value
                
        return sanitized

    def get_error_summary(self) -> str:
        """获取错误摘要"""
        if not self.error_chain:
            return "无错误信息"
            
        primary_error = self.error_chain[-1]
        summary = f"主要错误: {primary_error['error_type']} - {primary_error['error_message']}"
        
        if self.retry_count > 0:
            summary += f" (重试 {self.retry_count} 次)"
            
        if self.fallback_attempts:
            summary += f" (降级到: {', '.join(self.fallback_attempts)})"
            
        return summary

    def get_root_cause(self) -> Optional[Dict[str, Any]]:
        """获取根本原因"""
        if not self.error_chain:
            return None
            
        # 返回第一个错误作为根本原因
        return self.error_chain[0]


@dataclass
class ErrorStatistics:
    """错误统计信息"""
    
    # 基础统计
    total_errors: int = 0
    error_counts_by_type: Dict[str, int] = field(default_factory=dict)
    error_counts_by_model: Dict[str, int] = field(default_factory=dict)
    
    # 时间统计
    first_error_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    
    # 重试和降级统计
    retry_attempts: int = 0
    successful_retries: int = 0
    fallback_attempts: int = 0
    successful_fallbacks: int = 0
    
    # 错误趋势（按小时统计）
    hourly_error_counts: Dict[str, int] = field(default_factory=dict)
    
    # 最近错误列表（最多保存100个）
    recent_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_error(self, error_context: ErrorContext) -> None:
        """添加错误到统计"""
        self.total_errors += 1
        
        # 更新时间
        now = datetime.now()
        if self.first_error_time is None:
            self.first_error_time = now
        self.last_error_time = now
        
        # 按类型统计
        if error_context.error_chain:
            primary_error = error_context.error_chain[-1]
            error_type = primary_error['error_type']
            self.error_counts_by_type[error_type] = self.error_counts_by_type.get(error_type, 0) + 1
        
        # 按模型统计
        model_key = f"{error_context.model_type}:{error_context.model_name}"
        self.error_counts_by_model[model_key] = self.error_counts_by_model.get(model_key, 0) + 1
        
        # 重试和降级统计
        self.retry_attempts += error_context.retry_count
        self.fallback_attempts += len(error_context.fallback_attempts)
        
        # 按小时统计
        hour_key = now.strftime("%Y-%m-%d %H:00")
        self.hourly_error_counts[hour_key] = self.hourly_error_counts.get(hour_key, 0) + 1
        
        # 添加到最近错误列表
        error_summary = {
            "timestamp": now.isoformat(),
            "model_type": error_context.model_type,
            "model_name": error_context.model_name,
            "request_id": error_context.request_id,
            "error_summary": error_context.get_error_summary(),
            "retry_count": error_context.retry_count,
            "fallback_attempts": len(error_context.fallback_attempts),
        }
        
        self.recent_errors.append(error_summary)
        
        # 保持最近错误列表大小
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)
    
    def add_successful_retry(self) -> None:
        """添加成功重试统计"""
        self.successful_retries += 1
    
    def add_successful_fallback(self) -> None:
        """添加成功降级统计"""
        self.successful_fallbacks += 1
    
    def get_error_rate(self, time_window_minutes: int = 60) -> float:
        """获取指定时间窗口内的错误率"""
        if self.last_error_time is None:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        # 统计时间窗口内的错误数量
        recent_count = 0
        for error in self.recent_errors:
            error_time = datetime.fromisoformat(error["timestamp"])
            if error_time >= cutoff_time:
                recent_count += 1
        
        # 计算错误率（每分钟错误数）
        return recent_count / time_window_minutes
    
    def get_top_error_types(self, limit: int = 5) -> List[Tuple[str, int]]:
        """获取最常见的错误类型"""
        sorted_errors = sorted(
            self.error_counts_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_errors[:limit]
    
    def get_top_error_models(self, limit: int = 5) -> List[Tuple[str, int]]:
        """获取错误最多的模型"""
        sorted_models = sorted(
            self.error_counts_by_model.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_models[:limit]
    
    def get_retry_success_rate(self) -> float:
        """获取重试成功率"""
        if self.retry_attempts == 0:
            return 0.0
        return self.successful_retries / self.retry_attempts
    
    def get_fallback_success_rate(self) -> float:
        """获取降级成功率"""
        if self.fallback_attempts == 0:
            return 0.0
        return self.successful_fallbacks / self.fallback_attempts
    
    def get_hourly_trend(self, hours: int = 24) -> Dict[str, int]:
        """获取指定小时数内的错误趋势"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        trend = {}
        
        for hour_key, count in self.hourly_error_counts.items():
            hour_time = datetime.strptime(hour_key, "%Y-%m-%d %H:00")
            if hour_time >= cutoff_time:
                trend[hour_key] = count
        
        return trend
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "total_errors": self.total_errors,
            "error_counts_by_type": self.error_counts_by_type,
            "error_counts_by_model": self.error_counts_by_model,
            "first_error_time": self.first_error_time.isoformat() if self.first_error_time else None,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "retry_attempts": self.retry_attempts,
            "successful_retries": self.successful_retries,
            "fallback_attempts": self.fallback_attempts,
            "successful_fallbacks": self.successful_fallbacks,
            "hourly_error_counts": self.hourly_error_counts,
            "recent_errors": self.recent_errors,
            "metrics": {
                "error_rate_last_hour": self.get_error_rate(60),
                "retry_success_rate": self.get_retry_success_rate(),
                "fallback_success_rate": self.get_fallback_success_rate(),
                "top_error_types": self.get_top_error_types(),
                "top_error_models": self.get_top_error_models(),
            }
        }


class ErrorStatisticsManager:
    """错误统计管理器"""
    
    def __init__(self, max_history_hours: int = 24 * 7) -> None:
        """
        初始化错误统计管理器
        
        Args:
            max_history_hours: 最大历史记录保存时间（小时）
        """
        self.max_history_hours = max_history_hours
        self.statistics = ErrorStatistics()
        self._cleanup_timer = None
    
    def record_error(self, error_context: ErrorContext) -> None:
        """记录错误"""
        self.statistics.add_error(error_context)
        self._cleanup_old_data()
    
    def record_successful_retry(self) -> None:
        """记录成功重试"""
        self.statistics.add_successful_retry()
    
    def record_successful_fallback(self) -> None:
        """记录成功降级"""
        self.statistics.add_successful_fallback()
    
    def get_statistics(self) -> ErrorStatistics:
        """获取错误统计"""
        return self.statistics
    
    def get_error_summary(self) -> str:
        """获取错误摘要"""
        stats = self.statistics
        
        if stats.total_errors == 0:
            return "无错误记录"
        
        summary = (
            f"总错误数: {stats.total_errors}, "
            f"错误率: {stats.get_error_rate():.2f}/分钟, "
            f"重试成功率: {stats.get_retry_success_rate():.1%}, "
            f"降级成功率: {stats.get_fallback_success_rate():.1%}"
        )
        
        top_errors = stats.get_top_error_types(3)
        if top_errors:
            error_types = ", ".join([f"{err_type}({count})" for err_type, count in top_errors])
            summary += f", 主要错误: {error_types}"
        
        return summary
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.statistics = ErrorStatistics()
    
    def _cleanup_old_data(self) -> None:
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_history_hours)
        
        # 清理按小时统计的数据
        keys_to_remove = []
        for hour_key in self.statistics.hourly_error_counts:
            hour_time = datetime.strptime(hour_key, "%Y-%m-%d %H:00")
            if hour_time < cutoff_time:
                keys_to_remove.append(hour_key)
        
        for key in keys_to_remove:
            del self.statistics.hourly_error_counts[key]
        
        # 清理最近错误列表
        self.statistics.recent_errors = [
            error for error in self.statistics.recent_errors
            if datetime.fromisoformat(error["timestamp"]) >= cutoff_time
        ]
    
    def export_statistics(self, format: str = "json") -> str:
        """导出统计信息"""
        if format.lower() == "json":
            return json.dumps(self.statistics.to_dict(), indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            return self._export_to_csv()
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_to_csv(self) -> str:
        """导出为CSV格式"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题
        writer.writerow([
            "Timestamp", "Model_Type", "Model_Name", "Request_ID",
            "Error_Summary", "Retry_Count", "Fallback_Attempts"
        ])
        
        # 写入数据
        for error in self.statistics.recent_errors:
            writer.writerow([
                error["timestamp"],
                error["model_type"],
                error["model_name"],
                error["request_id"] or "",
                error["error_summary"],
                error["retry_count"],
                error["fallback_attempts"],
            ])
        
        return output.getvalue()


# 全局错误统计管理器实例
_global_error_stats_manager: Optional[ErrorStatisticsManager] = None


def get_global_error_stats_manager() -> ErrorStatisticsManager:
    """获取全局错误统计管理器"""
    global _global_error_stats_manager
    if _global_error_stats_manager is None:
        _global_error_stats_manager = ErrorStatisticsManager()
    return _global_error_stats_manager


def set_global_error_stats_manager(manager: ErrorStatisticsManager) -> None:
    """设置全局错误统计管理器"""
    global _global_error_stats_manager
    _global_error_stats_manager = manager