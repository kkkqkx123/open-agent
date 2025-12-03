"""通用错误处理器

提供统一的错误处理和错误消息格式化功能。
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger


class ErrorHandler:
    """通用错误处理器"""
    
    def __init__(self) -> None:
        """初始化错误处理器"""
        self.logger = get_logger(__name__)
    
    @staticmethod
    def handle_validation_error(errors: List[str]) -> str:
        """处理验证错误
        
        Args:
            errors: 验证错误列表
            
        Returns:
            str: 格式化的错误消息
        """
        if not errors:
            return "验证失败，但没有具体错误信息"
        
        if len(errors) == 1:
            return f"验证错误: {errors[0]}"
        else:
            error_list = "\n".join(f"- {error}" for error in errors)
            return f"验证错误:\n{error_list}"
    
    @staticmethod
    def handle_format_error(error: Exception) -> str:
        """处理格式错误
        
        Args:
            error: 格式错误异常
            
        Returns:
            str: 格式化的错误消息
        """
        return f"格式错误: {str(error)}"
    
    def handle_api_error(self, error_response: Dict[str, Any], provider: str) -> str:
        """处理API错误响应
        
        Args:
            error_response: 错误响应
            provider: 提供商名称
            
        Returns:
            str: 用户友好的错误消息
        """
        try:
            # 获取错误信息
            error_info = error_response.get("error", {})
            error_type = error_info.get("type", "unknown")
            error_message = error_info.get("message", "未知错误")
            error_code = error_info.get("code", "")
            
            # 根据提供商和错误类型生成友好消息
            friendly_message = self._get_friendly_error_message(error_type, provider)
            
            # 构建完整错误消息
            if error_code:
                return f"{friendly_message} ({error_code}): {error_message}"
            else:
                return f"{friendly_message}: {error_message}"
        except Exception as e:
            self.logger.error(f"处理API错误失败: {e}")
            return f"{provider} API错误: 无法解析错误响应"
    
    def _get_friendly_error_message(self, error_type: str, provider: str) -> str:
        """获取友好的错误消息
        
        Args:
            error_type: 错误类型
            provider: 提供商名称
            
        Returns:
            str: 友好的错误消息
        """
        # 通用错误映射
        common_mappings = {
            "invalid_request_error": "请求参数无效",
            "authentication_error": "认证失败，请检查API密钥",
            "permission_error": "权限不足",
            "not_found_error": "请求的资源不存在",
            "rate_limit_error": "请求频率过高，请稍后重试",
            "api_error": "API内部错误",
            "overloaded_error": "服务过载，请稍后重试",
            "timeout_error": "请求超时",
            "connection_error": "网络连接错误",
            "ssl_error": "SSL证书错误"
        }
        
        # 提供商特定错误映射
        provider_mappings = self._get_provider_specific_mappings(provider)
        
        # 优先使用提供商特定映射
        if provider in provider_mappings and error_type in provider_mappings[provider]:
            return provider_mappings[provider][error_type]
        
        # 回退到通用映射
        return common_mappings.get(error_type, f"未知错误类型: {error_type}")
    
    def _get_provider_specific_mappings(self, provider: str) -> Dict[str, Dict[str, str]]:
        """获取提供商特定的错误映射
        
        Args:
            provider: 提供商名称
            
        Returns:
            Dict[str, Dict[str, str]]: 提供商错误映射
        """
        mappings = {
            "openai": {
                "invalid_api_key": "OpenAI API密钥无效",
                "insufficient_quota": "OpenAI API配额不足",
                "model_not_found": "OpenAI模型不存在",
                "context_length_exceeded": "OpenAI上下文长度超限",
                "content_filter": "OpenAI内容过滤器阻止了请求"
            },
            "anthropic": {
                "invalid_api_key": "Anthropic API密钥无效",
                "rate_limit_error": "Anthropic API频率限制",
                "permission_denied": "Anthropic API权限被拒绝",
                "overloaded_error": "Anthropic服务过载",
                "content_filter": "Anthropic内容策略阻止了请求"
            },
            "gemini": {
                "permission_denied": "Gemini API权限被拒绝",
                "resource_exhausted": "Gemini API资源耗尽",
                "invalid_argument": "Gemini API参数无效",
                "not_found": "Gemini API资源不存在",
                "quota_exceeded": "Gemini API配额超限"
            }
        }
        
        return mappings
    
    def handle_network_error(self, error: Exception, provider: str) -> str:
        """处理网络错误
        
        Args:
            error: 网络错误异常
            provider: 提供商名称
            
        Returns:
            str: 用户友好的错误消息
        """
        error_message = str(error).lower()
        
        if "timeout" in error_message:
            return f"{provider} API请求超时，请检查网络连接并重试"
        elif "connection" in error_message:
            return f"{provider} API连接失败，请检查网络连接"
        elif "ssl" in error_message or "certificate" in error_message:
            return f"{provider} API SSL证书验证失败"
        elif "dns" in error_message:
            return f"{provider} API DNS解析失败"
        else:
            return f"{provider} API网络错误: {str(error)}"
    
    def handle_parsing_error(self, error: Exception, content_type: str) -> str:
        """处理解析错误
        
        Args:
            error: 解析错误异常
            content_type: 内容类型（如JSON、XML等）
            
        Returns:
            str: 用户友好的错误消息
        """
        return f"{content_type}解析失败: {str(error)}"
    
    def handle_validation_exception(self, exception: Exception) -> str:
        """处理验证异常
        
        Args:
            exception: 验证异常
            
        Returns:
            str: 用户友好的错误消息
        """
        return f"验证异常: {str(exception)}"
    
    def create_error_response(
        self, 
        error_type: str, 
        message: str, 
        provider: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建标准错误响应
        
        Args:
            error_type: 错误类型
            message: 错误消息
            provider: 提供商名称
            error_code: 错误代码
            details: 错误详情
            
        Returns:
            Dict[str, Any]: 标准错误响应
        """
        error_response = {
            "error": {
                "type": error_type,
                "message": message
            }
        }
        
        if provider:
            error_response["error"]["provider"] = provider
        
        if error_code:
            error_response["error"]["code"] = error_code
        
        if details:
            error_response["error"]["details"] = details
        
        return error_response
    
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """记录错误日志
        
        Args:
            error: 错误异常
            context: 错误上下文信息
        """
        try:
            provider = context.get("provider", "unknown")
            operation = context.get("operation", "unknown")
            
            self.logger.error(
                f"提供商 {provider} 在操作 {operation} 中发生错误: {str(error)}",
                extra={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "context": context
                }
            )
        except Exception as e:
            # 避免日志记录本身出错
            print(f"记录错误日志失败: {e}")
    
    def should_retry(self, error_response: Dict[str, Any]) -> bool:
        """判断是否应该重试
        
        Args:
            error_response: 错误响应
            
        Returns:
            bool: 是否应该重试
        """
        error_info = error_response.get("error", {})
        error_type = error_info.get("type", "")
        error_code = error_info.get("code", "")
        
        # 可重试的错误类型
        retryable_types = {
            "rate_limit_error",
            "overloaded_error", 
            "timeout_error",
            "connection_error",
            "api_error"
        }
        
        # 可重试的错误代码
        retryable_codes = {
            "rate_limit_exceeded",
            "service_unavailable",
            "internal_server_error",
            "bad_gateway",
            "gateway_timeout"
        }
        
        return error_type in retryable_types or error_code in retryable_codes
    
    def get_retry_delay(self, error_response: Dict[str, Any], attempt: int) -> float:
        """获取重试延迟时间
        
        Args:
            error_response: 错误响应
            attempt: 当前尝试次数
            
        Returns:
            float: 延迟时间（秒）
        """
        error_info = error_response.get("error", {})
        error_type = error_info.get("type", "")
        
        # 基础延迟
        base_delay = 1.0
        
        # 根据错误类型调整延迟
        if error_type == "rate_limit_error":
            base_delay = 5.0  # 频率限制需要更长延迟
        elif error_type == "overloaded_error":
            base_delay = 2.0  # 服务过载需要中等延迟
        
        # 指数退避
        delay = base_delay * (2 ** (attempt - 1))
        
        # 最大延迟限制
        max_delay = 60.0
        return min(delay, max_delay)