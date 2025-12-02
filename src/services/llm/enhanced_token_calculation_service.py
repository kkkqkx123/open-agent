"""增强的Token计算服务

集成Provider配置，支持从Provider配置中获取Token计算相关设置。
"""

from typing import Dict, Any, List, Optional, Sequence, Union
from pathlib import Path
from dataclasses import dataclass

from langchain_core.messages import BaseMessage
from src.services.logger import get_logger
from src.core.llm.config_manager import LLMConfigManager
from src.core.llm.provider_config_discovery import ProviderConfigDiscovery

from .token_calculation_service import TokenCalculationService
from .token_processing.base_processor import ITokenProcessor
from .token_processing.token_types import TokenUsage

logger = get_logger(__name__)


@dataclass
class TokenCalculationConfig:
    """Token计算配置"""
    provider_name: str
    model_name: str
    tokenizer_type: Optional[str] = None
    tokenizer_config: Optional[Dict[str, Any]] = None
    cost_per_input_token: Optional[float] = None
    cost_per_output_token: Optional[float] = None
    custom_tokenizer: Optional[str] = None
    fallback_enabled: bool = True
    cache_enabled: bool = True


class EnhancedTokenCalculationService(TokenCalculationService):
    """增强的Token计算服务
    
    扩展基础Token计算服务，增加：
    1. Provider配置集成
    2. 动态配置加载
    3. 成本计算
    4. 配置驱动的处理器选择
    """
    
    def __init__(
        self, 
        default_provider: str = "openai",
        llm_config_manager: Optional[LLMConfigManager] = None,
        provider_discovery: Optional[ProviderConfigDiscovery] = None
    ):
        """
        初始化增强Token计算服务
        
        Args:
            default_provider: 默认提供商名称
            llm_config_manager: LLM配置管理器
            provider_discovery: Provider配置发现器
        """
        super().__init__(default_provider)
        
        self._llm_config_manager = llm_config_manager
        self._provider_discovery = provider_discovery
        self._token_configs: Dict[str, TokenCalculationConfig] = {}
        self._cost_cache: Dict[str, Dict[str, float]] = {}
        
        logger.debug(f"增强Token计算服务初始化完成，默认提供商: {default_provider}")
    
    def set_config_manager(self, config_manager: LLMConfigManager) -> None:
        """设置LLM配置管理器
        
        Args:
            config_manager: LLM配置管理器
        """
        self._llm_config_manager = config_manager
        logger.debug("已设置LLM配置管理器")
    
    def set_provider_discovery(self, provider_discovery: ProviderConfigDiscovery) -> None:
        """设置Provider配置发现器
        
        Args:
            provider_discovery: Provider配置发现器
        """
        self._provider_discovery = provider_discovery
        logger.debug("已设置Provider配置发现器")
    
    def _get_token_config(self, model_type: str, model_name: str) -> TokenCalculationConfig:
        """获取Token计算配置
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            TokenCalculationConfig: Token计算配置
        """
        config_key = f"{model_type}:{model_name}"
        
        if config_key in self._token_configs:
            return self._token_configs[config_key]
        
        # 从Provider配置中获取Token计算配置
        token_config = self._load_token_config_from_provider(model_type, model_name)
        
        # 缓存配置
        self._token_configs[config_key] = token_config
        return token_config
    
    def _load_token_config_from_provider(self, model_type: str, model_name: str) -> TokenCalculationConfig:
        """从Provider配置中加载Token计算配置
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            TokenCalculationConfig: Token计算配置
        """
        # 默认配置
        default_config = TokenCalculationConfig(
            provider_name=model_type,
            model_name=model_name,
            fallback_enabled=True,
            cache_enabled=True
        )
        
        # 如果没有Provider配置发现器，返回默认配置
        if not self._provider_discovery:
            logger.debug(f"未设置Provider配置发现器，使用默认配置: {model_type}:{model_name}")
            return default_config
        
        try:
            # 尝试从Provider配置中获取
            provider_config = self._provider_discovery.get_provider_config(
                model_type, model_name
            )
            
            if not provider_config:
                logger.debug(f"未找到Provider配置: {model_type}:{model_name}，使用默认配置")
                return default_config
            
            # 提取Token计算相关配置
            token_config = self._extract_token_config(provider_config, model_type, model_name)
            logger.debug(f"从Provider配置加载Token计算配置: {model_type}:{model_name}")
            return token_config
            
        except Exception as e:
            logger.warning(f"加载Provider Token配置失败 {model_type}:{model_name}: {e}，使用默认配置")
            return default_config
    
    def _extract_token_config(self, provider_config: Dict[str, Any], model_type: str, model_name: str) -> TokenCalculationConfig:
        """从Provider配置中提取Token计算配置
        
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
    
    def _get_processor_for_model(self, model_type: str, model_name: str) -> ITokenProcessor:
        """获取指定模型的处理器（增强版）
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            ITokenProcessor: 对应的处理器
        """
        # 获取Token计算配置
        token_config = self._get_token_config(model_type, model_name)
        
        # 创建唯一的处理器键
        processor_key = f"{model_type}:{model_name}"
        
        # 如果处理器已存在，直接返回
        if processor_key in self._processors:
            return self._processors[processor_key]
        
        # 根据配置创建处理器
        processor = self._create_processor_with_config(model_type, model_name, token_config)
        
        # 缓存处理器
        self._processors[processor_key] = processor
        return processor
    
    def _create_processor_with_config(self, model_type: str, model_name: str, token_config: TokenCalculationConfig) -> ITokenProcessor:
        """根据配置创建处理器
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            token_config: Token计算配置
            
        Returns:
            ITokenProcessor: 处理器实例
        """
        # 导入处理器类
        from .token_processing.openai_processor import OpenAITokenProcessor
        from .token_processing.gemini_processor import GeminiTokenProcessor
        from .token_processing.anthropic_processor import AnthropicTokenProcessor
        from .token_processing.hybrid_processor import HybridTokenProcessor
        
        # 根据模型类型和配置创建处理器
        if model_type.lower() == "openai":
            processor = OpenAITokenProcessor(model_name)
        elif model_type.lower() == "gemini":
            processor = GeminiTokenProcessor(model_name)
        elif model_type.lower() == "anthropic":
            processor = AnthropicTokenProcessor(model_name)
        else:
            # 使用混合处理器作为默认选项
            processor = HybridTokenProcessor(model_name, model_type)
        
        # 如果有自定义tokenizer配置，应用它
        if token_config.custom_tokenizer:
            processor = self._apply_custom_tokenizer(processor, token_config.custom_tokenizer)
        
        return processor
    
    def _apply_custom_tokenizer(self, processor: ITokenProcessor, custom_tokenizer: str) -> ITokenProcessor:
        """应用自定义tokenizer
        
        Args:
            processor: 原始处理器
            custom_tokenizer: 自定义tokenizer配置
            
        Returns:
            ITokenProcessor: 增强的处理器
        """
        # 这里可以根据custom_tokenizer配置来增强处理器
        # 例如：加载自定义tokenizer模型、应用特殊规则等
        logger.debug(f"应用自定义tokenizer: {custom_tokenizer}")
        
        # 暂时返回原始处理器，实际实现需要根据具体需求
        return processor
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model_type: str, model_name: str) -> Dict[str, Any]:
        """计算Token使用成本
        
        Args:
            input_tokens: 输入token数量
            output_tokens: 输出token数量
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 成本信息
        """
        token_config = self._get_token_config(model_type, model_name)
        
        input_cost = 0.0
        output_cost = 0.0
        
        if token_config.cost_per_input_token:
            input_cost = input_tokens * token_config.cost_per_input_token
        
        if token_config.cost_per_output_token:
            output_cost = output_tokens * token_config.cost_per_output_token
        
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "currency": "USD",
            "model_type": model_type,
            "model_name": model_name
        }
    
    def get_model_pricing_info(self, model_type: str, model_name: str) -> Dict[str, Any]:
        """获取模型定价信息
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 定价信息
        """
        token_config = self._get_token_config(model_type, model_name)
        
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
    
    def refresh_token_configs(self) -> None:
        """刷新Token配置缓存"""
        self._token_configs.clear()
        self._cost_cache.clear()
        
        # 清除处理器缓存，强制重新创建
        self._processors.clear()
        
        logger.info("Token配置缓存已刷新")
    
    def get_supported_models(self) -> Dict[str, List[str]]:
        """获取支持的模型列表
        
        Returns:
            Dict[str, List[str]]: 支持的模型列表
        """
        if self._provider_discovery:
            return self._provider_discovery.list_all_models()
        
        # 如果没有Provider发现器，返回基础支持的模型
        return {
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            "anthropic": ["claude-3-sonnet", "claude-3-opus"],
            "gemini": ["gemini-pro", "gemini-pro-vision"]
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        return {
            "default_provider": self._default_provider,
            "cached_processors": len(self._processors),
            "cached_token_configs": len(self._token_configs),
            "cached_costs": len(self._cost_cache),
            "has_config_manager": self._llm_config_manager is not None,
            "has_provider_discovery": self._provider_discovery is not None,
            "supported_models": self.get_supported_models()
        }