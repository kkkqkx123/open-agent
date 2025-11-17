"""日志记录器适配器

用于将 Core 层的 DefaultFallbackLogger 适配到 IFallbackLogger 接口。
"""

from typing import Any
from .interfaces import IFallbackLogger
from src.core.llm.models import LLMResponse
from src.core.llm.wrappers.fallback_manager import DefaultFallbackLogger as CoreDefaultFallbackLogger


class LoggerAdapter(IFallbackLogger):
    """日志记录器适配器
    
    将 Core 层的 DefaultFallbackLogger 适配到 IFallbackLogger 接口
    """
    
    def __init__(self, core_logger: CoreDefaultFallbackLogger):
        """
        初始化日志记录器适配器
        
        Args:
            core_logger: Core 层的默认日志记录器
        """
        self._core_logger = core_logger
    
    def log_fallback_attempt(self, primary_model: str, fallback_model: str, 
                            error: Exception, attempt: int) -> None:
        """
        记录降级尝试
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            error: 发生的错误
            attempt: 尝试次数
        """
        self._core_logger.log_fallback_attempt(primary_model, fallback_model, error, attempt)
    
    def log_fallback_success(self, primary_model: str, fallback_model: str, 
                           response: LLMResponse, attempt: int) -> None:
        """
        记录降级成功
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            response: 响应结果
            attempt: 尝试次数
        """
        self._core_logger.log_fallback_success(primary_model, fallback_model, response, attempt)
    
    def log_fallback_failure(self, primary_model: str, error: Exception, 
                           total_attempts: int) -> None:
        """
        记录降级失败
        
        Args:
            primary_model: 主模型名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        self._core_logger.log_fallback_failure(primary_model, error, total_attempts)