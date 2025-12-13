"""内存History Repository实现

提供基于内存的历史记录Repository实现，用于测试和开发环境。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional
from datetime import datetime
import threading
from collections import defaultdict

from src.interfaces.repository.history import IHistoryRepository
from src.core.history.entities import (
    BaseHistoryRecord, LLMRequestRecord, LLMResponseRecord,
    TokenUsageRecord, CostRecord, WorkflowTokenStatistics,
    RecordType, HistoryQuery
)
from ..memory_base import MemoryBaseRepository
from ..utils import TimeUtils, IdUtils


logger = get_logger(__name__)


class MemoryHistoryRepository(MemoryBaseRepository, IHistoryRepository):
    """内存History Repository实现
    
    提供基于内存的历史记录存储，支持所有IHistoryRepository接口方法。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存Repository
        
        Args:
            config: 配置参数，可包含 max_records 等选项
        """
        super().__init__(config)
        self.max_records = config.get("max_records", 10000)
        self._workflow_stats: Dict[str, WorkflowTokenStatistics] = {}
        self._lock = threading.RLock()
        
        self.logger.info(f"内存History Repository初始化完成，最大记录数: {self.max_records}")
    
    # === 基础CRUD操作 ===
    
    async def save_record(self, record: BaseHistoryRecord) -> bool:
        """保存历史记录"""
        try:
            def _save():
                with self._lock:
                    # 检查容量限制
                    if len(self._storage) >= self.max_records:
                        self._cleanup_old_records()
                    
                    # 保存记录
                    record_data = record.to_dict()
                    self._save_item(record.record_id, record_data)
                    
                    # 更新索引
                    self._update_indexes(record)
                    
                    # 更新工作流统计
                    if isinstance(record, TokenUsageRecord):
                        self._update_workflow_stats(record)
                    
                    self._log_operation("保存历史记录", True, record.record_id)
                    return True
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存历史记录", e)
            return False
    
    async def save_records(self, records: List[BaseHistoryRecord]) -> List[bool]:
        """批量保存历史记录"""
        results = []
        for record in records:
            result = await self.save_record(record)
            results.append(result)
        return results
    
    async def get_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        record_type: Optional[RecordType] = None,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseHistoryRecord]:
        """获取历史记录"""
        try:
            def _get():
                with self._lock:
                    # 获取候选记录
                    candidate_ids = set(self._storage.keys())
                    
                    # 应用过滤条件
                    if session_id:
                        session_ids = set(self._get_from_index("session_id", session_id))
                        candidate_ids &= session_ids
                    
                    if workflow_id:
                        workflow_ids = set(self._get_from_index("workflow_id", workflow_id))
                        candidate_ids &= workflow_ids
                    
                    if record_type:
                        type_ids = set(self._get_from_index("record_type", record_type.value))
                        candidate_ids &= type_ids
                    
                    if model:
                        model_ids = set(self._get_from_index("model", model))
                        candidate_ids &= model_ids
                    
                    # 获取记录并应用时间过滤
                    records = []
                    for record_id in candidate_ids:
                        record_data = self._load_item(record_id)
                        if not record_data:
                            continue
                        
                        record = self._create_record_from_data(record_data)
                        if not record:
                            continue
                        
                        # 时间过滤
                        if start_time and record.timestamp < start_time:
                            continue
                        if end_time and record.timestamp > end_time:
                            continue
                        
                        records.append(record)
                    
                    # 按时间排序
                    records.sort(key=lambda r: r.timestamp, reverse=True)
                    
                    # 应用分页
                    return records[offset:offset + limit]
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取历史记录", e)
            return []
    
    async def get_record_by_id(self, record_id: str) -> Optional[BaseHistoryRecord]:
        """根据ID获取记录"""
        try:
            def _get():
                record_data = self._load_item(record_id)
                if record_data:
                    return self._create_record_from_data(record_data)
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("根据ID获取记录", e)
            return None
    
    async def delete_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional[datetime] = None
    ) -> int:
        """删除历史记录"""
        try:
            def _delete():
                with self._lock:
                    records_to_delete = []
                    
                    for record_id, record_data in self._storage.items():
                        should_delete = False
                        
                        if session_id and record_data.get('session_id') == session_id:
                            should_delete = True
                        elif workflow_id and record_data.get('workflow_id') == workflow_id:
                            should_delete = True
                        elif older_than:
                            timestamp = record_data.get('timestamp')
                            if timestamp:
                                record_time = datetime.fromisoformat(timestamp)
                                if record_time < older_than:
                                    should_delete = True
                        
                        if should_delete:
                            records_to_delete.append(record_id)
                    
                    # 删除记录
                    for record_id in records_to_delete:
                        record_data = self._load_item(record_id)
                        if record_data:
                            self._remove_from_indexes(record_data)
                            self._delete_item(record_id)
                    
                    self._log_operation("删除历史记录", True, f"删除了 {len(records_to_delete)} 条记录")
                    return len(records_to_delete)
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除历史记录", e)
            return 0
    
    async def delete_records_by_query(self, query: HistoryQuery) -> int:
        """根据查询条件删除历史记录"""
        try:
            def _delete():
                with self._lock:
                    records_to_delete = []
                    
                    for record_id, record_data in self._storage.items():
                        should_delete = True
                        
                        # 应用所有过滤条件
                        if query.session_id and record_data.get('session_id') != query.session_id:
                            should_delete = False
                        
                        if query.workflow_id and record_data.get('workflow_id') != query.workflow_id:
                            should_delete = False
                        
                        if query.record_type:
                            record_type_value = record_data.get('record_type')
                            if record_type_value != query.record_type.value:
                                should_delete = False
                        
                        if query.model and record_data.get('model') != query.model:
                            should_delete = False
                        
                        # 时间范围过滤
                        if should_delete:
                            timestamp = record_data.get('timestamp')
                            if timestamp:
                                record_time = datetime.fromisoformat(timestamp)
                                if query.start_time and record_time < query.start_time:
                                    should_delete = False
                                if query.end_time and record_time > query.end_time:
                                    should_delete = False
                        
                        if should_delete:
                            records_to_delete.append(record_id)
                    
                    # 删除记录
                    for record_id in records_to_delete:
                        record_data = self._load_item(record_id)
                        if record_data:
                            self._remove_from_indexes(record_data)
                            self._delete_item(record_id)
                    
                    self._log_operation("根据查询条件删除历史记录", True, f"删除了 {len(records_to_delete)} 条记录")
                    return len(records_to_delete)
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("根据查询条件删除历史记录", e)
            return 0
    
    # === 统计相关操作 ===
    
    async def get_workflow_token_stats(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[WorkflowTokenStatistics]:
        """获取工作流Token统计"""
        try:
            def _get():
                with self._lock:
                    stats = []
                    
                    if model:
                        # 获取特定模型的统计
                        key = f"{workflow_id}:{model}"
                        if key in self._workflow_stats:
                            stat = self._workflow_stats[key]
                            if self._is_stat_in_time_range(stat, start_time, end_time):
                                stats.append(stat)
                    else:
                        # 获取所有模型的统计
                        for key, stat in self._workflow_stats.items():
                            if key.startswith(f"{workflow_id}:"):
                                if self._is_stat_in_time_range(stat, start_time, end_time):
                                    stats.append(stat)
                    
                    return stats
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取工作流Token统计", e)
            return []
    
    async def update_workflow_token_stats(
        self,
        stats: WorkflowTokenStatistics
    ) -> bool:
        """更新工作流Token统计"""
        try:
            def _update():
                with self._lock:
                    key = f"{stats.workflow_id}:{stats.model}"
                    self._workflow_stats[key] = stats
                    self._log_operation("更新工作流Token统计", True, key)
                    return True
            
            return await asyncio.get_event_loop().run_in_executor(None, _update)
            
        except Exception as e:
            self._handle_exception("更新工作流Token统计", e)
            return False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            def _get_stats():
                with self._lock:
                    # 按类型统计
                    type_counts = defaultdict(int)
                    model_counts = defaultdict(int)
                    workflow_counts = defaultdict(int)
                    session_counts = defaultdict(int)
                    
                    for record_data in self._storage.values():
                        # 记录类型统计
                        record_type = record_data.get("record_type", "unknown")
                        type_counts[record_type] += 1
                        
                        # 模型统计
                        if record_data.get("model"):
                            model_counts[record_data["model"]] += 1
                        
                        # 工作流统计
                        if record_data.get("workflow_id"):
                            workflow_counts[record_data["workflow_id"]] += 1
                        
                        # 会话统计
                        if record_data.get("session_id"):
                            session_counts[record_data["session_id"]] += 1
                    
                    return {
                        "total_records": len(self._storage),
                        "max_records": self.max_records,
                        "usage_percentage": len(self._storage) / self.max_records * 100,
                        "record_types": dict(type_counts),
                        "models": dict(model_counts),
                        "workflows": dict(workflow_counts),
                        "sessions": dict(session_counts),
                        "workflow_stats_count": len(self._workflow_stats),
                        "index_sizes": {
                            name: len(index) for name, index in self._indexes.items()
                        }
                    }
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
            
        except Exception as e:
            self._handle_exception("获取存储统计信息", e)
            return {}
    
    # === 兼容性方法（向后兼容旧的接口） ===
    
    async def save_history(self, entry: Dict[str, Any]) -> str:
        """保存历史记录（兼容性方法）"""
        # 将字典转换为BaseHistoryRecord
        record_id = IdUtils.get_or_generate_id(entry, "record_id", IdUtils.generate_history_id)
        entry["record_id"] = record_id
        
        # 创建基础记录
        record = BaseHistoryRecord(**entry)
        success = await self.save_record(record)
        return record_id if success else ""
    
    async def get_history(self, thread_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录（兼容性方法）"""
        records = await self.get_records(session_id=thread_id, limit=limit)
        return [record.to_dict() for record in records]
    
    async def get_history_by_timerange(
        self, 
        thread_id: str, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """按时间范围获取历史记录（兼容性方法）"""
        records = await self.get_records(
            session_id=thread_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return [record.to_dict() for record in records]
    
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录（兼容性方法）"""
        deleted_count = await self.delete_records()
        return deleted_count > 0
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录（兼容性方法）"""
        deleted_count = await self.delete_records(session_id=agent_id)
        return deleted_count > 0
    
    async def clear_thread_history(self, thread_id: str) -> bool:
        """清空线程的历史记录
        
        Args:
            thread_id: 线程ID
            
        Returns:
            bool: 是否清空成功
        """
        deleted_count = await self.delete_records(session_id=thread_id)
        return deleted_count > 0
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息（兼容性方法）"""
        return await self.get_storage_statistics()
    
    async def get_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取历史记录（兼容性方法）"""
        record = await self.get_record_by_id(history_id)
        return record.to_dict() if record else None
    
    # === 私有辅助方法 ===
    
    def _update_indexes(self, record: BaseHistoryRecord) -> None:
        """更新索引"""
        record_data = record.to_dict()
        record_id = record.record_id
        
        # 会话ID索引
        if record.session_id:
            self._add_to_index("session_id", record.session_id, record_id)
        
        # 工作流ID索引
        if record.workflow_id:
            self._add_to_index("workflow_id", record.workflow_id, record_id)
        
        # 记录类型索引
        if hasattr(record, 'record_type'):
            self._add_to_index("record_type", record.record_type.value, record_id)
        
        # 模型索引
        if hasattr(record, 'model'):
            model = getattr(record, 'model', None)
            if model:
                self._add_to_index("model", model, record_id)
    
    def _remove_from_indexes(self, record_data: Dict[str, Any]) -> None:
        """从索引中移除记录"""
        record_id = record_data.get("record_id")
        if not record_id:
            return
        
        # 会话ID索引
        if record_data.get("session_id"):
            self._remove_from_index("session_id", record_data["session_id"], record_id)
        
        # 工作流ID索引
        if record_data.get("workflow_id"):
            self._remove_from_index("workflow_id", record_data["workflow_id"], record_id)
        
        # 记录类型索引
        if record_data.get("record_type"):
            self._remove_from_index("record_type", record_data["record_type"], record_id)
        
        # 模型索引
        if record_data.get("model"):
            self._remove_from_index("model", record_data["model"], record_id)
    
    def _update_workflow_stats(self, record: TokenUsageRecord) -> None:
        """更新工作流统计"""
        if not record.workflow_id:
            return
        
        key = f"{record.workflow_id}:{record.model}"
        
        if key not in self._workflow_stats:
            self._workflow_stats[key] = WorkflowTokenStatistics(
                workflow_id=record.workflow_id,
                model=record.model
            )
        
        stats = self._workflow_stats[key]
        stats.update_from_record(record)
    
    def _is_stat_in_time_range(
        self,
        stat: WorkflowTokenStatistics,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> bool:
        """检查统计是否在时间范围内"""
        if start_time and stat.period_start and stat.period_start < start_time:
            return False
        if end_time and stat.period_end and stat.period_end > end_time:
            return False
        return True
    
    def _cleanup_old_records(self) -> None:
        """清理旧记录"""
        if len(self._storage) <= self.max_records:
            return
        
        # 按时间排序，删除最旧的记录
        sorted_records = sorted(
            self._storage.items(),
            key=lambda x: x[1].get("timestamp", "")
        )
        
        # 删除最旧的10%记录
        delete_count = int(self.max_records * 0.1)
        for i in range(delete_count):
            if i < len(sorted_records):
                record_id, record_data = sorted_records[i]
                self._remove_from_indexes(record_data)
                self._delete_item(record_id)
        
        self.logger.info(f"清理了 {delete_count} 条旧记录")
    
    def _create_record_from_data(self, data: Dict[str, Any]) -> Optional[BaseHistoryRecord]:
        """从数据字典创建记录对象"""
        try:
            record_type = data.get("record_type", "unknown")
            
            if record_type == "llm_request":
                return LLMRequestRecord(**data)
            elif record_type == "llm_response":
                return LLMResponseRecord(**data)
            elif record_type == "token_usage":
                return TokenUsageRecord(**data)
            elif record_type == "cost":
                return CostRecord(**data)
            else:
                # 尝试创建基础记录
                return BaseHistoryRecord(**data)
                
        except Exception as e:
            self.logger.warning(f"创建记录对象失败: {e}")
            return None


# 需要导入 asyncio
import asyncio