from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class IHistoryManager(ABC):
    @abstractmethod
    async def record_message(self, record: 'MessageRecord') -> None: pass
    
    @abstractmethod
    async def record_tool_call(self, record: 'ToolCallRecord') -> None: pass
    
    @abstractmethod
    async def query_history(self, query: 'HistoryQuery') -> 'HistoryResult': pass
    
    # 新增LLM相关方法
    @abstractmethod
    async def record_llm_request(self, record: 'LLMRequestRecord') -> None: pass
    
    @abstractmethod
    async def record_llm_response(self, record: 'LLMResponseRecord') -> None: pass
    
    @abstractmethod
    async def record_token_usage(self, record: 'TokenUsageRecord') -> None: pass
    
    @abstractmethod
    async def record_cost(self, record: 'CostRecord') -> None: pass
    
    # 新增查询和统计方法
    @abstractmethod
    async def get_token_statistics(self, session_id: str) -> Dict[str, Any]: pass
    
    @abstractmethod
    async def get_cost_statistics(self, session_id: str) -> Dict[str, Any]: pass
    
    @abstractmethod
    async def get_llm_statistics(self, session_id: str) -> Dict[str, Any]: pass