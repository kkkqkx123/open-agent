"""Token配置提取工具

提供统一的配置提取逻辑，避免重复实现。
"""

from typing import Dict, Any

from src.interfaces.llm import TokenCalculationConfig
from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator as CacheKeyGenerator


def create_config_key(model_type: str, model_name: str) -> str:
    """为模型配置生成缓存键
    
    Args:
        model_type: 模型类型
        model_name: 模型名称
        
    Returns:
        str: 配置缓存键
    """
    return CacheKeyGenerator.generate_composite_key([model_type, model_name])


class TokenConfigExtractor:
     """Token配置提取器
     
     提供统一的配置提取逻辑，从Provider配置中提取Token计算相关配置。
     """
     
     @staticmethod
     def extract_token_config(
        provider_config: Dict[str, Any], 
        model_type: str, 
        model_name: str
    ) -> TokenCalculationConfig:
        """
        从Provider配置中提取Token计算配置
        
        Args:
            provider_config: Provider配置
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            TokenCalculationConfig: Token计算配置
        """
        # 查找token_calculation配置段
        token_config_data = provider_config.get("token_calculation", {})
        
        # 查找pricing配置段
        pricing_config = provider_config.get("pricing", {})
        
        # 查找tokenizer配置段
        tokenizer_config = provider_config.get("tokenizer", {})
        
        return TokenCalculationConfig(
            provider_name=model_type,
            model_name=model_name,
            tokenizer_type=token_config_data.get("type"),
            tokenizer_config=tokenizer_config,
            cost_per_input_token=pricing_config.get("input_token_cost"),
            cost_per_output_token=pricing_config.get("output_token_cost"),
            custom_tokenizer=token_config_data.get("custom_tokenizer"),
            fallback_enabled=token_config_data.get("fallback_enabled", True),
            cache_enabled=token_config_data.get("cache_enabled", True)
        )