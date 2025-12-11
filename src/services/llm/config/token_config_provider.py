"""Token配置提供者实现

基于Provider配置发现器实现Token配置提供功能。
"""

from typing import Dict, Any, Optional, List

from src.interfaces.dependency_injection import get_logger
from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    TokenCalculationConfig,
    TokenCostInfo
)
from src.infrastructure.config.impl.llm_config_impl import LLMConfigImpl
from src.infrastructure.config.impl.llm_config_impl import ProviderInfo
from src.services.llm.utils.config_extractor import TokenConfigExtractor, create_config_key
from src.infrastructure.common.cache import ConfigCache

logger = get_logger(__name__)


class ProviderConfigTokenConfigProvider(ITokenConfigProvider):
    """基于Provider配置的Token配置提供者
    
    从配置发现器中获取Token计算相关配置。
    """
    
    def __init__(self, llm_config_impl: LLMConfigImpl):
        """
        初始化配置提供者
        
        Args:
            llm_config_impl: LLM配置实现
        """
        self._llm_config_impl = llm_config_impl
        self._config_cache = ConfigCache()
        
        logger.debug("ProviderConfigTokenConfigProvider初始化完成")
    
    def get_token_config(self, model_type: str, model_name: str) -> Optional[TokenCalculationConfig]:
        """
        获取指定模型的Token计算配置
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[TokenCalculationConfig]: Token计算配置
        """
        config_key = create_config_key(model_type, model_name)
        
        # 检查缓存
        cached_config = self._config_cache.get(config_key)
        if cached_config is not None:
            return cached_config  # type: ignore
        
        # 从Provider配置中加载
        config = self._load_config_from_provider(model_type, model_name)
        
        # 缓存配置
        if config:
            self._config_cache.put(config_key, config)
        
        return config
    
    def _load_config_from_provider(self, model_type: str, model_name: str) -> Optional[TokenCalculationConfig]:
        """
        从Provider配置中加载配置
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[TokenCalculationConfig]: Token计算配置
        """
        try:
            # 获取Provider配置
            provider_config = self._llm_config_impl.get_provider_config(model_type, model_name)
            
            if not provider_config:
                logger.debug(f"未找到Provider配置: {model_type}:{model_name}")
                return None
            
            # 提取Token计算配置
            return self._extract_token_config(provider_config, model_type, model_name)
            
        except Exception as e:
            logger.warning(f"加载Provider Token配置失败 {model_type}:{model_name}: {e}")
            return None
    
    def _extract_token_config(
        self,
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
        return TokenConfigExtractor.extract_token_config(provider_config, model_type, model_name)
    
    def get_supported_models(self) -> Dict[str, List[str]]:
        """
        获取支持的模型列表
        
        Returns:
            Dict[str, List[str]]: 按提供商分组的模型列表
        """
        try:
            providers = self._llm_config_impl.discover_providers()
            result = {}
            for provider_name, provider_info in providers.items():
                result[provider_name] = provider_info.models
            return result
        except Exception as e:
            logger.error(f"获取支持的模型列表失败: {e}")
            return {}
    
    def is_model_supported(self, model_type: str, model_name: str) -> bool:
        """
        检查是否支持指定模型
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            bool: 是否支持该模型
        """
        try:
            return self._llm_config_impl.validate_client_config(model_name)
        except Exception as e:
            logger.error(f"验证模型支持失败 {model_type}:{model_name}: {e}")
            return False
    
    def refresh_config_cache(self) -> None:
        """
        刷新配置缓存
        """
        self._config_cache.clear()
        self._llm_config_impl.invalidate_cache()
        
        logger.info("Token配置缓存已刷新")


class ProviderConfigTokenCostCalculator(ITokenCostCalculator):
    """基于Provider配置的Token成本计算器
    
    根据Provider配置中的定价信息计算Token使用成本。
    """
    
    def __init__(self, config_provider: ITokenConfigProvider):
        """
        初始化成本计算器
        
        Args:
            config_provider: Token配置提供者
        """
        self._config_provider = config_provider
        
        logger.debug("ProviderConfigTokenCostCalculator初始化完成")
    
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
            Optional[TokenCostInfo]: 成本信息
        """
        try:
            # 获取模型配置
            token_config = self._config_provider.get_token_config(model_type, model_name)
            
            if not token_config:
                logger.debug(f"未找到模型配置: {model_type}:{model_name}")
                return None
            
            # 计算成本
            input_cost = 0.0
            output_cost = 0.0
            
            if token_config.cost_per_input_token:
                input_cost = input_tokens * token_config.cost_per_input_token
            
            if token_config.cost_per_output_token:
                output_cost = output_tokens * token_config.cost_per_output_token
            
            total_cost = input_cost + output_cost
            
            return TokenCostInfo(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                currency="USD",
                model_type=model_type,
                model_name=model_name
            )
            
        except Exception as e:
            logger.error(f"计算Token成本失败 {model_type}:{model_name}: {e}")
            return None
    
    def get_model_pricing_info(self, model_type: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型定价信息
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[Dict[str, Any]]: 定价信息
        """
        try:
            token_config = self._config_provider.get_token_config(model_type, model_name)
            
            if not token_config:
                return None
            
            return {
                "model_type": model_type,
                "model_name": model_name,
                "input_token_cost": token_config.cost_per_input_token,
                "output_token_cost": token_config.cost_per_output_token,
                "tokenizer_type": token_config.tokenizer_type,
                "custom_tokenizer": token_config.custom_tokenizer,
                "fallback_enabled": token_config.fallback_enabled,
                "cache_enabled": token_config.cache_enabled
            }
            
        except Exception as e:
            logger.error(f"获取模型定价信息失败 {model_type}:{model_name}: {e}")
            return None