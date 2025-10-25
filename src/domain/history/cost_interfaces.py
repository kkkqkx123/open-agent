from abc import ABC, abstractmethod
from typing import Dict, Any
from .llm_models import TokenUsageRecord, CostRecord


class ICostCalculator(ABC):
    @abstractmethod
    def calculate_cost(self, token_usage: TokenUsageRecord) -> CostRecord:
        """
        根据Token使用记录计算成本
        """
        pass