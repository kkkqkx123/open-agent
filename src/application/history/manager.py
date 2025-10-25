from typing import Dict, Any
from datetime import datetime
import json

from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult, MessageType
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord
from src.infrastructure.history.storage.file_storage import FileHistoryStorage


class HistoryManager(IHistoryManager):
    def __init__(self, storage: FileHistoryStorage):
        self.storage = storage
    
    def record_message(self, record: MessageRecord) -> None:
        self.storage.store_record(record)
    
    def record_tool_call(self, record: ToolCallRecord) -> None:
        self.storage.store_record(record)
    
    def query_history(self, query: HistoryQuery) -> HistoryResult:
        """
        查询历史记录
        
        Args:
            query: 查询条件
            
        Returns:
            HistoryResult: 查询结果
        """
        # 获取所有记录（原始字典格式）
        raw_records = self.storage.get_all_records(query.session_id) if query.session_id else []
        
        # 将原始字典转换为适当的记录对象
        all_records = []
        for raw_record in raw_records:
            record_type = raw_record.get('record_type', 'message')
            record_obj = self._deserialize_record(raw_record, record_type)
            if record_obj:
                all_records.append(record_obj)
        
        # 应用时间范围过滤
        if query.start_time:
            all_records = [r for r in all_records if hasattr(r, 'timestamp') and r.timestamp >= query.start_time]
        if query.end_time:
            all_records = [r for r in all_records if hasattr(r, 'timestamp') and r.timestamp <= query.end_time]
        
        # 应用记录类型过滤
        if query.record_types:
            all_records = [r for r in all_records if hasattr(r, 'record_type') and r.record_type in query.record_types]
        
        # 应用分页
        total = len(all_records)
        if query.offset:
            all_records = all_records[query.offset:]
        if query.limit:
            all_records = all_records[:query.limit]
        
        return HistoryResult(records=all_records, total=total)
    
    def _deserialize_record(self, raw_record: Dict[str, Any], record_type: str):
        """
        将原始字典反序列化为记录对象
        
        Args:
            raw_record: 原始记录字典
            record_type: 记录类型
            
        Returns:
            适当的记录对象或None
        """
        try:
            # 处理时间戳
            if 'timestamp' in raw_record and isinstance(raw_record['timestamp'], str):
                raw_record['timestamp'] = datetime.fromisoformat(raw_record['timestamp'])
            
            if record_type == 'message':
                message_type_value = raw_record.get('message_type', 'user')
                # 将字符串转换为MessageType枚举
                if isinstance(message_type_value, str):
                    try:
                        message_type = MessageType[message_type_value.upper()]
                    except KeyError:
                        message_type = MessageType.USER  # 默认值
                else:
                    message_type = message_type_value if message_type_value is not None else MessageType.USER
                
                return MessageRecord(
                    record_id=raw_record.get('record_id', ''),
                    session_id=raw_record.get('session_id', ''),
                    timestamp=raw_record.get('timestamp', datetime.now()),
                    record_type=raw_record.get('record_type', 'message'),
                    message_type=message_type,
                    content=raw_record.get('content', ''),
                    metadata=raw_record.get('metadata', {})
                )
            elif record_type == 'tool_call':
                return ToolCallRecord(
                    record_id=raw_record.get('record_id', ''),
                    session_id=raw_record.get('session_id', ''),
                    timestamp=raw_record.get('timestamp', datetime.now()),
                    record_type=raw_record.get('record_type', 'tool_call'),
                    tool_name=raw_record.get('tool_name', ''),
                    tool_input=raw_record.get('tool_input', {}),
                    tool_output=raw_record.get('tool_output'),
                    metadata=raw_record.get('metadata', {})
                )
            elif record_type == 'llm_request':
                return LLMRequestRecord(
                    record_id=raw_record.get('record_id', ''),
                    session_id=raw_record.get('session_id', ''),
                    timestamp=raw_record.get('timestamp', datetime.now()),
                    record_type=raw_record.get('record_type', 'llm_request'),
                    model=raw_record.get('model', ''),
                    provider=raw_record.get('provider', ''),
                    messages=raw_record.get('messages', []),
                    parameters=raw_record.get('parameters', {}),
                    estimated_tokens=raw_record.get('estimated_tokens'),
                    metadata=raw_record.get('metadata', {})
                )
            elif record_type == 'llm_response':
                return LLMResponseRecord(
                    record_id=raw_record.get('record_id', ''),
                    session_id=raw_record.get('session_id', ''),
                    timestamp=raw_record.get('timestamp', datetime.now()),
                    record_type=raw_record.get('record_type', 'llm_response'),
                    request_id=raw_record.get('request_id', ''),
                    content=raw_record.get('content', ''),
                    finish_reason=raw_record.get('finish_reason', ''),
                    token_usage=raw_record.get('token_usage', {}),
                    response_time=raw_record.get('response_time', 0.0),
                    model=raw_record.get('model', ''),
                    metadata=raw_record.get('metadata', {})
                )
            elif record_type == 'token_usage':
                return TokenUsageRecord(
                    record_id=raw_record.get('record_id', ''),
                    session_id=raw_record.get('session_id', ''),
                    timestamp=raw_record.get('timestamp', datetime.now()),
                    record_type=raw_record.get('record_type', 'token_usage'),
                    model=raw_record.get('model', ''),
                    provider=raw_record.get('provider', ''),
                    prompt_tokens=raw_record.get('prompt_tokens', 0),
                    completion_tokens=raw_record.get('completion_tokens', 0),
                    total_tokens=raw_record.get('total_tokens', 0),
                    source=raw_record.get('source', ''),
                    confidence=raw_record.get('confidence', 1.0),
                    metadata=raw_record.get('metadata', {})
                )
            elif record_type == 'cost':
                return CostRecord(
                    record_id=raw_record.get('record_id', ''),
                    session_id=raw_record.get('session_id', ''),
                    timestamp=raw_record.get('timestamp', datetime.now()),
                    record_type=raw_record.get('record_type', 'cost'),
                    model=raw_record.get('model', ''),
                    provider=raw_record.get('provider', ''),
                    prompt_tokens=raw_record.get('prompt_tokens', 0),
                    completion_tokens=raw_record.get('completion_tokens', 0),
                    total_tokens=raw_record.get('total_tokens', 0),
                    prompt_cost=raw_record.get('prompt_cost', 0.0),
                    completion_cost=raw_record.get('completion_cost', 0.0),
                    total_cost=raw_record.get('total_cost', 0.0),
                    currency=raw_record.get('currency', 'USD'),
                    metadata=raw_record.get('metadata', {})
                )
            else:
                # 未知类型，返回None
                return None
        except Exception as e:
            # 如果反序列化失败，记录错误并返回None
            print(f"Failed to deserialize record: {e}")
            return None
    
    # 新增LLM相关方法
    def record_llm_request(self, record: LLMRequestRecord) -> None:
        self.storage.store_record(record)
    
    def record_llm_response(self, record: LLMResponseRecord) -> None:
        self.storage.store_record(record)
    
    def record_token_usage(self, record: TokenUsageRecord) -> None:
        self.storage.store_record(record)
    
    def record_cost(self, record: CostRecord) -> None:
        self.storage.store_record(record)
    
    # 新增查询和统计方法
    def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        获取Token使用统计
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: Token使用统计信息
        """
        # 查询Token使用记录
        raw_records = self.storage.get_all_records(session_id)
        token_records = []
        for raw_record in raw_records:
            if raw_record.get('record_type') == 'token_usage':
                token_record = self._deserialize_record(raw_record, 'token_usage')
                if token_record:
                    token_records.append(token_record)
        
        total_tokens = sum(r.total_tokens for r in token_records)
        prompt_tokens = sum(r.prompt_tokens for r in token_records)
        completion_tokens = sum(r.completion_tokens for r in token_records)
        
        return {
            "session_id": session_id,
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "record_count": len(token_records),
            "avg_tokens_per_record": total_tokens / len(token_records) if token_records else 0
        }
    
    def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        获取成本统计
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 成本统计信息
        """
        # 查询成本记录
        raw_records = self.storage.get_all_records(session_id)
        cost_records = []
        for raw_record in raw_records:
            if raw_record.get('record_type') == 'cost':
                cost_record = self._deserialize_record(raw_record, 'cost')
                if cost_record:
                    cost_records.append(cost_record)
        
        total_cost = sum(r.total_cost for r in cost_records)
        prompt_cost = sum(r.prompt_cost for r in cost_records)
        completion_cost = sum(r.completion_cost for r in cost_records)
        
        # 获取使用的模型
        models_used = list(set(r.model for r in cost_records))
        
        return {
            "session_id": session_id,
            "total_cost": total_cost,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "currency": cost_records[0].currency if cost_records else "USD",
            "record_count": len(cost_records),
            "models_used": models_used
        }
    
    def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        获取LLM调用统计
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: LLM调用统计信息
        """
        # 查询LLM相关记录
        raw_records = self.storage.get_all_records(session_id)
        llm_request_records = []
        llm_response_records = []
        
        for raw_record in raw_records:
            record_type = raw_record.get('record_type')
            if record_type == 'llm_request':
                request_record = self._deserialize_record(raw_record, 'llm_request')
                if request_record:
                    llm_request_records.append(request_record)
            elif record_type == 'llm_response':
                response_record = self._deserialize_record(raw_record, 'llm_response')
                if response_record:
                    llm_response_records.append(response_record)
        
        # 获取使用的模型
        models_used = list(set(r.model for r in llm_request_records))
        
        return {
            "session_id": session_id,
            "llm_requests": len(llm_request_records),
            "llm_responses": len(llm_response_records),
            "models_used": models_used,
            "request_record_count": len(llm_request_records),
            "response_record_count": len(llm_response_records)
        }