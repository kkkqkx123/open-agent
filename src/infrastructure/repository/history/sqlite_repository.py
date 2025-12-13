"""SQLite History Repository实现

提供基于SQLite的历史记录Repository实现，用于生产环境。
"""

import asyncio
from src.interfaces.dependency_injection import get_logger
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from src.interfaces.repository.history import IHistoryRepository
from src.core.history.entities import (
    BaseHistoryRecord, LLMRequestRecord, LLMResponseRecord,
    TokenUsageRecord, CostRecord, WorkflowTokenStatistics,
    RecordType, HistoryQuery
)
from ..sqlite_base import SQLiteBaseRepository
from ..utils import TimeUtils, IdUtils


logger = get_logger(__name__)


class SQLiteHistoryRepository(SQLiteBaseRepository, IHistoryRepository):
    """SQLite History Repository实现
    
    提供基于SQLite的历史记录存储，支持所有IHistoryRepository接口方法。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite Repository
        
        Args:
            config: 配置参数，包含 db_path 等选项
        """
        # 定义表结构和索引
        table_sql = """
            CREATE TABLE IF NOT EXISTS history_records (
                record_id TEXT PRIMARY KEY,
                session_id TEXT,
                workflow_id TEXT,
                record_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                model TEXT,
                provider TEXT,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_history_session_id ON history_records(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_history_workflow_id ON history_records(workflow_id)",
            "CREATE INDEX IF NOT EXISTS idx_history_record_type ON history_records(record_type)",
            "CREATE INDEX IF NOT EXISTS idx_history_model ON history_records(model)",
            "CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history_records(timestamp)"
        ]
        
        # 工作流统计表
        workflow_stats_table_sql = """
            CREATE TABLE IF NOT EXISTS workflow_stats (
                workflow_id TEXT NOT NULL,
                model TEXT NOT NULL,
                total_prompt_tokens INTEGER DEFAULT 0,
                total_completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                request_count INTEGER DEFAULT 0,
                period_start TEXT,
                period_end TEXT,
                last_updated TEXT NOT NULL,
                PRIMARY KEY (workflow_id, model)
            )
        """
        
        workflow_stats_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_workflow_stats_workflow_id ON workflow_stats(workflow_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_stats_model ON workflow_stats(model)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_stats_last_updated ON workflow_stats(last_updated)"
        ]
        
        # 初始化主表
        super().__init__(config, "history_records", table_sql, indexes_sql)
        
        # 初始化工作流统计表
        self._init_workflow_stats_table(workflow_stats_table_sql, workflow_stats_indexes_sql)
        
        self.logger.info(f"SQLite History Repository初始化完成: {self.db_path}")
    
    def _init_workflow_stats_table(self, table_sql: str, indexes_sql: List[str]) -> None:
        """初始化工作流统计表"""
        try:
            from ..utils import SQLiteUtils
            SQLiteUtils.init_database(self.db_path, table_sql, indexes_sql)
            self._log_operation("工作流统计表初始化", True)
        except Exception as e:
            self._handle_exception("工作流统计表初始化", e)
    
    # === 基础CRUD操作 ===
    
    async def save_record(self, record: BaseHistoryRecord) -> bool:
        """保存历史记录"""
        try:
            def _save():
                data = {
                    "record_id": record.record_id,
                    "session_id": getattr(record, 'session_id', None),
                    "workflow_id": getattr(record, 'workflow_id', None),
                    "record_type": record.record_type.value if hasattr(record, 'record_type') else 'unknown',
                    "timestamp": record.timestamp.isoformat(),
                    "model": getattr(record, 'model', None),
                    "provider": getattr(record, 'provider', None),
                    "data": record.to_dict()
                }
                
                self._insert_or_replace(data)
                self._log_operation("保存历史记录", True, record.record_id)
                return True
            
            await asyncio.get_event_loop().run_in_executor(None, _save)
            return True
            
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
                from ..utils import SQLiteUtils
                
                # 构建查询
                query = "SELECT * FROM history_records WHERE 1=1"
                params = []
                
                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                if workflow_id:
                    query += " AND workflow_id = ?"
                    params.append(workflow_id)
                
                if record_type:
                    query += " AND record_type = ?"
                    params.append(record_type.value)
                
                if model:
                    query += " AND model = ?"
                    params.append(model)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                rows = SQLiteUtils.execute_query(self.db_path, query, tuple(params))
                
                # 转换为记录对象
                records = []
                for row in rows:
                    try:
                        data = json.loads(row[7])  # data 字段在第7列
                        record = self._create_record_from_data(data)
                        if record:
                            records.append(record)
                    except Exception as e:
                        self.logger.warning(f"解析记录失败: {row[0]}, 错误: {e}")
                        continue
                
                return records
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取历史记录", e)
            return []
    
    async def get_record_by_id(self, record_id: str) -> Optional[BaseHistoryRecord]:
        """根据ID获取记录"""
        try:
            def _get():
                from ..utils import SQLiteUtils
                
                row = SQLiteUtils.find_by_id(self.db_path, "history_records", "record_id", record_id)
                
                if row:
                    data = json.loads(row[7])  # data 字段在第7列
                    return self._create_record_from_data(data)
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
                from ..utils import SQLiteUtils
                
                query = "DELETE FROM history_records WHERE 1=1"
                params = []
                
                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                if workflow_id:
                    query += " AND workflow_id = ?"
                    params.append(workflow_id)
                
                if older_than:
                    query += " AND timestamp < ?"
                    params.append(older_than.isoformat())
                
                deleted_count = SQLiteUtils.execute_update(self.db_path, query, tuple(params))
                self._log_operation("删除历史记录", True, f"删除了 {deleted_count} 条记录")
                return deleted_count
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除历史记录", e)
            return 0
    
    async def delete_records_by_query(self, query: HistoryQuery) -> int:
        """根据查询条件删除历史记录"""
        try:
            def _delete():
                from ..utils import SQLiteUtils
                
                delete_query = "DELETE FROM history_records WHERE 1=1"
                params = []
                
                if query.session_id:
                    delete_query += " AND session_id = ?"
                    params.append(query.session_id)
                
                if query.workflow_id:
                    delete_query += " AND workflow_id = ?"
                    params.append(query.workflow_id)
                
                if query.record_type:
                    delete_query += " AND record_type = ?"
                    params.append(query.record_type.value)
                
                if query.model:
                    delete_query += " AND model = ?"
                    params.append(query.model)
                
                if query.start_time:
                    delete_query += " AND timestamp >= ?"
                    params.append(query.start_time.isoformat())
                
                if query.end_time:
                    delete_query += " AND timestamp <= ?"
                    params.append(query.end_time.isoformat())
                
                deleted_count = SQLiteUtils.execute_update(self.db_path, delete_query, tuple(params))
                self._log_operation("根据查询条件删除历史记录", True, f"删除了 {deleted_count} 条记录")
                return deleted_count
            
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
                from ..utils import SQLiteUtils
                
                query = "SELECT * FROM workflow_stats WHERE workflow_id = ?"
                params = [workflow_id]
                
                if model:
                    query += " AND model = ?"
                    params.append(model)
                
                rows = SQLiteUtils.execute_query(self.db_path, query, tuple(params))
                
                stats = []
                for row in rows:
                    stat = WorkflowTokenStatistics(
                        workflow_id=row[0],
                        model=row[1]
                    )
                    stat.total_prompt_tokens = row[2]
                    stat.total_completion_tokens = row[3]
                    stat.total_tokens = row[4]
                    stat.total_cost = row[5]
                    stat.request_count = row[6]
                    
                    if row[7]:  # period_start
                        stat.period_start = datetime.fromisoformat(row[7])
                    if row[8]:  # period_end
                        stat.period_end = datetime.fromisoformat(row[8])
                    stat.last_updated = datetime.fromisoformat(row[9])
                    
                    # 时间范围过滤
                    if start_time and stat.period_start and stat.period_start < start_time:
                        continue
                    if end_time and stat.period_end and stat.period_end > end_time:
                        continue
                    
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
                from ..utils import SQLiteUtils
                
                data = {
                    "workflow_id": stats.workflow_id,
                    "model": stats.model,
                    "total_prompt_tokens": stats.total_prompt_tokens,
                    "total_completion_tokens": stats.total_completion_tokens,
                    "total_tokens": stats.total_tokens,
                    "total_cost": stats.total_cost,
                    "request_count": stats.request_count,
                    "period_start": stats.period_start.isoformat() if stats.period_start else None,
                    "period_end": stats.period_end.isoformat() if stats.period_end else None,
                    "last_updated": stats.last_updated.isoformat()
                }
                
                SQLiteUtils.insert_or_replace(self.db_path, "workflow_stats", data)
                self._log_operation("更新工作流Token统计", True, f"{stats.workflow_id}:{stats.model}")
                return True
            
            await asyncio.get_event_loop().run_in_executor(None, _update)
            return True
            
        except Exception as e:
            self._handle_exception("更新工作流Token统计", e)
            return False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            def _get_stats():
                from ..utils import SQLiteUtils
                
                # 总记录数
                total_records = SQLiteUtils.count_records(self.db_path, "history_records")
                
                # 按类型统计
                type_stats = SQLiteUtils.get_top_records(
                    self.db_path, "history_records", "record_type", "COUNT(*)", 10
                )
                
                # 按模型统计
                model_stats = SQLiteUtils.get_top_records(
                    self.db_path, "history_records", "model", "COUNT(*)", 10
                )
                
                # 按工作流统计
                workflow_stats = SQLiteUtils.get_top_records(
                    self.db_path, "history_records", "workflow_id", "COUNT(*)", 10
                )
                
                # 工作流统计数量
                stats_count = SQLiteUtils.count_records(self.db_path, "workflow_stats")
                
                # 数据库文件大小
                db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                
                return {
                    "total_records": total_records,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / 1024 / 1024, 2),
                    "record_types": {row[0]: row[1] for row in type_stats},
                    "models": {row[0]: row[1] for row in model_stats if row[0]},
                    "workflows": {row[0]: row[1] for row in workflow_stats if row[0]},
                    "workflow_stats_count": stats_count,
                    "database_path": str(self.db_path)
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
        """获取历史记录"""
        records = await self.get_records(session_id=thread_id, limit=limit)
        return [record.to_dict() for record in records]
    
    async def get_history_by_timerange(
        self,
        thread_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """按时间范围获取历史记录"""
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
    
    async def clear_thread_history(self, thread_id: str) -> bool:
        """清空线程的历史记录"""
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