"""历史管理接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass

from .entities import (
    IBaseHistoryRecord,
    ILLMRequestRecord,
    ILLMResponseRecord,
    ITokenUsageRecord,
    ICostRecord,
    IMessageRecord,
    IToolCallRecord
)

if TYPE_CHECKING:
    from ...core.history.entities import (
        TokenUsageRecord,
        CostRecord,
        LLMRequestRecord,
        LLMResponseRecord,
        MessageRecord,
        ToolCallRecord,
        HistoryQuery,
        HistoryResult,
        RecordType
    )


@dataclass
class DeleteResult:
    """删除结果"""
    deleted_count: int
    success: bool
    error: Optional[str] = None


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
    
    @abstractmethod
    async def cleanup_old_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional[datetime] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """清理旧记录"""
        pass
    
    @abstractmethod
    async def query_history_by_thread(
        self,
        thread_id: str,
        limit: int = 100,
        offset: int = 0,
        record_type: Optional['RecordType'] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        model: Optional[str] = None
    ) -> 'HistoryResult':
        """按thread_id查询历史记录
        
        Args:
            thread_id: 线程ID
            limit: 返回记录数量限制
            offset: 偏移量
            record_type: 记录类型过滤
            start_time: 开始时间
            end_time: 结束时间
            model: 模型过滤
            
        Returns:
            历史查询结果
        """
        pass
    
    @abstractmethod
    async def delete_history(
        self,
        query: 'HistoryQuery'
    ) -> DeleteResult:
        """删除历史记录
        
        Args:
            query: 删除查询条件
            
        Returns:
            删除结果
        """
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


__all__ = [
    "IBaseHistoryRecord",
    "ILLMRequestRecord",
    "ILLMResponseRecord",
    "ITokenUsageRecord",
    "ICostRecord",
    "IMessageRecord",
    "IToolCallRecord",
    "IHistoryManager",
    "ICostCalculator",
    "DeleteResult",
]