# History模块接口设计

## 概述

History模块负责记录和管理工作流执行过程中的各种历史数据，包括消息记录、工具调用记录、LLM请求/响应记录、Token使用记录和成本记录。基于分析，History模块需要处理多种记录类型和复杂的统计查询，目前缺少具体的存储实现。

## 现有接口分析

### 当前接口 (IHistoryManager)

```python
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
```

### 问题分析

1. **缺少实现**：只有接口定义，没有具体的存储实现
2. **查询功能不完整**：缺少灵活的查询接口
3. **统计功能有限**：只提供了基本的统计方法
4. **数据管理不足**：缺少数据清理和归档功能

## 新接口设计

### 完整的History存储接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

class RecordType(str, Enum):
    """记录类型枚举"""
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOKEN_USAGE = "token_usage"
    COST = "cost"

class IHistoryStore(ABC):
    """历史记录存储接口"""
    
    # 基本记录方法
    @abstractmethod
    async def record_message(self, record: 'MessageRecord') -> None:
        """记录消息"""
        pass
    
    @abstractmethod
    async def record_tool_call(self, record: 'ToolCallRecord') -> None:
        """记录工具调用"""
        pass
    
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
    
    # 通用记录方法
    @abstractmethod
    async def record(self, record_type: RecordType, record_data: Dict[str, Any]) -> None:
        """通用记录方法"""
        pass
    
    @abstractmethod
    async def batch_record(self, records: List[Tuple[RecordType, Dict[str, Any]]]) -> None:
        """批量记录方法"""
        pass
    
    # 查询方法
    @abstractmethod
    async def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """获取单个记录"""
        pass
    
    @abstractmethod
    async def query_records(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """查询记录"""
        pass
    
    @abstractmethod
    async def query_records_by_time_range(
        self,
        session_id: str,
        start_time: datetime,
        end_time: datetime,
        record_types: Optional[List[RecordType]] = None
    ) -> List[Dict[str, Any]]:
        """按时间范围查询记录"""
        pass
    
    @abstractmethod
    async def get_session_history(
        self, 
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话历史"""
        pass
    
    # 统计方法
    @abstractmethod
    async def get_token_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取Token统计"""
        pass
    
    @abstractmethod
    async def get_cost_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取成本统计"""
        pass
    
    @abstractmethod
    async def get_llm_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取LLM统计"""
        pass
    
    @abstractmethod
    async def get_tool_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取工具使用统计"""
        pass
    
    @abstractmethod
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要"""
        pass
    
    # 数据管理方法
    @abstractmethod
    async def delete_records(
        self, 
        filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> int:
        """删除记录"""
        pass
    
    @abstractmethod
    async def archive_records(
        self,
        filters: Dict[str, Any],
        archive_before: datetime
    ) -> int:
        """归档记录"""
        pass
    
    @abstractmethod
    async def cleanup_old_records(
        self,
        retention_days: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """清理旧记录"""
        pass
    
    # 导出导入方法
    @abstractmethod
    async def export_records(
        self,
        filters: Dict[str, Any],
        format: str = "json"
    ) -> Union[str, bytes]:
        """导出记录"""
        pass
    
    @abstractmethod
    async def import_records(
        self,
        data: Union[str, bytes],
        format: str = "json"
    ) -> int:
        """导入记录"""
        pass
```

### 基于统一存储的实现

```python
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
from ...domain.storage.interfaces import IUnifiedStorage
from ...domain.storage.exceptions import StorageError

class HistoryStore(IHistoryStore):
    """历史记录存储实现"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    # 基本记录方法实现
    async def record_message(self, record: 'MessageRecord') -> None:
        """记录消息"""
        try:
            data = {
                "id": record.record_id,
                "type": "message",
                "session_id": record.session_id,
                "timestamp": record.timestamp,
                "data": record.to_dict()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to record message {record.record_id}: {e}")
    
    async def record_tool_call(self, record: 'ToolCallRecord') -> None:
        """记录工具调用"""
        try:
            data = {
                "id": record.record_id,
                "type": "tool_call",
                "session_id": record.session_id,
                "timestamp": record.timestamp,
                "data": record.to_dict()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to record tool call {record.record_id}: {e}")
    
    async def record_llm_request(self, record: 'LLMRequestRecord') -> None:
        """记录LLM请求"""
        try:
            data = {
                "id": record.record_id,
                "type": "llm_request",
                "session_id": record.session_id,
                "timestamp": record.timestamp,
                "data": record.to_dict()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to record LLM request {record.record_id}: {e}")
    
    async def record_llm_response(self, record: 'LLMResponseRecord') -> None:
        """记录LLM响应"""
        try:
            data = {
                "id": record.record_id,
                "type": "llm_response",
                "session_id": record.session_id,
                "timestamp": record.timestamp,
                "data": record.to_dict()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to record LLM response {record.record_id}: {e}")
    
    async def record_token_usage(self, record: 'TokenUsageRecord') -> None:
        """记录Token使用"""
        try:
            data = {
                "id": record.record_id,
                "type": "token_usage",
                "session_id": record.session_id,
                "timestamp": record.timestamp,
                "data": record.to_dict()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to record token usage {record.record_id}: {e}")
    
    async def record_cost(self, record: 'CostRecord') -> None:
        """记录成本"""
        try:
            data = {
                "id": record.record_id,
                "type": "cost",
                "session_id": record.session_id,
                "timestamp": record.timestamp,
                "data": record.to_dict()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to record cost {record.record_id}: {e}")
    
    # 通用记录方法实现
    async def record(self, record_type: RecordType, record_data: Dict[str, Any]) -> None:
        """通用记录方法"""
        try:
            import uuid
            record_id = record_data.get("record_id") or str(uuid.uuid4())
            
            data = {
                "id": record_id,
                "type": record_type.value,
                "session_id": record_data.get("session_id"),
                "timestamp": record_data.get("timestamp", datetime.now()),
                "data": record_data
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to record {record_type.value}: {e}")
    
    async def batch_record(self, records: List[Tuple[RecordType, Dict[str, Any]]]) -> None:
        """批量记录方法"""
        try:
            import uuid
            operations = []
            
            for record_type, record_data in records:
                record_id = record_data.get("record_id") or str(uuid.uuid4())
                
                data = {
                    "id": record_id,
                    "type": record_type.value,
                    "session_id": record_data.get("session_id"),
                    "timestamp": record_data.get("timestamp", datetime.now()),
                    "data": record_data
                }
                operations.append({"type": "save", "data": data})
            
            await self._storage.transaction(operations)
        except Exception as e:
            raise StorageError(f"Failed to batch record: {e}")
    
    # 查询方法实现
    async def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """获取单个记录"""
        try:
            data = await self._storage.load(record_id)
            return data.get("data") if data else None
        except Exception:
            return None
    
    async def query_records(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """查询记录"""
        try:
            # 转换过滤器
            query_filters = {}
            for key, value in filters.items():
                if key == "record_type":
                    query_filters["type"] = value.value if isinstance(value, RecordType) else value
                else:
                    query_filters[f"data.{key}"] = value
            
            results = await self._storage.list(query_filters, limit)
            
            # 排序
            if order_by:
                results.sort(key=lambda x: x.get("data", {}).get(order_by, ""))
            
            # 偏移
            if offset:
                results = results[offset:]
            
            return [result.get("data") for result in results]
        except Exception as e:
            raise StorageError(f"Failed to query records: {e}")
    
    async def query_records_by_time_range(
        self,
        session_id: str,
        start_time: datetime,
        end_time: datetime,
        record_types: Optional[List[RecordType]] = None
    ) -> List[Dict[str, Any]]:
        """按时间范围查询记录"""
        try:
            filters = {
                "session_id": session_id,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            
            if record_types:
                filters["type"] = {"$in": [rt.value for rt in record_types]}
            
            results = await self._storage.list(filters)
            return [result.get("data") for result in results]
        except Exception as e:
            raise StorageError(f"Failed to query records by time range: {e}")
    
    async def get_session_history(
        self, 
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话历史"""
        try:
            filters = {"session_id": session_id}
            results = await self._storage.list(filters, limit)
            
            # 按时间排序
            results.sort(key=lambda x: x.get("timestamp", ""))
            
            return [result.get("data") for result in results]
        except Exception as e:
            raise StorageError(f"Failed to get session history: {e}")
    
    # 统计方法实现
    async def get_token_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取Token统计"""
        try:
            filters = {
                "type": "token_usage",
                "session_id": session_id
            }
            
            if time_range:
                filters["timestamp"] = {"$gte": time_range[0], "$lte": time_range[1]}
            
            results = await self._storage.list(filters)
            
            total_tokens = 0
            prompt_tokens = 0
            completion_tokens = 0
            model_stats = {}
            provider_stats = {}
            
            for result in results:
                data = result.get("data", {})
                total_tokens += data.get("total_tokens", 0)
                prompt_tokens += data.get("prompt_tokens", 0)
                completion_tokens += data.get("completion_tokens", 0)
                
                model = data.get("model", "unknown")
                provider = data.get("provider", "unknown")
                
                model_stats[model] = model_stats.get(model, 0) + data.get("total_tokens", 0)
                provider_stats[provider] = provider_stats.get(provider, 0) + data.get("total_tokens", 0)
            
            return {
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "model_statistics": model_stats,
                "provider_statistics": provider_stats,
                "record_count": len(results)
            }
        except Exception as e:
            raise StorageError(f"Failed to get token statistics: {e}")
    
    async def get_cost_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取成本统计"""
        try:
            filters = {
                "type": "cost",
                "session_id": session_id
            }
            
            if time_range:
                filters["timestamp"] = {"$gte": time_range[0], "$lte": time_range[1]}
            
            results = await self._storage.list(filters)
            
            total_cost = 0.0
            cost_by_model = {}
            cost_by_provider = {}
            
            for result in results:
                data = result.get("data", {})
                cost = data.get("cost", 0.0)
                total_cost += cost
                
                model = data.get("model", "unknown")
                provider = data.get("provider", "unknown")
                
                cost_by_model[model] = cost_by_model.get(model, 0.0) + cost
                cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + cost
            
            return {
                "total_cost": total_cost,
                "cost_by_model": cost_by_model,
                "cost_by_provider": cost_by_provider,
                "record_count": len(results)
            }
        except Exception as e:
            raise StorageError(f"Failed to get cost statistics: {e}")
    
    async def get_llm_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取LLM统计"""
        try:
            # 获取请求记录
            request_filters = {
                "type": "llm_request",
                "session_id": session_id
            }
            
            # 获取响应记录
            response_filters = {
                "type": "llm_response",
                "session_id": session_id
            }
            
            if time_range:
                time_filter = {"$gte": time_range[0], "$lte": time_range[1]}
                request_filters["timestamp"] = time_filter
                response_filters["timestamp"] = time_filter
            
            requests = await self._storage.list(request_filters)
            responses = await self._storage.list(response_filters)
            
            # 统计信息
            request_count = len(requests)
            response_count = len(responses)
            
            model_stats = {}
            provider_stats = {}
            avg_response_time = 0.0
            
            # 处理响应统计
            total_response_time = 0.0
            for result in responses:
                data = result.get("data", {})
                
                model = data.get("model", "unknown")
                provider = data.get("provider", "unknown")
                response_time = data.get("response_time", 0.0)
                
                model_stats[model] = model_stats.get(model, 0) + 1
                provider_stats[provider] = provider_stats.get(provider, 0) + 1
                total_response_time += response_time
            
            if response_count > 0:
                avg_response_time = total_response_time / response_count
            
            return {
                "request_count": request_count,
                "response_count": response_count,
                "success_rate": response_count / request_count if request_count > 0 else 0.0,
                "average_response_time": avg_response_time,
                "model_statistics": model_stats,
                "provider_statistics": provider_stats
            }
        except Exception as e:
            raise StorageError(f"Failed to get LLM statistics: {e}")
    
    async def get_tool_statistics(
        self, 
        session_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取工具使用统计"""
        try:
            filters = {
                "type": "tool_call",
                "session_id": session_id
            }
            
            if time_range:
                filters["timestamp"] = {"$gte": time_range[0], "$lte": time_range[1]}
            
            results = await self._storage.list(filters)
            
            tool_stats = {}
            success_count = 0
            error_count = 0
            
            for result in results:
                data = result.get("data", {})
                tool_name = data.get("tool_name", "unknown")
                success = data.get("success", False)
                
                tool_stats[tool_name] = tool_stats.get(tool_name, {"count": 0, "success": 0})
                tool_stats[tool_name]["count"] += 1
                if success:
                    tool_stats[tool_name]["success"] += 1
                    success_count += 1
                else:
                    error_count += 1
            
            return {
                "total_calls": len(results),
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": success_count / len(results) if results else 0.0,
                "tool_statistics": tool_stats
            }
        except Exception as e:
            raise StorageError(f"Failed to get tool statistics: {e}")
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要"""
        try:
            # 获取各种统计信息
            token_stats = await self.get_token_statistics(session_id)
            cost_stats = await self.get_cost_statistics(session_id)
            llm_stats = await self.get_llm_statistics(session_id)
            tool_stats = await self.get_tool_statistics(session_id)
            
            # 获取会话时间范围
            filters = {"session_id": session_id}
            results = await self._storage.list(filters)
            
            if not results:
                return {"session_id": session_id, "status": "empty"}
            
            timestamps = [result.get("timestamp") for result in results]
            start_time = min(timestamps)
            end_time = max(timestamps)
            duration = end_time - start_time
            
            return {
                "session_id": session_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "total_records": len(results),
                "token_statistics": token_stats,
                "cost_statistics": cost_stats,
                "llm_statistics": llm_stats,
                "tool_statistics": tool_stats
            }
        except Exception as e:
            raise StorageError(f"Failed to get session summary: {e}")
    
    # 数据管理方法实现
    async def delete_records(
        self, 
        filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> int:
        """删除记录"""
        try:
            results = await self._storage.list(filters, limit)
            count = len(results)
            
            operations = [{"type": "delete", "id": result.get("id")} for result in results]
            await self._storage.transaction(operations)
            
            return count
        except Exception as e:
            raise StorageError(f"Failed to delete records: {e}")
    
    async def archive_records(
        self,
        filters: Dict[str, Any],
        archive_before: datetime
    ) -> int:
        """归档记录"""
        try:
            # 获取需要归档的记录
            time_filters = {
                **filters,
                "timestamp": {"$lt": archive_before}
            }
            results = await self._storage.list(time_filters)
            count = len(results)
            
            # 标记为已归档
            operations = []
            for result in results:
                data = result.get("data", {})
                data["archived"] = True
                data["archived_at"] = datetime.now()
                operations.append({
                    "type": "update",
                    "id": result.get("id"),
                    "data": {"data": data}
                })
            
            await self._storage.transaction(operations)
            return count
        except Exception as e:
            raise StorageError(f"Failed to archive records: {e}")
    
    async def cleanup_old_records(
        self,
        retention_days: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """清理旧记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            filters = {"timestamp": {"$lt": cutoff_date}}
            
            if dry_run:
                results = await self._storage.list(filters)
                return {
                    "dry_run": True,
                    "records_to_delete": len(results),
                    "cutoff_date": cutoff_date
                }
            else:
                count = await self.delete_records(filters)
                return {
                    "dry_run": False,
                    "records_deleted": count,
                    "cutoff_date": cutoff_date
                }
        except Exception as e:
            raise StorageError(f"Failed to cleanup old records: {e}")
    
    # 导出导入方法实现
    async def export_records(
        self,
        filters: Dict[str, Any],
        format: str = "json"
    ) -> Union[str, bytes]:
        """导出记录"""
        try:
            results = await self._storage.list(filters)
            records = [result.get("data") for result in results]
            
            if format == "json":
                import json
                return json.dumps(records, indent=2, default=str)
            elif format == "csv":
                import csv
                import io
                
                if not records:
                    return ""
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            raise StorageError(f"Failed to export records: {e}")
    
    async def import_records(
        self,
        data: Union[str, bytes],
        format: str = "json"
    ) -> int:
        """导入记录"""
        try:
            if format == "json":
                import json
                records = json.loads(data)
            elif format == "csv":
                import csv
                import io
                
                records = []
                reader = csv.DictReader(io.StringIO(data))
                for row in reader:
                    records.append(dict(row))
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            # 批量导入
            record_tuples = []
            for record in records:
                record_type = RecordType(record.get("type", "message"))
                record_tuples.append((record_type, record))
            
            await self.batch_record(record_tuples)
            return len(records)
        except Exception as e:
            raise StorageError(f"Failed to import records: {e}")
```

## 数据模型

### 历史记录数据模型

```python
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class BaseHistoryRecord(BaseModel):
    """基础历史记录模型"""
    record_id: str
    session_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class MessageRecord(BaseHistoryRecord):
    """消息记录"""
    role: str  # user, assistant, system
    content: str
    message_type: str = "text"  # text, image, audio, etc.

class ToolCallRecord(BaseHistoryRecord):
    """工具调用记录"""
    tool_name: str
    tool_args: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    execution_time: Optional[float] = None

class LLMRequestRecord(BaseHistoryRecord):
    """LLM请求记录"""
    model: str
    provider: str
    messages: list
    parameters: Dict[str, Any] = {}
    request_id: Optional[str] = None

class LLMResponseRecord(BaseHistoryRecord):
    """LLM响应记录"""
    request_id: str
    model: str
    provider: str
    content: str
    finish_reason: Optional[str] = None
    response_time: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None

class TokenUsageRecord(BaseHistoryRecord):
    """Token使用记录"""
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    source: str = "api"  # api, local, estimated
    confidence: float = 1.0

class CostRecord(BaseHistoryRecord):
    """成本记录"""
    model: str
    provider: str
    cost: float
    currency: str = "USD"
    cost_breakdown: Dict[str, float] = {}
```

## 性能优化

### 存储优化

1. **索引策略**：
   - 按session_id索引
   - 按timestamp索引
   - 按record_type索引
   - 复合索引(session_id, timestamp)

2. **分区策略**：
   - 按时间分区（月度分区）
   - 按会话ID分区

3. **压缩策略**：
   - 历史数据压缩存储
   - 大字段单独存储

### 查询优化

1. **缓存策略**：
   - 缓存常用统计数据
   - 缓存会话摘要
   - 缓存最近的历史记录

2. **预计算**：
   - 预计算常用统计
   - 定期更新汇总数据

3. **批量操作**：
   - 批量插入记录
   - 批量删除记录

## 评估结论

### 可行性评估

1. **技术可行性**：高
   - 统一存储接口可以满足History模块的复杂需求
   - 支持灵活的查询和统计功能
   - 可以处理大数据量的历史记录

2. **迁移风险**：低
   - 目前缺少实现，没有迁移负担
   - 可以直接实现新接口
   - 不影响现有功能

3. **性能影响**：中
   - 历史记录数据量大，需要优化
   - 统计查询可能较慢，需要缓存
   - 需要合理的数据生命周期管理

### 推荐方案

**推荐使用完整的History存储接口**

理由：
1. 满足了History模块的所有需求
2. 提供了灵活的查询和统计功能
3. 支持数据管理和归档
4. 为未来扩展提供了良好的基础

### 实现优先级

1. **高优先级**：
   - 基本记录方法
   - 基本查询方法
   - 基本统计方法

2. **中优先级**：
   - 批量操作
   - 高级查询功能
   - 数据管理方法

3. **低优先级**：
   - 导出导入功能
   - 性能优化
   - 监控和日志