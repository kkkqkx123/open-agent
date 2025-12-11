"""
Token计算器工厂

提供统一的Token计算器创建和管理功能。
"""

from typing import Dict, Any, Optional, List, Type
from threading import RLock

from src.interfaces.dependency_injection import get_logger
from .base_token_calculator import ITokenCalculator, BaseTokenCalculator
from .openai_token_calculator import OpenAITokenCalculator
from .gemini_token_calculator import GeminiTokenCalculator
from .anthropic_token_calculator import AnthropicTokenCalculator
from .local_token_calculator import LocalTokenCalculator

logger = get_logger(__name__)


class TokenCalculatorFactory:
    """Token计算器工厂
    
    负责创建、缓存和管理不同提供商的Token计算器实例。
    """
    
    def __init__(self):
        """初始化Token计算器工厂"""
        self._calculators: Dict[str, ITokenCalculator] = {}
        self._lock = RLock()
        
        logger.debug("Token计算器工厂初始化完成")
    
    def create_openai_calculator(self, model_name: str = "gpt-3.5-turbo", enable_cache: bool = True) -> ITokenCalculator:
        """创建OpenAI Token计算器"""
        return OpenAITokenCalculator(model_name=model_name, enable_cache=enable_cache)
    
    def create_gemini_calculator(self, model_name: str = "gemini-pro", enable_cache: bool = True) -> ITokenCalculator:
        """创建Gemini Token计算器"""
        return GeminiTokenCalculator(model_name=model_name, enable_cache=enable_cache)
    
    def create_anthropic_calculator(self, model_name: str = "claude-3-sonnet-20240229", enable_cache: bool = True) -> ITokenCalculator:
        """创建Anthropic Token计算器"""
        return AnthropicTokenCalculator(model_name=model_name, enable_cache=enable_cache)
    
    def create_universal_calculator(self, model_name: str = "default", enable_cache: bool = True) -> ITokenCalculator:
        """创建通用Token计算器"""
        return LocalTokenCalculator(
            provider_name="universal",
            model_name=model_name,
            enable_cache=enable_cache
        )
    
    def create_calculator(
        self,
        provider: str,
        model_name: Optional[str] = None,
        enable_cache: bool = True
    ) -> ITokenCalculator:
        """
        创建Token计算器实例
        
        Args:
            provider: 提供商名称
            model_name: 模型名称
            enable_cache: 是否启用缓存
            
        Returns:
            ITokenCalculator: Token计算器实例
            
        Raises:
            ValueError: 不支持的提供商
        """
        provider_lower = provider.lower()
        
        if provider_lower == "openai":
            return self.create_openai_calculator(model_name or "gpt-3.5-turbo", enable_cache)
        elif provider_lower == "gemini":
            return self.create_gemini_calculator(model_name or "gemini-pro", enable_cache)
        elif provider_lower == "anthropic":
            return self.create_anthropic_calculator(model_name or "claude-3-sonnet-20240229", enable_cache)
        elif provider_lower == "universal":
            return self.create_universal_calculator(model_name or "default", enable_cache)
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    
    def get_calculator(
        self,
        provider: str,
        model_name: Optional[str] = None,
        enable_cache: bool = True
    ) -> ITokenCalculator:
        """
        获取Token计算器实例（带缓存）
        
        Args:
            provider: 提供商名称
            model_name: 模型名称
            enable_cache: 是否启用缓存
            
        Returns:
            ITokenCalculator: Token计算器实例
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(provider, model_name, enable_cache)
        
        with self._lock:
            # 检查缓存
            if cache_key in self._calculators:
                logger.debug(f"从缓存获取Token计算器: {cache_key}")
                return self._calculators[cache_key]
            
            # 创建新实例
            calculator = self.create_calculator(provider, model_name, enable_cache)
            
            # 缓存实例
            self._calculators[cache_key] = calculator
            
            logger.debug(f"缓存Token计算器: {cache_key}")
            return calculator
    
    def _generate_cache_key(
        self,
        provider: str,
        model_name: Optional[str],
        enable_cache: bool
    ) -> str:
        """
        生成缓存键
        
        Args:
            provider: 提供商名称
            model_name: 模型名称
            enable_cache: 是否启用缓存
            
        Returns:
            str: 缓存键
        """
        key_parts = [provider.lower()]
        
        if model_name:
            key_parts.append(model_name)
        
        key_parts.append(f"cache={enable_cache}")
        
        return "|".join(key_parts)
    
    def clear_cache(self) -> None:
        """清空计算器缓存"""
        with self._lock:
            cleared_count = len(self._calculators)
            self._calculators.clear()
            logger.info(f"清空Token计算器缓存，清除了 {cleared_count} 个实例")
    
    def get_cached_calculators(self) -> Dict[str, ITokenCalculator]:
        """
        获取缓存的计算器列表
        
        Returns:
            Dict[str, ITokenCalculator]: 缓存的计算器字典
        """
        with self._lock:
            return self._calculators.copy()
    
    def get_supported_providers(self) -> List[str]:
        """
        获取支持的提供商列表
        
        Returns:
            List[str]: 支持的提供商名称列表
        """
        return ["openai", "gemini", "anthropic", "universal"]
    
    def is_provider_supported(self, provider: str) -> bool:
        """
        检查是否支持指定提供商
        
        Args:
            provider: 提供商名称
            
        Returns:
            bool: 是否支持
        """
        return provider.lower() in self.get_supported_providers()
    
    def create_calculator_for_response(
        self,
        response: Dict[str, Any],
        enable_cache: bool = True
    ) -> Optional[ITokenCalculator]:
        """
        根据API响应创建合适的Token计算器
        
        Args:
            response: API响应
            enable_cache: 是否启用缓存
            
        Returns:
            Optional[ITokenCalculator]: Token计算器实例
        """
        # 尝试从响应中识别提供商
        provider = self._identify_provider_from_response(response)
        
        if not provider:
            logger.warning("无法从响应中识别提供商，使用通用计算器")
            return self.create_universal_calculator(enable_cache=enable_cache)
        
        # 尝试从响应中获取模型名称
        model_name = response.get("model")
        
        try:
            return self.get_calculator(provider, model_name, enable_cache)
        except Exception as e:
            logger.error(f"为响应创建Token计算器失败: {e}")
            # 回退到通用计算器
            return self.create_universal_calculator(enable_cache=enable_cache)
    
    def _identify_provider_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """
        从API响应中识别提供商
        
        Args:
            response: API响应
            
        Returns:
            Optional[str]: 提供商名称
        """
        # 使用通用响应解析器进行识别
        from .token_response_parser import get_token_response_parser
        parser = get_token_response_parser()
        return parser._detect_provider(response)
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """
        获取工厂统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            # 统计各提供商的计算器数量
            provider_stats = {}
            for cache_key, calculator in self._calculators.items():
                provider = cache_key.split("|")[0]
                provider_stats[provider] = provider_stats.get(provider, 0) + 1
            
            return {
                "total_cached_calculators": len(self._calculators),
                "supported_providers": self.get_supported_providers(),
                "provider_distribution": provider_stats,
            }


# 全局工厂实例
_global_factory: Optional[TokenCalculatorFactory] = None


def get_token_calculator_factory() -> TokenCalculatorFactory:
    """
    获取全局Token计算器工厂实例
    
    Returns:
        TokenCalculatorFactory: 工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = TokenCalculatorFactory()
    return _global_factory


def create_token_calculator(
    provider: str,
    model_name: Optional[str] = None,
    enable_cache: bool = True
) -> ITokenCalculator:
    """
    便捷函数：创建Token计算器
    
    Args:
        provider: 提供商名称
        model_name: 模型名称
        enable_cache: 是否启用缓存
        
    Returns:
        ITokenCalculator: Token计算器实例
    """
    factory = get_token_calculator_factory()
    return factory.get_calculator(provider, model_name, enable_cache)