"""Token计算装饰器

为基础TokenCalculationService添加配置驱动的增强功能。
"""

from typing import Dict, Any, Optional, Sequence
from src.infrastructure.messages.base import BaseMessage

from src.interfaces.dependency_injection import get_logger
from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    TokenCostInfo,
    TokenCalculationConfig
)
from src.services.llm.token_calculation_service import TokenCalculationService
# 使用 infrastructure 层的实现
from src.infrastructure.llm.token_calculators import ITokenCalculator
from src.infrastructure.llm.models import TokenUsage
from src.services.llm.utils.config_extractor import TokenConfigExtractor

logger = get_logger(__name__)


class TokenCalculationDecorator:
    """Token计算装饰器
    
    为基础TokenCalculationService添加以下增强功能：
    1. 配置驱动的处理器选择
    2. 成本计算功能
    3. 配置缓存和刷新
    4. 增强的模型支持查询
    """
    
    def __init__(
        self,
        base_service: TokenCalculationService,
        config_provider: Optional[ITokenConfigProvider] = None,
        cost_calculator: Optional[ITokenCostCalculator] = None
    ):
        """
        初始化装饰器
        
        Args:
            base_service: 基础Token计算服务
            config_provider: Token配置提供者
            cost_calculator: Token成本计算器
        """
        self._base_service = base_service
        self._config_provider = config_provider
        self._cost_calculator = cost_calculator
        
        # 如果没有提供成本计算器但有配置提供者，创建默认的成本计算器
        if not self._cost_calculator and self._config_provider:
            from .config import ProviderConfigTokenCostCalculator
            self._cost_calculator = ProviderConfigTokenCostCalculator(self._config_provider)
        
        logger.debug("TokenCalculationDecorator初始化完成")
    
    def set_config_provider(self, config_provider: ITokenConfigProvider) -> None:
        """
        设置配置提供者
        
        Args:
            config_provider: Token配置提供者
        """
        self._config_provider = config_provider
        
        # 重新创建成本计算器
        if self._config_provider:
            from .config import ProviderConfigTokenCostCalculator
            self._cost_calculator = ProviderConfigTokenCostCalculator(self._config_provider)
        
        logger.debug("已设置Token配置提供者")
    
    def set_cost_calculator(self, cost_calculator: ITokenCostCalculator) -> None:
        """
        设置成本计算器
        
        Args:
            cost_calculator: Token成本计算器
        """
        self._cost_calculator = cost_calculator
        logger.debug("已设置Token成本计算器")
    
    def calculate_tokens(self, text: str, model_type: str, model_name: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            int: token数量
        """
        # 使用基础服务计算
        return self._base_service.calculate_tokens(text, model_type, model_name)
    
    def calculate_messages_tokens(self, messages: Sequence[BaseMessage], model_type: str, model_name: str) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            int: token数量
        """
        # 使用基础服务计算
        return self._base_service.calculate_messages_tokens(messages, model_type, model_name)
    
    def parse_token_usage_from_response(self, response: Dict[str, Any], model_type: str) -> Optional[TokenUsage]:
        """
        从API响应中解析token使用情况
        
        Args:
            response: API响应
            model_type: 模型类型
            
        Returns:
            Optional[TokenUsage]: token使用情况
        """
        # 使用基础服务解析
        return self._base_service.parse_token_usage_from_response(response, model_type)
    
    def get_processor_stats(self, model_type: str, model_name: str) -> Dict[str, Any]:
        """
        获取处理器统计信息
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        # 使用基础服务获取统计信息
        return self._base_service.get_processor_stats(model_type, model_name)
    
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
        if not self._cost_calculator:
            logger.warning("未设置成本计算器，无法计算成本")
            return None
        
        return self._cost_calculator.calculate_cost(input_tokens, output_tokens, model_type, model_name)
    
    def get_model_pricing_info(self, model_type: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型定价信息
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[Dict[str, Any]]: 定价信息
        """
        if not self._cost_calculator:
            logger.warning("未设置成本计算器，无法获取定价信息")
            return None
        
        return self._cost_calculator.get_model_pricing_info(model_type, model_name)
    
    def get_supported_models(self) -> Dict[str, list[str]]:
        """
        获取支持的模型列表
        
        Returns:
            Dict[str, list[str]]: 按提供商分组的模型列表
        """
        if self._config_provider:
            return self._config_provider.get_supported_models()
        
        # 如果没有配置提供者，返回基础支持的模型
        return {
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            "anthropic": ["claude-3-sonnet", "claude-3-opus"],
            "gemini": ["gemini-pro", "gemini-pro-vision"]
        }
    
    def is_model_supported(self, model_type: str, model_name: str) -> bool:
        """
        检查是否支持指定模型
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            bool: 是否支持该模型
        """
        if self._config_provider:
            return self._config_provider.is_model_supported(model_type, model_name)
        
        # 如果没有配置提供者，使用基础检查
        supported_models = self.get_supported_models()
        return model_type in supported_models and model_name in supported_models[model_type]
    
    def refresh_config_cache(self) -> None:
        """
        刷新配置缓存
        """
        if self._config_provider:
            self._config_provider.refresh_config_cache()
            logger.info("Token配置缓存已刷新")
        else:
            logger.warning("未设置配置提供者，无法刷新缓存")
    
    def get_enhanced_processor_for_model(self, model_type: str, model_name: str) -> Optional[ITokenCalculator]:
        """
        获取增强的处理器（配置驱动）
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[ITokenCalculator]: 增强的处理器
        """
        if not self._config_provider:
            logger.debug("未设置配置提供者，使用基础处理器")
            return self._base_service._factory.get_calculator(model_type, model_name)
        
        try:
            # 获取配置
            token_config = self._config_provider.get_token_config(model_type, model_name)
            
            if not token_config:
                logger.debug(f"未找到模型配置: {model_type}:{model_name}，使用基础处理器")
                return self._base_service._factory.get_calculator(model_type, model_name)
            
            # 根据配置创建处理器
            return self._create_processor_with_config(model_type, model_name, token_config)
            
        except Exception as e:
            logger.error(f"创建增强处理器失败 {model_type}:{model_name}: {e}")
            return self._base_service._factory.get_calculator(model_type, model_name)
    
    def _create_processor_with_config(
        self,
        model_type: str,
        model_name: str,
        token_config: TokenCalculationConfig
    ) -> ITokenCalculator:
        """
        根据配置创建处理器
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            token_config: Token计算配置
            
        Returns:
            ITokenCalculator: 处理器实例
        """
        # 使用 infrastructure 层的工厂创建处理器
        processor = self._base_service._factory.get_calculator(model_type, model_name)
        
        # 如果有自定义tokenizer配置，应用它
        if token_config.custom_tokenizer:
            processor = self._apply_custom_tokenizer(processor, token_config.custom_tokenizer)
        
        return processor
    
    def _apply_custom_tokenizer(self, processor: ITokenCalculator, custom_tokenizer: str) -> ITokenCalculator:
        """
        应用自定义tokenizer
        
        Args:
            processor: 原始处理器
            custom_tokenizer: 自定义tokenizer配置
            
        Returns:
            ITokenCalculator: 增强的处理器
        """
        # 这里可以根据custom_tokenizer配置来增强处理器
        logger.debug(f"应用自定义tokenizer: {custom_tokenizer}")
        
        # 暂时返回原始处理器，实际实现需要根据具体需求
        return processor
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        status = {
            "base_service_type": type(self._base_service).__name__,
            "has_config_provider": self._config_provider is not None,
            "has_cost_calculator": self._cost_calculator is not None,
            "supported_models": self.get_supported_models()
        }
        
        if self._config_provider:
            status["config_provider_type"] = type(self._config_provider).__name__
            # 如果配置提供者有缓存统计，添加到状态中
            try:
                if hasattr(self._config_provider, '_config_cache'):
                    config_cache = getattr(self._config_provider, '_config_cache', None)
                    if config_cache and hasattr(config_cache, '_manager'):
                        # 使用core/common/cache的统计接口
                        import asyncio
                        try:
                            cache_stats = asyncio.run(config_cache._manager.get_stats(config_cache._cache_name))
                            status["config_cache_stats"] = cache_stats
                        except RuntimeError:
                            # 如果无法运行异步，提供基本信息
                            status["config_cache_info"] = {
                                "cache_type": type(config_cache).__name__,
                                "cache_name": getattr(config_cache, '_cache_name', 'unknown')
                            }
            except Exception as e:
                logger.debug(f"无法获取配置缓存统计: {e}")
        
        if self._cost_calculator:
            status["cost_calculator_type"] = type(self._cost_calculator).__name__
        
        return status
    
    def get_enhanced_token_config(self, model_type: str, model_name: str) -> Optional[TokenCalculationConfig]:
        """
        获取增强的Token配置（包含缓存统计）
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Optional[TokenCalculationConfig]: Token计算配置
        """
        if not self._config_provider:
            logger.warning("未设置配置提供者，无法获取Token配置")
            return None
        
        return self._config_provider.get_token_config(model_type, model_name)
    
    def calculate_enhanced_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_type: str,
        model_name: str
    ) -> Dict[str, Any]:
        """
        计算增强的成本信息（包含配置详情）
        
        Args:
            input_tokens: 输入token数量
            output_tokens: 输出token数量
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 增强的成本信息
        """
        result = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model_type": model_type,
            "model_name": model_name,
            "cost_calculated": False,
            "cost_info": None,
            "config_info": None
        }
        
        # 获取配置信息
        if self._config_provider:
            # 检查是否有成本计算器来获取定价信息
            if self._cost_calculator and hasattr(self._cost_calculator, 'get_model_pricing_info'):
                config_info = self._cost_calculator.get_model_pricing_info(model_type, model_name)
                result["config_info"] = config_info
            else:
                # 获取基础配置信息
                token_config = self._config_provider.get_token_config(model_type, model_name)
                if token_config:
                    result["config_info"] = {
                        "model_type": model_type,
                        "model_name": model_name,
                        "input_token_cost": token_config.cost_per_input_token,
                        "output_token_cost": token_config.cost_per_output_token,
                        "tokenizer_type": token_config.tokenizer_type,
                        "custom_tokenizer": token_config.custom_tokenizer,
                        "fallback_enabled": token_config.fallback_enabled,
                        "cache_enabled": token_config.cache_enabled
                    }
        
        # 计算成本
        if self._cost_calculator:
            cost_info = self._cost_calculator.calculate_cost(input_tokens, output_tokens, model_type, model_name)
            result["cost_info"] = cost_info
            result["cost_calculated"] = cost_info is not None
        
        return result
    
    @property
    def base_service(self) -> TokenCalculationService:
        """获取基础服务"""
        return self._base_service
    
    @property
    def config_provider(self) -> Optional[ITokenConfigProvider]:
        """获取配置提供者"""
        return self._config_provider
    
    @property
    def cost_calculator(self) -> Optional[ITokenCostCalculator]:
        """获取成本计算器"""
        return self._cost_calculator