"""LLM降级管理接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
from ..base import LLMResponse

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage


class IFallbackManager(ABC):
    """降级管理器接口"""
    
    @abstractmethod
    async def execute_with_fallback(
        self,
        primary_target: str,
        fallback_groups: List[str],
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """执行带降级的请求"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
    
    @abstractmethod
    def reset_stats(self) -> None:
        """重置统计信息"""
        pass


class IFallbackStrategy(ABC):
    """降级策略接口"""
    
    @abstractmethod
    def should_fallback(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该降级
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该降级
        """
        pass
    
    @abstractmethod
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]:
        """
        获取降级目标
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            降级目标模型名称，None表示不降级
        """
        pass
    
    @abstractmethod
    def get_fallback_delay(self, error: Exception, attempt: int) -> float:
        """
        获取降级前的延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        pass


class IFallbackLogger(ABC):
    """降级日志记录器接口"""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def log_fallback_failure(self, primary_model: str, error: Exception,
                           total_attempts: int) -> None:
        """
        记录降级失败
        
        Args:
            primary_model: 主模型名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        pass
    
    @abstractmethod
    def log_retry_success(self, func_name: str, result: Any, attempt: int) -> None:
        """
        记录重试成功
        
        Args:
            func_name: 函数名称
            result: 结果
            attempt: 尝试次数
        """
        pass
    
    @abstractmethod
    def log_retry_failure(self, func_name: str, error: Exception, total_attempts: int) -> None:
        """
        记录重试失败
        
        Args:
            func_name: 函数名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        pass