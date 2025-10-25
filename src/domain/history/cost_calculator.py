from typing import Dict, Any
from .llm_models import TokenUsageRecord, CostRecord
from .cost_interfaces import ICostCalculator


def generate_id() -> str:
    """生成唯一ID的辅助函数"""
    import uuid
    return str(uuid.uuid4())


class CostCalculator(ICostCalculator):
    """成本计算器"""
    
    def __init__(self, pricing_config: Dict[str, Any]):
        """
        初始化成本计算器
        
        Args:
            pricing_config: 定价配置，格式为 { "provider:model": {"prompt_price_per_1k": float, "completion_price_per_1k": float} }
        """
        self.pricing = pricing_config  # 模型定价配置
    
    def calculate_cost(self, token_usage: TokenUsageRecord) -> CostRecord:
        """
        根据Token使用记录计算成本
        
        Args:
            token_usage: Token使用记录
            
        Returns:
            CostRecord: 成本记录
        """
        model_key = f"{token_usage.provider}:{token_usage.model}"
        
        # 默认定价（如果配置中没有指定）
        default_prompt_price_per_1k = 0.01  # $0.01/1K tokens
        default_completion_price_per_1k = 0.03  # $0.03/1K tokens
        
        if model_key not in self.pricing:
            # 使用默认定价或估算
            prompt_cost = token_usage.prompt_tokens * default_prompt_price_per_1k / 1000
            completion_cost = token_usage.completion_tokens * default_completion_price_per_1k / 1000
        else:
            pricing = self.pricing[model_key]
            prompt_price_per_1k = pricing.get("prompt_price_per_1k", default_prompt_price_per_1k)
            completion_price_per_1k = pricing.get("completion_price_per_1k", default_completion_price_per_1k)
            
            prompt_cost = token_usage.prompt_tokens * prompt_price_per_1k / 1000
            completion_cost = token_usage.completion_tokens * completion_price_per_1k / 1000
        
        total_cost = prompt_cost + completion_cost
        
        return CostRecord(
            record_id=generate_id(),
            session_id=token_usage.session_id,
            timestamp=token_usage.timestamp,  # 使用Token使用记录的时间戳
            model=token_usage.model,
            provider=token_usage.provider,
            prompt_tokens=token_usage.prompt_tokens,
            completion_tokens=token_usage.completion_tokens,
            total_tokens=token_usage.total_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            currency="USD"
        )