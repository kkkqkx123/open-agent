"""成本计算服务实现

提供LLM调用的成本计算功能，支持多模型定价。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from src.interfaces.history import ICostCalculator
from src.interfaces.history.exceptions import CostCalculationError
from src.interfaces.container.exceptions import ValidationError

from src.core.history.entities import TokenUsageRecord, CostRecord


logger = get_logger(__name__)


@dataclass
class ModelPricing:
    """模型定价配置"""
    input_price: float  # 输入token价格（每1K tokens）
    output_price: float  # 输出token价格（每1K tokens）
    currency: str = "USD"
    provider: str = "openai"
    model_name: str = ""
    updated_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.input_price < 0 or self.output_price < 0:
            raise ValidationError("价格不能为负数")
        if not self.currency:
            raise ValidationError("货币单位不能为空")
        if not self.provider:
            raise ValidationError("提供商不能为空")
        
        if self.updated_at is None:
            self.updated_at = datetime.now()


class CostCalculator(ICostCalculator):
    """成本计算器实现
    
    支持多种LLM提供商和模型的成本计算。
    """
    
    def __init__(self, pricing_config: Optional[Dict[str, Any]] = None):
        """
        初始化成本计算器
        
        Args:
            pricing_config: 定价配置字典
        """
        self.pricing_config = pricing_config or {}
        self._model_pricing: Dict[str, ModelPricing] = {}
        self._logger = get_logger(self.__class__.__name__)
        
        # 加载默认定价配置
        self._load_default_pricing()
        
        # 加载用户自定义定价配置
        if pricing_config:
            self._load_custom_pricing(pricing_config)
    
    def _load_default_pricing(self) -> None:
        """加载默认定价配置"""
        try:
            # OpenAI模型定价
            openai_pricing = {
                "gpt-4": ModelPricing(0.03, 0.06, "USD", "openai", "gpt-4"),
                "gpt-4-32k": ModelPricing(0.06, 0.12, "USD", "openai", "gpt-4-32k"),
                "gpt-4-turbo": ModelPricing(0.01, 0.03, "USD", "openai", "gpt-4-turbo"),
                "gpt-4-turbo-preview": ModelPricing(0.01, 0.03, "USD", "openai", "gpt-4-turbo-preview"),
                "gpt-3.5-turbo": ModelPricing(0.0015, 0.002, "USD", "openai", "gpt-3.5-turbo"),
                "gpt-3.5-turbo-16k": ModelPricing(0.003, 0.004, "USD", "openai", "gpt-3.5-turbo-16k"),
                "gpt-3.5-turbo-instruct": ModelPricing(0.0015, 0.002, "USD", "openai", "gpt-3.5-turbo-instruct"),
                "text-davinci-003": ModelPricing(0.02, 0.02, "USD", "openai", "text-davinci-003"),
                "text-curie-001": ModelPricing(0.002, 0.002, "USD", "openai", "text-curie-001"),
            }
            
            # Gemini模型定价
            gemini_pricing = {
                "gemini-pro": ModelPricing(0.0005, 0.0015, "USD", "google", "gemini-pro"),
                "gemini-pro-vision": ModelPricing(0.0025, 0.0075, "USD", "google", "gemini-pro-vision"),
                "gemini-1.5-pro": ModelPricing(0.0025, 0.0075, "USD", "google", "gemini-1.5-pro"),
                "gemini-1.5-flash": ModelPricing(0.00015, 0.0006, "USD", "google", "gemini-1.5-flash"),
            }
            
            # Anthropic模型定价
            anthropic_pricing = {
                "claude-3-opus-20240229": ModelPricing(0.015, 0.075, "USD", "anthropic", "claude-3-opus-20240229"),
                "claude-3-sonnet-20240229": ModelPricing(0.003, 0.015, "USD", "anthropic", "claude-3-sonnet-20240229"),
                "claude-3-haiku-20240307": ModelPricing(0.00025, 0.00125, "USD", "anthropic", "claude-3-haiku-20240307"),
                "claude-2.1": ModelPricing(0.008, 0.024, "USD", "anthropic", "claude-2.1"),
                "claude-2.0": ModelPricing(0.008, 0.024, "USD", "anthropic", "claude-2.0"),
                "claude-instant-1.2": ModelPricing(0.0008, 0.0024, "USD", "anthropic", "claude-instant-1.2"),
            }
            
            # 合并所有定价
            self._model_pricing.update(openai_pricing)
            self._model_pricing.update(gemini_pricing)
            self._model_pricing.update(anthropic_pricing)
            
            self._logger.info(f"加载了 {len(self._model_pricing)} 个模型的默认定价")
            
        except Exception as e:
            self._logger.error(f"加载默认定价配置失败: {e}")
            raise CostCalculationError(f"加载默认定价配置失败: {e}")
    
    def _load_custom_pricing(self, pricing_config: Dict[str, Any]) -> None:
        """加载用户自定义定价配置"""
        try:
            for model_name, config in pricing_config.items():
                if isinstance(config, dict):
                    input_price = config.get("input_price", 0)
                    output_price = config.get("output_price", 0)
                    currency = config.get("currency", "USD")
                    provider = config.get("provider", "custom")
                    
                    self._model_pricing[model_name] = ModelPricing(
                        input_price=input_price,
                        output_price=output_price,
                        currency=currency,
                        provider=provider,
                        model_name=model_name
                    )
            
            self._logger.info(f"加载了 {len(pricing_config)} 个自定义定价配置")
            
        except Exception as e:
            self._logger.error(f"加载自定义定价配置失败: {e}")
            raise CostCalculationError(f"加载自定义定价配置失败: {e}")
    
    def calculate_cost(self, token_usage: TokenUsageRecord) -> CostRecord:
        """
        计算Token使用的成本
        
        Args:
            token_usage: Token使用记录
            
        Returns:
            CostRecord: 成本记录
            
        Raises:
            CostCalculationError: 成本计算失败
        """
        try:
            model_name = token_usage.model
            pricing = self._model_pricing.get(model_name)
            
            if not pricing:
                self._logger.warning(f"未找到模型 {model_name} 的定价信息，使用默认定价")
                # 使用默认定价
                pricing = ModelPricing(0.001, 0.002, "USD", "unknown", model_name)
            
            # 计算成本（价格是每1K tokens）
            prompt_cost = (token_usage.prompt_tokens / 1000) * pricing.input_price
            completion_cost = (token_usage.completion_tokens / 1000) * pricing.output_price
            total_cost = prompt_cost + completion_cost
            
            cost_record = CostRecord(
                record_id=self._generate_id(),
                session_id=token_usage.session_id,
                workflow_id=token_usage.workflow_id,
                timestamp=datetime.now(),
                model=model_name,
                provider=pricing.provider,
                prompt_tokens=token_usage.prompt_tokens,
                completion_tokens=token_usage.completion_tokens,
                total_tokens=token_usage.total_tokens,
                prompt_cost=prompt_cost,
                completion_cost=completion_cost,
                total_cost=total_cost,
                currency=pricing.currency,
                metadata={
                    "pricing_source": "calculator",
                    "confidence": token_usage.confidence,
                    "pricing_updated_at": pricing.updated_at.isoformat() if pricing.updated_at else None
                }
            )
            
            self._logger.debug(f"计算成本: 模型={model_name}, "
                             f"Token={token_usage.total_tokens}, "
                             f"成本={total_cost:.6f} {pricing.currency}")
            
            return cost_record
            
        except Exception as e:
            self._logger.error(f"计算成本失败: {e}")
            model_name = token_usage.model  # 确保model_name在异常处理中被定义
            raise CostCalculationError(f"计算成本失败: {e}", model=model_name)
    
    def calculate_cost_from_tokens(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        currency: str = "USD"
    ) -> CostRecord:
        """
        根据Token数量计算成本
        
        Args:
            model: 模型名称
            provider: 提供商名称
            prompt_tokens: Prompt token数量
            completion_tokens: Completion token数量
            currency: 货币单位
            
        Returns:
            CostRecord: 成本记录
        """
        try:
            pricing = self._model_pricing.get(model)
            
            if not pricing:
                # 使用默认定价
                pricing = ModelPricing(0.001, 0.002, currency, provider, model)
            
            # 计算成本
            prompt_cost = (prompt_tokens / 1000) * pricing.input_price
            completion_cost = (completion_tokens / 1000) * pricing.output_price
            total_cost = prompt_cost + completion_cost
            total_tokens = prompt_tokens + completion_tokens
            
            cost_record = CostRecord(
                record_id=self._generate_id(),
                session_id="manual",
                workflow_id=None,
                timestamp=datetime.now(),
                model=model,
                provider=provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                prompt_cost=prompt_cost,
                completion_cost=completion_cost,
                total_cost=total_cost,
                currency=pricing.currency,
                metadata={
                    "pricing_source": "manual_calculation",
                    "pricing_updated_at": pricing.updated_at.isoformat() if pricing.updated_at else None
                }
            )
            
            return cost_record
            
        except Exception as e:
            self._logger.error(f"手动计算成本失败: {e}")
            raise CostCalculationError(f"手动计算成本失败: {e}", model=model)
    
    def get_model_pricing(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型定价信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 定价信息
        """
        pricing = self._model_pricing.get(model_name)
        
        if not pricing:
            return {}
        
        return {
            "model_name": pricing.model_name,
            "input_price": pricing.input_price,
            "output_price": pricing.output_price,
            "currency": pricing.currency,
            "provider": pricing.provider,
            "updated_at": pricing.updated_at.isoformat() if pricing.updated_at else None
        }
    
    def update_pricing(
        self,
        model_name: str,
        input_price: float,
        output_price: float,
        currency: str = "USD",
        provider: str = "custom"
    ) -> None:
        """
        更新模型定价
        
        Args:
            model_name: 模型名称
            input_price: 输入价格（每1K tokens）
            output_price: 输出价格（每1K tokens）
            currency: 货币单位
            provider: 提供商名称
        """
        try:
            if input_price < 0 or output_price < 0:
                raise ValidationError("价格不能为负数")
            
            existing = self._model_pricing.get(model_name)
            if existing:
                existing.input_price = input_price
                existing.output_price = output_price
                existing.currency = currency
                existing.provider = provider
                existing.updated_at = datetime.now()
            else:
                self._model_pricing[model_name] = ModelPricing(
                    input_price=input_price,
                    output_price=output_price,
                    currency=currency,
                    provider=provider,
                    model_name=model_name
                )
            
            self._logger.info(f"更新模型定价: {model_name}, "
                            f"输入价格={input_price}, 输出价格={output_price}")
            
        except Exception as e:
            self._logger.error(f"更新模型定价失败: {e}")
            raise CostCalculationError(f"更新模型定价失败: {e}", model=model_name)
    
    def list_supported_models(self) -> List[str]:
        """
        获取支持的模型列表
        
        Returns:
            List[str]: 模型名称列表
        """
        return list(self._model_pricing.keys())
    
    def get_provider_models(self, provider: str) -> List[str]:
        """
        获取指定提供商的模型列表
        
        Args:
            provider: 提供商名称
            
        Returns:
            List[str]: 模型名称列表
        """
        return [
            model_name for model_name, pricing in self._model_pricing.items()
            if pricing.provider.lower() == provider.lower()
        ]
    
    def get_all_pricing(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有模型的定价信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 模型名称到定价信息的映射
        """
        return {
            model_name: self.get_model_pricing(model_name)
            for model_name in self._model_pricing.keys()
        }
    
    def estimate_cost(
        self,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int = 0
    ) -> Dict[str, Any]:
        """
        估算成本
        
        Args:
            model: 模型名称
            estimated_input_tokens: 估算的输入token数量
            estimated_output_tokens: 估算的输出token数量
            
        Returns:
            Dict[str, Any]: 估算结果
        """
        try:
            pricing = self._model_pricing.get(model)
            
            if not pricing:
                return {
                    "model": model,
                    "error": "未找到模型定价信息",
                    "estimated_cost": 0.0
                }
            
            estimated_prompt_cost = (estimated_input_tokens / 1000) * pricing.input_price
            estimated_completion_cost = (estimated_output_tokens / 1000) * pricing.output_price
            estimated_total_cost = estimated_prompt_cost + estimated_completion_cost
            
            return {
                "model": model,
                "provider": pricing.provider,
                "currency": pricing.currency,
                "estimated_input_tokens": estimated_input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_prompt_cost": estimated_prompt_cost,
                "estimated_completion_cost": estimated_completion_cost,
                "estimated_total_cost": estimated_total_cost,
                "pricing_updated_at": pricing.updated_at.isoformat() if pricing.updated_at else None
            }
            
        except Exception as e:
            self._logger.error(f"估算成本失败: {e}")
            return {
                "model": model,
                "error": str(e),
                "estimated_cost": 0.0
            }
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())