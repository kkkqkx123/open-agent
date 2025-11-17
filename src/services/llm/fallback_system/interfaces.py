"""降级接口定义"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Sequence
from langchain_core.messages import BaseMessage

from src.core.llm.models import LLMResponse
from src.core.llm.exceptions import LLMCallError


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


class IClientFactory(ABC):
    """客户端工厂接口"""
    
    @abstractmethod
    def create_client(self, model_name: str) -> Any:
        """
        创建客户端实例
        
        Args:
            model_name: 模型名称
            
        Returns:
            客户端实例
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            模型名称列表
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