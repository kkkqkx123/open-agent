"""Token配置相关接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenCalculationConfig:
    """Token计算配置数据模型"""
    provider_name: str
    model_name: str
    tokenizer_type: Optional[str] = None
    tokenizer_config: Optional[Dict[str, Any]] = None
    cost_per_input_token: Optional[float] = None
    cost_per_output_token: Optional[float] = None
    custom_tokenizer: Optional[str] = None
    fallback_enabled: bool = True
    cache_enabled: bool = True


@dataclass
class TokenCostInfo:
    """Token成本信息数据模型"""
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    currency: str = "USD"
    model_type: str = ""
    model_name: str = ""


class ITokenConfigProvider(ABC):
    """Token配置提供者接口
    
    负责提供Token计算相关的配置信息，包括处理器配置和定价信息。
    """

    @abstractmethod
    def get_token_config(self, model_type: str, model_name: str) -> Optional[TokenCalculationConfig]:
        """
        获取指定模型的Token计算配置
        
        Args:
            model_type: 模型类型（如 openai, anthropic, gemini）
            model_name: 模型名称（如 gpt-4, claude-3-sonnet）
            
        Returns:
            Optional[TokenCalculationConfig]: Token计算配置，如果未找到则返回None
        """
        pass

    @abstractmethod
    def get_supported_models(self) -> Dict[str, list[str]]:
        """
        获取支持的模型列表
        
        Returns:
            Dict[str, list[str]]: 按提供商分组的模型列表
        """
        pass

    @abstractmethod
    def is_model_supported(self, model_type: str, model_name: str) -> bool:
        """
        检查是否支持指定模型
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            bool: 是否支持该模型
        """
        pass

    @abstractmethod
    def refresh_config_cache(self) -> None:
        """
        刷新配置缓存
        
        当配置发生变更时，可以调用此方法刷新缓存。
        """
        pass


class ITokenCostCalculator(ABC):
    """Token成本计算器接口
    
    负责根据Token使用情况和定价信息计算成本。
    """

    @abstractmethod
    def calculate_cost(
        self, 
        input_tokens: int, 
        output_tokens: int, 
        model_type: str, 
        model_name: str
    ) -> Optional[TokenCostInfo]:
        """
        计算Token使用成本
        
        Args:
            input_tokens: 输入token数量
            output_tokens: 输出token数量
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[TokenCostInfo]: 成本信息，如果无法计算则返回None
        """
        pass

    @abstractmethod
    def get_model_pricing_info(self, model_type: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型定价信息
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[Dict[str, Any]]: 定价信息，如果未找到则返回None
        """
        pass