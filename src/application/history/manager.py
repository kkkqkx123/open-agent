"""历史管理器 - 重构版本"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult, MessageType
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord
from src.infrastructure.history.storage.file_storage import FileHistoryStorage

# 导入公用组件
from src.infrastructure.common.serialization.universal_serializer import UniversalSerializer
from src.infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from src.infrastructure.common.temporal.temporal_manager import TemporalManager
from src.infrastructure.common.metadata.metadata_manager import MetadataManager
from src.infrastructure.common.id_generator.id_generator import IDGenerator
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor


class HistoryManager(IHistoryManager):
    """历史管理器实现 - 重构版本"""
    
    def __init__(
        self,
        storage: FileHistoryStorage,
        serializer: Optional[UniversalSerializer] = None,
        cache_manager: Optional[EnhancedCacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化历史管理器"""
        self.storage = storage
        
        # 公用组件
        self.serializer = serializer or UniversalSerializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
        self.id_generator = IDGenerator()
    
    def record_message(self, record: MessageRecord) -> None:
        """记录消息"""
        operation_id = self.monitor.start_operation("record_message")
        
        try:
            # 使用公用组件处理记录
            processed_record = self._process_record(record)
            
            # 序列化记录
            serialized_record = self.serializer.serialize(processed_record, "compact_json")
            
            # 存储记录
            self.storage.store_record(processed_record)
            
            # 缓存记录
            if self.cache:
                cache_key = f"message:{record.record_id}"
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, processed_record, ttl=1800))
            
            self.monitor.end_operation(operation_id, "record_message", True)
            
        except Exception as e:
            self.monitor.end_operation(operation_id, "record_message", False, {"error": str(e)})
            raise
    
    def record_tool_call(self, record: ToolCallRecord) -> None:
        """记录工具调用"""
        operation_id = self.monitor.start_operation("record_tool_call")
        
        try:
            # 使用公用组件处理记录
            processed_record = self._process_record(record)
            
            # 序列化记录
            serialized_record = self.serializer.serialize(processed_record, "compact_json")
            
            # 存储记录
            self.storage.store_record(processed_record)
            
            # 缓存记录
            if self.cache:
                cache_key = f"tool_call:{record.record_id}"
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, processed_record, ttl=1800))
            
            self.monitor.end_operation(operation_id, "record_tool_call", True)
            
        except Exception as e:
            self.monitor.end_operation(operation_id, "record_tool_call", False, {"error": str(e)})
            raise
    
    def query_history(self, query: HistoryQuery) -> HistoryResult:
        """查询历史记录"""
        operation_id = self.monitor.start_operation("query_history")
        
        try:
            # 先尝试从缓存获取
            cache_key = f"history_query:{hash(str(query.__dict__))}"
            if self.cache:
                import asyncio
                cached_result = asyncio.run(self.cache.get(cache_key))
                if cached_result:
                    self.monitor.end_operation(
                        operation_id, "query_history", True,
                        {"cache_hit": True}
                    )
                    return HistoryResult(**cached_result)
            
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
            
            result = HistoryResult(records=all_records, total=total)
            
            # 缓存结果
            if self.cache:
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, result.__dict__, ttl=300))
            
            self.monitor.end_operation(
                operation_id, "query_history", True,
                {"cache_hit": False, "count": len(all_records)}
            )
            
            return result
        except Exception as e:
            self.monitor.end_operation(operation_id, "query_history", False, {"error": str(e)})
            raise
    
    def _process_record(self, record) -> Any:
        """处理记录，使用公用组件"""
        # 标准化元数据
        if hasattr(record, 'metadata'):
            record.metadata = self.metadata.normalize_metadata(record.metadata)
        
        # 处理时间戳
        if hasattr(record, 'timestamp'):
            record.timestamp = self.temporal.format_timestamp(record.timestamp, "iso")
        
        return record
    
    def _deserialize_record(self, raw_record: Dict[str, Any], record_type: str):
        """将原始字典反序列化为记录对象"""
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
    
    def record_llm_request(self, record: LLMRequestRecord) -> None:
        """记录LLM请求"""
        operation_id = self.monitor.start_operation("record_llm_request")
        
        try:
            # 使用公用组件处理记录
            processed_record = self._process_record(record)
            
            # 序列化记录
            serialized_record = self.serializer.serialize(processed_record, "compact_json")
            
            # 存储记录
            self.storage.store_record(processed_record)
            
            # 缓存记录
            if self.cache:
                cache_key = f"llm_request:{record.record_id}"
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, processed_record, ttl=1800))
            
            self.monitor.end_operation(operation_id, "record_llm_request", True)
            
        except Exception as e:
            self.monitor.end_operation(operation_id, "record_llm_request", False, {"error": str(e)})
            raise
    
    def record_llm_response(self, record: LLMResponseRecord) -> None:
        """记录LLM响应"""
        operation_id = self.monitor.start_operation("record_llm_response")
        
        try:
            # 使用公用组件处理记录
            processed_record = self._process_record(record)
            
            # 序列化记录
            serialized_record = self.serializer.serialize(processed_record, "compact_json")
            
            # 存储记录
            self.storage.store_record(processed_record)
            
            # 缓存记录
            if self.cache:
                cache_key = f"llm_response:{record.record_id}"
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, processed_record, ttl=1800))
            
            self.monitor.end_operation(operation_id, "record_llm_response", True)
            
        except Exception as e:
            self.monitor.end_operation(operation_id, "record_llm_response", False, {"error": str(e)})
            raise
    
    def record_token_usage(self, record: TokenUsageRecord) -> None:
        """记录Token使用"""
        operation_id = self.monitor.start_operation("record_token_usage")
        
        try:
            # 使用公用组件处理记录
            processed_record = self._process_record(record)
            
            # 序列化记录
            serialized_record = self.serializer.serialize(processed_record, "compact_json")
            
            # 存储记录
            self.storage.store_record(processed_record)
            
            # 缓存记录
            if self.cache:
                cache_key = f"token_usage:{record.record_id}"
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, processed_record, ttl=1800))
            
            self.monitor.end_operation(operation_id, "record_token_usage", True)
            
        except Exception as e:
            self.monitor.end_operation(operation_id, "record_token_usage", False, {"error": str(e)})
            raise
    
    def record_cost(self, record: CostRecord) -> None:
        """记录成本"""
        operation_id = self.monitor.start_operation("record_cost")
        
        try:
            # 使用公用组件处理记录
            processed_record = self._process_record(record)
            
            # 序列化记录
            serialized_record = self.serializer.serialize(processed_record, "compact_json")
            
            # 存储记录
            self.storage.store_record(processed_record)
            
            # 缓存记录
            if self.cache:
                cache_key = f"cost:{record.record_id}"
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, processed_record, ttl=1800))
            
            self.monitor.end_operation(operation_id, "record_cost", True)
            
        except Exception as e:
            self.monitor.end_operation(operation_id, "record_cost", False, {"error": str(e)})
            raise
    
    def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取Token使用统计"""
        operation_id = self.monitor.start_operation("get_token_statistics")
        
        try:
            # 先尝试从缓存获取
            cache_key = f"token_stats:{session_id}"
            if self.cache:
                import asyncio
                cached_stats = asyncio.run(self.cache.get(cache_key))
                if cached_stats:
                    self.monitor.end_operation(
                        operation_id, "get_token_statistics", True,
                        {"cache_hit": True}
                    )
                    return cached_stats
            
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
            
            result = {
                "session_id": session_id,
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "record_count": len(token_records),
                "avg_tokens_per_record": total_tokens / len(token_records) if token_records else 0
            }
            
            # 缓存结果
            if self.cache:
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, result, ttl=600))
            
            self.monitor.end_operation(
                operation_id, "get_token_statistics", True,
                {"cache_hit": False, "session_id": session_id}
            )
            
            return result
        except Exception as e:
            self.monitor.end_operation(operation_id, "get_token_statistics", False, {"error": str(e)})
            raise
    
    def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        operation_id = self.monitor.start_operation("get_cost_statistics")
        
        try:
            # 先尝试从缓存获取
            cache_key = f"cost_stats:{session_id}"
            if self.cache:
                import asyncio
                cached_stats = asyncio.run(self.cache.get(cache_key))
                if cached_stats:
                    self.monitor.end_operation(
                        operation_id, "get_cost_statistics", True,
                        {"cache_hit": True}
                    )
                    return cached_stats
            
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
            
            result = {
                "session_id": session_id,
                "total_cost": total_cost,
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "currency": cost_records[0].currency if cost_records else "USD",
                "record_count": len(cost_records),
                "models_used": models_used
            }
            
            # 缓存结果
            if self.cache:
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, result, ttl=600))
            
            self.monitor.end_operation(
                operation_id, "get_cost_statistics", True,
                {"cache_hit": False, "session_id": session_id}
            )
            
            return result
        except Exception as e:
            self.monitor.end_operation(operation_id, "get_cost_statistics", False, {"error": str(e)})
            raise
    
    def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM调用统计"""
        operation_id = self.monitor.start_operation("get_llm_statistics")
        
        try:
            # 先尝试从缓存获取
            cache_key = f"llm_stats:{session_id}"
            if self.cache:
                import asyncio
                cached_stats = asyncio.run(self.cache.get(cache_key))
                if cached_stats:
                    self.monitor.end_operation(
                        operation_id, "get_llm_statistics", True,
                        {"cache_hit": True}
                    )
                    return cached_stats
            
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
            
            result = {
                "session_id": session_id,
                "llm_requests": len(llm_request_records),
                "llm_responses": len(llm_response_records),
                "models_used": models_used,
                "request_record_count": len(llm_request_records),
                "response_record_count": len(llm_response_records)
            }
            
            # 缓存结果
            if self.cache:
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, result, ttl=600))
            
            self.monitor.end_operation(
                operation_id, "get_llm_statistics", True,
                {"cache_hit": False, "session_id": session_id}
            )
            
            return result
        except Exception as e:
            self.monitor.end_operation(operation_id, "get_llm_statistics", False, {"error": str(e)})
            raise