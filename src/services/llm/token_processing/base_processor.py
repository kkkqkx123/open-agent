"""Token处理器基础接口和抽象类

整合了Token计算和解析功能。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, Sequence

from langchain_core.messages import BaseMessage  # type: ignore


@dataclass
class TokenUsage:
    """Token使用数据结构"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    source: str = "local"  # "local" 或 "api"
    timestamp: Optional[datetime] = None
    additional_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.additional_info is None:
            self.additional_info = {}


class ITokenProcessor(ABC):
    """统一的Token处理器接口
    
    整合了Token计算和解析功能。
    """
    
    @abstractmethod
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量，如果无法计算则返回None
        """
        pass
    
    @abstractmethod
    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            api_response: API响应（可选，用于更准确的计算）
            
        Returns:
            Optional[int]: token数量，如果无法计算则返回None
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析API响应中的token使用信息
        
        Args:
            response: API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息，如果解析失败返回None
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        pass
    
    @abstractmethod
    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        """
        从API响应更新token信息
        
        Args:
            response: API响应数据
            context: 上下文文本（可选）
            
        Returns:
            bool: 是否成功更新
        """
        pass
    
    @abstractmethod
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """
        获取最近的API使用情况
        
        Returns:
            Optional[TokenUsage]: 最近的API使用情况，如果没有则返回None
        """
        pass
    
    @abstractmethod
    def is_api_usage_available(self) -> bool:
        """
        检查是否有可用的API使用数据
        
        Returns:
            bool: 是否有可用的API使用数据
        """
        pass
    
    @abstractmethod
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        pass
    
    def calculate_usage_cost(self, usage: TokenUsage, model_pricing: Optional[Dict[str, float]] = None) -> Optional[float]:
        """
        计算Token使用成本
        
        Args:
            usage: Token使用情况
            model_pricing: 模型定价信息，格式为 {"prompt": 0.001, "completion": 0.002}
            
        Returns:
            Optional[float]: 成本，如果无法计算则返回None
        """
        if not model_pricing:
            return None
        
        try:
            prompt_cost = usage.prompt_tokens * model_pricing.get("prompt", 0)
            completion_cost = usage.completion_tokens * model_pricing.get("completion", 0)
            total_cost = prompt_cost + completion_cost
            return total_cost
        except Exception:
            return None
    
    def format_usage_summary(self, usage: TokenUsage) -> str:
        """
        格式化Token使用情况摘要
        
        Args:
            usage: Token使用情况
            
        Returns:
            str: 格式化的摘要字符串
        """
        return (
            f"Token使用情况 - "
            f"提示: {usage.prompt_tokens}, "
            f"完成: {usage.completion_tokens}, "
            f"总计: {usage.total_tokens} "
            f"(来源: {usage.source})"
        )