"""服务层降级策略实现

这个模块提供服务层特有的降级策略功能，包括条件降级工具类。
基础的降级策略已经迁移到基础设施层。
"""

from typing import Optional, List, Callable, Any


class ConditionalFallback:
    """条件降级工具类"""
    
    @staticmethod
    def on_timeout(error: Exception) -> bool:
        """超时条件"""
        return "timeout" in str(error).lower() or "TimeoutError" in type(error).__name__
    
    @staticmethod
    def on_rate_limit(error: Exception) -> bool:
        """频率限制条件"""
        return "rate limit" in str(error).lower() or "RateLimitError" in type(error).__name__
    
    @staticmethod
    def on_service_unavailable(error: Exception) -> bool:
        """服务不可用条件"""
        return "service unavailable" in str(error).lower() or "ServiceUnavailableError" in type(error).__name__
    
    @staticmethod
    def on_authentication_error(error: Exception) -> bool:
        """认证错误条件"""
        return "authentication" in str(error).lower() or "AuthenticationError" in type(error).__name__
    
    @staticmethod
    def on_model_not_found(error: Exception) -> bool:
        """模型未找到条件"""
        return "model not found" in str(error).lower() or "ModelNotFoundError" in type(error).__name__
    
    @staticmethod
    def on_token_limit(error: Exception) -> bool:
        """Token限制条件"""
        return "token limit" in str(error).lower() or "TokenLimitError" in type(error).__name__
    
    @staticmethod
    def on_content_filter(error: Exception) -> bool:
        """内容过滤条件"""
        return "content filter" in str(error).lower() or "ContentFilterError" in type(error).__name__
    
    @staticmethod
    def on_invalid_request(error: Exception) -> bool:
        """无效请求条件"""
        return "invalid request" in str(error).lower() or "InvalidRequestError" in type(error).__name__
    
    @staticmethod
    def on_any_error(error: Exception) -> bool:
        """任意错误条件"""
        return True
    
    @staticmethod
    def on_retryable_error(error: Exception) -> bool:
        """可重试错误条件"""
        retryable_patterns = [
            "timeout", "rate limit", "service unavailable", "overloaded",
            "connection", "network", "temporary"
        ]
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in retryable_patterns)