"""Token处理模块

提供统一的Token计算和解析功能。
"""

from .base_processor import ITokenProcessor, TokenUsage
from .openai_processor import OpenAITokenProcessor
from .anthropic_processor import AnthropicTokenProcessor
from .gemini_processor import GeminiTokenProcessor

# 处理器映射
PROCESSOR_MAP = {
    "openai": OpenAITokenProcessor,
    "anthropic": AnthropicTokenProcessor,
    "gemini": GeminiTokenProcessor,
}

def create_token_processor(provider: str, model_name: str) -> ITokenProcessor:
    """
    创建Token处理器
    
    Args:
        provider: 提供商名称
        model_name: 模型名称
        
    Returns:
        ITokenProcessor: Token处理器实例
        
    Raises:
        ValueError: 不支持的提供商
    """
    processor_class = PROCESSOR_MAP.get(provider.lower())
    if not processor_class:
        raise ValueError(f"不支持的Token处理器提供商: {provider}")
    
    return processor_class(model_name=model_name)

def get_supported_providers() -> list[str]:
    """
    获取支持的提供商列表
    
    Returns:
        list[str]: 支持的提供商名称列表
    """
    return list(PROCESSOR_MAP.keys())

__all__ = [
    "ITokenProcessor",
    "TokenUsage",
    "OpenAITokenProcessor",
    "AnthropicTokenProcessor",
    "GeminiTokenProcessor",
    "PROCESSOR_MAP",
    "create_token_processor",
    "get_supported_providers"
]