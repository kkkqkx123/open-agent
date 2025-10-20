"""Token解析器基础接口和抽象类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


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


class ITokenParser(ABC):
    """Token解析器接口"""
    
    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析API响应中的token使用信息
        
        Args:
            response: API响应数据
            
        Returns:
            TokenUsage: 解析出的token使用信息，如果解析失败返回None
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
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        pass