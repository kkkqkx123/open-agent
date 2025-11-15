"""历史记录仓储接口定义

定义历史记录仓储的核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .interfaces import IHistoryManager
from .models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult
from .llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord


class IHistoryRepository(ABC):
    """历史记录仓储接口
    
    负责历史记录数据的存储和检索。
    """
    
    @abstractmethod
    def record_message(self, record: MessageRecord) -> None:
        """记录消息"""
        pass
    
    @abstractmethod
    def record_tool_call(self, record: ToolCallRecord) -> None:
        """记录工具调用"""
        pass
    
    @abstractmethod
    def query_history(self, query: HistoryQuery) -> HistoryResult:
        """查询历史记录"""
        pass
    
    @abstractmethod
    def record_llm_request(self, record: LLMRequestRecord) -> None:
        """记录LLM请求"""
        pass
    
    @abstractmethod
    def record_llm_response(self, record: LLMResponseRecord) -> None:
        """记录LLM响应"""
        pass
    
    @abstractmethod
    def record_token_usage(self, record: TokenUsageRecord) -> None:
        """记录令牌使用情况"""
        pass
    
    @abstractmethod
    def record_cost(self, record: CostRecord) -> None:
        """记录成本"""
        pass
    
    @abstractmethod
    def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取令牌统计"""
        pass
    
    @abstractmethod
    def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        pass
    
    @abstractmethod
    def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM统计"""
        pass


class HistoryRepository(IHistoryRepository):
    """历史记录仓储实现
    
    使用IHistoryManager作为底层管理器。
    """
    
    def __init__(self, history_store: Optional[IHistoryManager] = None):
        """初始化历史记录仓储
        
        Args:
            history_store: 历史记录管理器实例
        """
        self.history_store = history_store
    
    def record_message(self, record: MessageRecord) -> None:
        """记录消息"""
        if self.history_store:
            self.history_store.record_message(record)
    
    def record_tool_call(self, record: ToolCallRecord) -> None:
        """记录工具调用"""
        if self.history_store:
            self.history_store.record_tool_call(record)
    
    def query_history(self, query: HistoryQuery) -> HistoryResult:
        """查询历史记录"""
        if self.history_store:
            return self.history_store.query_history(query)
        return HistoryResult(records=[])
    
    def record_llm_request(self, record: LLMRequestRecord) -> None:
        """记录LLM请求"""
        if self.history_store:
            self.history_store.record_llm_request(record)
    
    def record_llm_response(self, record: LLMResponseRecord) -> None:
        """记录LLM响应"""
        if self.history_store:
            self.history_store.record_llm_response(record)
    
    def record_token_usage(self, record: TokenUsageRecord) -> None:
        """记录令牌使用情况"""
        if self.history_store:
            self.history_store.record_token_usage(record)
    
    def record_cost(self, record: CostRecord) -> None:
        """记录成本"""
        if self.history_store:
            self.history_store.record_cost(record)
    
    def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取令牌统计"""
        if self.history_store:
            return self.history_store.get_token_statistics(session_id)
        return {}
    
    def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        if self.history_store:
            return self.history_store.get_cost_statistics(session_id)
        return {}
    
    def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM统计"""
        if self.history_store:
            return self.history_store.get_llm_statistics(session_id)
        return {}