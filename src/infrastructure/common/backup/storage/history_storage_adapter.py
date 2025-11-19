"""History存储适配器"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult
from src.domain.history.llm_models import (
    LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord
)
from .base_storage import BaseStorage
from ..cache.cache_manager import CacheManager


class HistoryStorageAdapter(IHistoryManager):
    """History存储适配器，将IHistoryManager适配到BaseStorage"""
    
    def __init__(self, base_storage: BaseStorage, cache_manager: Optional[CacheManager] = None):
        """初始化适配器
        
        Args:
            base_storage: 基础存储实例
            cache_manager: 缓存管理器（可选）
        """
        self.base_storage = base_storage
        self.cache_manager = cache_manager
    
    async def record_message(self, record: MessageRecord) -> None:
        """记录消息"""
        # 将记录转换为存储格式
        data = {
            "id": record.record_id,
            "type": "message",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "message_type": record.message_type.value,
            "content": record.content,
            "metadata": record.metadata
        }
        
        # 异步保存
        await self.base_storage.save_with_metadata(data)
    
    async def record_tool_call(self, record: ToolCallRecord) -> None:
        """记录工具调用"""
        data = {
            "id": record.record_id,
            "type": "tool_call",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "tool_name": record.tool_name,
            "tool_input": record.tool_input,
            "tool_output": record.tool_output,
            "metadata": record.metadata
        }
        
        await self.base_storage.save_with_metadata(data)
    
    async def query_history(self, query: HistoryQuery) -> HistoryResult:
        """查询历史记录"""
        # 获取所有记录
        all_records = await self.base_storage.list({
            "session_id": query.session_id
        })
        
        # 过滤和转换记录
        filtered_records = []
        for record in all_records:
            # 应用时间范围过滤
            if query.start_time and record.get("timestamp"):
                record_time = self.base_storage.temporal.parse_timestamp(
                    record["timestamp"], "iso"
                )
                if record_time < query.start_time:
                    continue
            
            if query.end_time and record.get("timestamp"):
                record_time = self.base_storage.temporal.parse_timestamp(
                    record["timestamp"], "iso"
                )
                if record_time > query.end_time:
                    continue
            
            # 应用记录类型过滤
            if query.record_types and record.get("type") not in query.record_types:
                continue
            
            filtered_records.append(record)
        
        # 应用分页
        total = len(filtered_records)
        if query.offset:
            filtered_records = filtered_records[query.offset:]
        if query.limit:
            filtered_records = filtered_records[:query.limit]
        
        # 转换为历史记录对象
        return HistoryResult(records=filtered_records, total=total)
    
    async def record_llm_request(self, record: LLMRequestRecord) -> None:
        """记录LLM请求"""
        data = {
            "id": record.record_id,
            "type": "llm_request",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "model": record.model,
            "provider": record.provider,
            "messages": record.messages,
            "parameters": record.parameters,
            "estimated_tokens": record.estimated_tokens,
            "metadata": record.metadata
        }
        
        await self.base_storage.save_with_metadata(data)
    
    async def record_llm_response(self, record: LLMResponseRecord) -> None:
        """记录LLM响应"""
        data = {
            "id": record.record_id,
            "type": "llm_response",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "request_id": record.request_id,
            "content": record.content,
            "finish_reason": record.finish_reason,
            "token_usage": record.token_usage,
            "response_time": record.response_time,
            "model": record.model,
            "metadata": record.metadata
        }
        
        await self.base_storage.save_with_metadata(data)
    
    async def record_token_usage(self, record: TokenUsageRecord) -> None:
        """记录Token使用"""
        data = {
            "id": record.record_id,
            "type": "token_usage",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "model": record.model,
            "provider": record.provider,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "total_tokens": record.total_tokens,
            "source": record.source,
            "confidence": record.confidence,
            "metadata": record.metadata
        }
        
        await self.base_storage.save_with_metadata(data)
    
    async def record_cost(self, record: CostRecord) -> None:
        """记录成本"""
        data = {
            "id": record.record_id,
            "type": "cost",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "model": record.model,
            "provider": record.provider,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "total_tokens": record.total_tokens,
            "prompt_cost": record.prompt_cost,
            "completion_cost": record.completion_cost,
            "total_cost": record.total_cost,
            "currency": record.currency,
            "metadata": record.metadata
        }
        
        await self.base_storage.save_with_metadata(data)
    
    async def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取Token使用统计"""
        # 查询Token使用记录
        all_records = await self.base_storage.list({
            "session_id": session_id,
            "type": "token_usage"
        })
        
        total_tokens = sum(r.get("total_tokens", 0) for r in all_records)
        prompt_tokens = sum(r.get("prompt_tokens", 0) for r in all_records)
        completion_tokens = sum(r.get("completion_tokens", 0) for r in all_records)
        
        return {
            "session_id": session_id,
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "record_count": len(all_records),
            "avg_tokens_per_record": total_tokens / len(all_records) if all_records else 0
        }
    
    async def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        # 查询成本记录
        all_records = await self.base_storage.list({
            "session_id": session_id,
            "type": "cost"
        })
        
        total_cost = sum(r.get("total_cost", 0.0) for r in all_records)
        prompt_cost = sum(r.get("prompt_cost", 0.0) for r in all_records)
        completion_cost = sum(r.get("completion_cost", 0.0) for r in all_records)
        
        # 获取使用的模型
        models_used = list(set(r.get("model", "") for r in all_records))
        
        return {
            "session_id": session_id,
            "total_cost": total_cost,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "currency": all_records[0].get("currency", "USD") if all_records else "USD",
            "record_count": len(all_records),
            "models_used": models_used
        }
    
    async def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM调用统计"""
        # 查询LLM相关记录
        request_records = await self.base_storage.list({
            "session_id": session_id,
            "type": "llm_request"
        })
        
        response_records = await self.base_storage.list({
            "session_id": session_id,
            "type": "llm_response"
        })
        
        # 获取使用的模型
        models_used = list(set(r.get("model", "") for r in request_records))
        
        return {
            "session_id": session_id,
            "llm_requests": len(request_records),
            "llm_responses": len(response_records),
            "models_used": models_used,
            "request_record_count": len(request_records),
            "response_record_count": len(response_records)
        }