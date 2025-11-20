"""历史管理接口定义"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult
    from ..domain.history.llm_models import (
        LLMRequestRecord,
        LLMResponseRecord,
        TokenUsageRecord,
        CostRecord
    )


class IHistoryManager(ABC):
    """历史管理器接口"""
    
    @abstractmethod
    async def record_message(self, record: 'MessageRecord') -> None:
        """记录消息"""
        pass
    
    @abstractmethod
    async def record_tool_call(self, record: 'ToolCallRecord') -> None:
        """记录工具调用"""
        pass
    
    @abstractmethod
    async def query_history(self, query: 'HistoryQuery') -> 'HistoryResult':
        """查询历史"""
        pass
    
    # 新增LLM相关方法
    @abstractmethod
    async def record_llm_request(self, record: 'LLMRequestRecord') -> None:
        """记录LLM请求"""
        pass
    
    @abstractmethod
    async def record_llm_response(self, record: 'LLMResponseRecord') -> None:
        """记录LLM响应"""
        pass
    
    @abstractmethod
    async def record_token_usage(self, record: 'TokenUsageRecord') -> None:
        """记录Token使用"""
        pass
    
    @abstractmethod
    async def record_cost(self, record: 'CostRecord') -> None:
        """记录成本"""
        pass
    
    # 新增查询和统计方法
    @abstractmethod
    async def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取Token统计"""
        pass
    
    @abstractmethod
    async def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        pass
    
    @abstractmethod
    async def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM统计"""
        pass


class ICostCalculator(ABC):
    """成本计算器接口"""
    
    @abstractmethod
    def calculate_cost(self, token_usage: 'TokenUsageRecord') -> 'CostRecord':
        """计算成本"""
        pass
    
    @abstractmethod
    def get_model_pricing(self, model_name: str) -> Dict[str, float]:
        """获取模型定价"""
        pass
    
    @abstractmethod
    def update_pricing(self, model_name: str, input_price: float, output_price: float) -> None:
        """更新定价"""
        pass