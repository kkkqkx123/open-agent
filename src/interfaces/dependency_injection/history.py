"""History依赖注入空实现

提供History服务的空实现，避免循环依赖。
"""

from typing import Optional, Any, TYPE_CHECKING
from datetime import datetime

from src.interfaces.history import IHistoryManager, ICostCalculator, DeleteResult
from src.core.history.interfaces import ITokenTracker
from src.interfaces.repository.history import IHistoryRepository

if TYPE_CHECKING:
    from src.core.history.entities import (
        MessageRecord,
        ToolCallRecord,
        HistoryQuery,
        HistoryResult,
        LLMRequestRecord,
        LLMResponseRecord,
        TokenUsageRecord,
        CostRecord,
        RecordType,
        TokenSource,
        BaseHistoryRecord,
        WorkflowTokenStatistics
    )


class _StubHistoryManager(IHistoryManager):
    """临时 HistoryManager 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        self._storage = None
    
    async def record_message(self, record: 'MessageRecord') -> None:
        """记录消息"""
        pass
    
    async def record_tool_call(self, record: 'ToolCallRecord') -> None:
        """记录工具调用"""
        pass
    
    async def query_history(self, query: 'HistoryQuery') -> 'HistoryResult':
        """查询历史"""
        from src.core.history.entities import HistoryResult
        return HistoryResult(records=[], total_count=0)
    
    async def record_llm_request(self, record: 'LLMRequestRecord') -> None:
        """记录LLM请求"""
        pass
    
    async def record_llm_response(self, record: 'LLMResponseRecord') -> None:
        """记录LLM响应"""
        pass
    
    async def record_token_usage(self, record: 'TokenUsageRecord') -> None:
        """记录Token使用"""
        pass
    
    async def record_cost(self, record: 'CostRecord') -> None:
        """记录成本"""
        pass
    
    async def get_token_statistics(self, session_id: str) -> dict:
        """获取Token统计"""
        return {}
    
    async def get_cost_statistics(self, session_id: str) -> dict:
        """获取成本统计"""
        return {}
    
    async def get_llm_statistics(self, session_id: str) -> dict:
        """获取LLM统计"""
        return {}
    
    async def cleanup_old_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional['datetime'] = None,
        dry_run: bool = False
    ) -> dict:
        """清理旧记录"""
        return {}
    
    async def query_history_by_thread(
        self,
        thread_id: str,
        limit: int = 100,
        offset: int = 0,
        record_type: Optional['RecordType'] = None,
        start_time: Optional['datetime'] = None,
        end_time: Optional['datetime'] = None,
        model: Optional[str] = None
    ) -> 'HistoryResult':
        """按thread_id查询历史记录"""
        from src.core.history.entities import HistoryResult
        return HistoryResult(records=[], total_count=0)
    
    async def delete_history(
        self,
        query: 'HistoryQuery'
    ) -> DeleteResult:
        """删除历史记录"""
        return DeleteResult(deleted_count=0, success=False)


class _StubCostCalculator(ICostCalculator):
    """临时 CostCalculator 实现（用于极端情况）"""
    
    def calculate_cost(self, token_usage: 'TokenUsageRecord') -> 'CostRecord':
        """计算成本"""
        from src.core.history.entities import CostRecord
        import uuid
        return CostRecord(
            record_id=str(uuid.uuid4()),
            session_id=token_usage.session_id if hasattr(token_usage, 'session_id') else "unknown",
            model=token_usage.model if hasattr(token_usage, 'model') else "unknown",
            prompt_cost=0.0,
            completion_cost=0.0,
            total_cost=0.0,
            currency="USD"
        )
    
    def calculate_cost_from_tokens(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        currency: str = "USD"
    ) -> 'CostRecord':
        """根据Token数量计算成本"""
        from src.core.history.entities import CostRecord
        import uuid
        return CostRecord(
            record_id=str(uuid.uuid4()),
            session_id="unknown",
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_cost=0.0,
            completion_cost=0.0,
            total_cost=0.0,
            currency=currency
        )
    
    def get_model_pricing(self, model_name: str) -> dict:
        """获取模型定价"""
        return {}
    
    def update_pricing(
        self,
        model_name: str,
        input_price: float,
        output_price: float,
        currency: str = "USD",
        provider: str = "custom"
    ) -> None:
        """更新模型定价"""
        pass
    
    def list_supported_models(self) -> list:
        """获取支持的模型列表"""
        return []
    
    def get_provider_models(self, provider: str) -> list:
        """获取指定提供商的模型列表"""
        return []


class _StubTokenTracker(ITokenTracker):
    """临时 TokenTracker 实现（用于极端情况）"""
    
    async def track_workflow_token_usage(
        self,
        workflow_id: str,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        source: Optional['TokenSource'] = None,
        confidence: float = 1.0,
        metadata: Optional[dict] = None
    ) -> None:
        """追踪工作流Token使用"""
        if source is None:
            from src.core.history.entities import TokenSource
            source = TokenSource.LOCAL
        pass
    
    async def track_llm_request(
        self,
        workflow_id: str,
        session_id: str,
        model: str,
        provider: str,
        messages: list,
        parameters: dict,
        estimated_tokens: int,
        metadata: Optional[dict] = None
    ) -> str:
        """追踪LLM请求"""
        return ""
    
    async def track_llm_response(
        self,
        request_id: str,
        content: str,
        finish_reason: str,
        token_usage: dict,
        response_time: float,
        metadata: Optional[dict] = None
    ) -> None:
        """追踪LLM响应"""
        pass
    
    async def get_workflow_statistics(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional['datetime'] = None,
        end_time: Optional['datetime'] = None
    ) -> 'WorkflowTokenStatistics':
        """获取工作流统计"""
        from src.core.history.entities import WorkflowTokenStatistics
        return WorkflowTokenStatistics(
            workflow_id=workflow_id,
            model=model or "unknown",
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_tokens=0,
            total_cost=0.0,
            request_count=0,
            period_start=start_time,
            period_end=end_time
        )
    
    async def get_multi_model_statistics(
        self,
        workflow_id: str,
        start_time: Optional['datetime'] = None,
        end_time: Optional['datetime'] = None
    ) -> dict:
        """获取工作流多模型统计"""
        return {}
    
    async def get_cross_workflow_statistics(
        self,
        workflow_ids: list,
        model: Optional[str] = None,
        start_time: Optional['datetime'] = None,
        end_time: Optional['datetime'] = None
    ) -> dict:
        """获取跨工作流统计"""
        return {}


class _StubHistoryRepository(IHistoryRepository):
    """临时 HistoryRepository 实现（用于极端情况）"""
    
    async def save_record(self, record: 'BaseHistoryRecord') -> bool:
        """保存历史记录"""
        return False
    
    async def save_records(self, records: list) -> list:
        """批量保存历史记录"""
        return [False] * len(records)
    
    async def get_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        record_type: Optional['RecordType'] = None,
        model: Optional[str] = None,
        start_time: Optional['datetime'] = None,
        end_time: Optional['datetime'] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """获取历史记录"""
        return []
    
    async def get_record_by_id(self, record_id: str) -> Optional['BaseHistoryRecord']:
        """根据ID获取记录"""
        return None
    
    async def delete_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional['datetime'] = None
    ) -> int:
        """删除历史记录"""
        return 0
    
    async def delete_records_by_query(self, query: 'HistoryQuery') -> int:
        """根据查询条件删除历史记录"""
        return 0
    
    async def get_workflow_token_stats(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional['datetime'] = None,
        end_time: Optional['datetime'] = None
    ) -> list:
        """获取工作流Token统计"""
        return []
    
    async def update_workflow_token_stats(
        self,
        stats: 'WorkflowTokenStatistics'
    ) -> bool:
        """更新工作流Token统计"""
        return False
    
    async def get_storage_statistics(self) -> dict:
        """获取存储统计信息"""
        return {}
    
    async def save_history(self, entry: dict) -> str:
        """保存历史记录"""
        return ""
    
    async def get_history(self, thread_id: str, limit: int = 100) -> list:
        """获取历史记录"""
        return []
    
    async def get_history_by_timerange(
        self,
        thread_id: str,
        start_time: 'datetime',
        end_time: 'datetime',
        limit: int = 100
    ) -> list:
        """按时间范围获取历史记录"""
        return []
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录"""
        return False
    
    async def clear_thread_history(self, thread_id: str) -> bool:
        """清空线程的历史记录"""
        return False
    
    async def get_history_statistics(self) -> dict:
        """获取历史记录统计信息"""
        return {}
    
    async def get_history_by_id(self, history_id: str) -> Optional[dict]:
        """根据ID获取历史记录"""
        return None


# 全局实例
_global_history_manager: Optional[IHistoryManager] = None
_global_cost_calculator: Optional[ICostCalculator] = None
_global_token_tracker: Optional[ITokenTracker] = None
_global_history_repository: Optional[IHistoryRepository] = None


def get_history_manager() -> IHistoryManager:
    """获取History管理器实例"""
    global _global_history_manager
    if _global_history_manager is not None:
        return _global_history_manager
    return _StubHistoryManager()


def get_cost_calculator() -> ICostCalculator:
    """获取成本计算器实例"""
    global _global_cost_calculator
    if _global_cost_calculator is not None:
        return _global_cost_calculator
    return _StubCostCalculator()


def get_token_tracker() -> ITokenTracker:
    """获取Token追踪器实例"""
    global _global_token_tracker
    if _global_token_tracker is not None:
        return _global_token_tracker
    return _StubTokenTracker()


def get_history_repository() -> IHistoryRepository:
    """获取History仓储实例"""
    global _global_history_repository
    if _global_history_repository is not None:
        return _global_history_repository
    return _StubHistoryRepository()


def set_history_manager_instance(history_manager: IHistoryManager) -> None:
    """设置全局History管理器实例"""
    global _global_history_manager
    _global_history_manager = history_manager


def set_cost_calculator_instance(cost_calculator: ICostCalculator) -> None:
    """设置全局成本计算器实例"""
    global _global_cost_calculator
    _global_cost_calculator = cost_calculator


def set_token_tracker_instance(token_tracker: ITokenTracker) -> None:
    """设置全局Token追踪器实例"""
    global _global_token_tracker
    _global_token_tracker = token_tracker


def set_history_repository_instance(history_repository: IHistoryRepository) -> None:
    """设置全局History仓储实例"""
    global _global_history_repository
    _global_history_repository = history_repository


def clear_history_manager_instance() -> None:
    """清除全局History管理器实例"""
    global _global_history_manager
    _global_history_manager = None


def clear_cost_calculator_instance() -> None:
    """清除全局成本计算器实例"""
    global _global_cost_calculator
    _global_cost_calculator = None


def clear_token_tracker_instance() -> None:
    """清除全局Token追踪器实例"""
    global _global_token_tracker
    _global_token_tracker = None


def clear_history_repository_instance() -> None:
    """清除全局History仓储实例"""
    global _global_history_repository
    _global_history_repository = None


def get_history_manager_status() -> dict:
    """获取History管理器状态"""
    return {
        "has_instance": _global_history_manager is not None,
        "type": type(_global_history_manager).__name__ if _global_history_manager else None
    }


def get_cost_calculator_status() -> dict:
    """获取成本计算器状态"""
    return {
        "has_instance": _global_cost_calculator is not None,
        "type": type(_global_cost_calculator).__name__ if _global_cost_calculator else None
    }


def get_token_tracker_status() -> dict:
    """获取Token追踪器状态"""
    return {
        "has_instance": _global_token_tracker is not None,
        "type": type(_global_token_tracker).__name__ if _global_token_tracker else None
    }


def get_history_repository_status() -> dict:
    """获取History仓储状态"""
    return {
        "has_instance": _global_history_repository is not None,
        "type": type(_global_history_repository).__name__ if _global_history_repository else None
    }


__all__ = [
    "get_history_manager",
    "get_cost_calculator",
    "get_token_tracker",
    "get_history_repository",
    "set_history_manager_instance",
    "set_cost_calculator_instance",
    "set_token_tracker_instance",
    "set_history_repository_instance",
    "clear_history_manager_instance",
    "clear_cost_calculator_instance",
    "clear_token_tracker_instance",
    "clear_history_repository_instance",
    "get_history_manager_status",
    "get_cost_calculator_status",
    "get_token_tracker_status",
    "get_history_repository_status",
]