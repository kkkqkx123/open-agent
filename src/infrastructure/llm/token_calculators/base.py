"""Token计算器基础接口和抽象类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from langchain_core.messages import BaseMessage  # type: ignore

from ..token_parsers.base import TokenUsage


class ITokenCalculator(ABC):
    """Token计算器接口"""
    
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
    def count_messages_tokens(self, messages: List[BaseMessage]) -> Optional[int]:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            Optional[int]: token数量，如果无法计算则返回None
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
            TokenUsage: 最近的API使用情况，如果没有则返回None
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