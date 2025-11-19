"""SQLite存储适配器

提供基于SQLite的状态存储适配器实现。
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from src.core.state.entities import StateSnapshot, StateHistoryEntry
from src.core.state.exceptions import StorageError
from .base import BaseStateStorageAdapter
from .sqlite_backend import SQLiteStorageBackend
from .utils.sqlite_utils import SQLiteStorageUtils


logger = logging.getLogger(__name__)


class SQLiteStateStorageAdapter(BaseStateStorageAdapter):
    """SQLite状态存储适配器
    
    提供基于SQLite的状态存储适配器实现。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化SQLite状态存储适配器
        
        Args:
            **config: 配置参数
        """
        # 创建SQLite存储后端
        backend = SQLiteStorageBackend(**config)
        
        # 初始化基类
        super().__init__(backend)
        
        # 存储配置
        self._config = config
        
        logger.info("SQLiteStateStorageAdapter initialized")
    
    def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """保存历史记录条目
        
        Args:
            entry: 历史记录条目
            
        Returns:
            是否保存成功
        """
        try:
            # 转换为字典格式
            data = entry.to_dict()
            data["type"] = "history_entry"
            
            # 运行异步方法
            result = self._run_async_method(self._backend.save_impl, data)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to save history entry: {e}")
            return False
    
    def get_history_entries(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取指定代理的历史记录条目
        
        Args:
            agent_id: 代理ID
            limit: 返回条目数量限制
            
        Returns:
            历史记录条目列表
        """
        try:
            filters = {"type": "history_entry", "agent_id": agent_id}
            
            # 运行异步方法
            results = self._run_async_method(self._backend.list_impl, filters, limit)
            
            # 转换为历史记录条目对象
            entries = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get history entries: {e}")
            return []
    
    def get_history_entry(self, history_id: str) -> Optional[StateHistoryEntry]:
        """获取指定ID的历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            历史记录条目对象或None
        """
        try:
            # 运行异步方法
            data = self._run_async_method(self._backend.load_impl, history_id)
            
            if data is None:
                return None
            
            # 转换为历史记录条目对象
            return StateHistoryEntry.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to get history entry: {e}")
            return None
    
    def update_history_entry(self, history_id: str, updates: Dict[str, Any]) -> bool:
        """更新历史记录条目
        
        Args:
            history_id: 历史记录ID
            updates: 更新数据
            
        Returns:
            是否更新成功
        """
        try:
            # 运行异步方法
            result = self._run_async_method(self._backend.update_impl, history_id, updates)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to update history entry: {e}")
            return False
    
    def delete_history_entry(self, history_id: str) -> bool:
        """删除历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        try:
            # 运行异步方法
            result = self._run_async_method(self._backend.delete_impl, history_id)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete history entry: {e}")
            return False
    
    def get_history_entries_by_session(
        self, 
        session_id: str, 
        limit: int = 100
    ) -> List[StateHistoryEntry]:
        """获取指定会话的历史记录条目
        
        Args:
            session_id: 会话ID
            limit: 返回条目数量限制
            
        Returns:
            历史记录条目列表
        """
        try:
            filters = {"type": "history_entry", "session_id": session_id}
            
            # 运行异步方法
            results = self._run_async_method(self._backend.list_impl, filters, limit)
            
            # 转换为历史记录条目对象
            entries = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get history entries by session: {e}")
            return []
    
    def get_history_entries_by_thread(
        self, 
        thread_id: str, 
        limit: int = 100
    ) -> List[StateHistoryEntry]:
        """获取指定线程的历史记录条目
        
        Args:
            thread_id: 线程ID
            limit: 返回条目数量限制
            
        Returns:
            历史记录条目列表
        """
        try:
            filters = {"type": "history_entry", "thread_id": thread_id}
            
            # 运行异步方法
            results = self._run_async_method(self._backend.list_impl, filters, limit)
            
            # 转换为历史记录条目对象
            entries = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get history entries by thread: {e}")
            return []
    
    def get_history_entries_by_time_range(
        self, 
        start_time: float, 
        end_time: float, 
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[StateHistoryEntry]:
        """获取指定时间范围的历史记录条目
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            agent_id: 代理ID（可选）
            limit: 返回条目数量限制
            
        Returns:
            历史记录条目列表
        """
        try:
            filters = {
                "type": "history_entry",
                "created_at": {"$gte": start_time, "$lte": end_time}
            }
            
            if agent_id:
                filters["agent_id"] = agent_id
            
            # 运行异步方法
            results = self._run_async_method(self._backend.list_impl, filters, limit)
            
            # 转换为历史记录条目对象
            entries = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get history entries by time range: {e}")
            return []
    
    def search_history_entries(
        self, 
        query: str, 
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[StateHistoryEntry]:
        """搜索历史记录条目
        
        Args:
            query: 搜索查询
            agent_id: 代理ID（可选）
            limit: 返回条目数量限制
            
        Returns:
            历史记录条目列表
        """
        try:
            # 使用SQL查询进行搜索
            sql_query = """
                SELECT * FROM state_storage 
                WHERE type = 'history_entry' 
                AND (data LIKE ? OR metadata LIKE ?)
            """
            
            params = [f"%{query}%", f"%{query}%"]
            
            if agent_id:
                sql_query += " AND agent_id = ?"
                params.append(agent_id)
            
            sql_query += " ORDER BY created_at DESC"
            
            # 运行异步方法
            results = self._run_async_method(
                self._backend.query_impl,
                f"sql:{sql_query}",
                {"params": params, "limit": limit}
            )
            
            # 运行异步方法
            results = self._run_async_method(
                self._backend.query_impl, 
                f"sql:{sql_query}", 
                {"params": params}
            )
            
            # 转换为历史记录条目对象
            entries = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to search history entries: {e}")
            return []
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 运行异步方法
            count = self._run_async_method(self._backend.count_impl, {"type": "history_entry"})
            
            # 获取数据库信息
            health_info = self._run_async_method(self._backend.health_check_impl)
            
            return {
                "total_entries": count,
                "storage_type": "sqlite",
                "database_size_bytes": health_info.get("database_size_bytes", 0),
                "database_size_mb": health_info.get("database_size_mb", 0),
                "connection_pool_size": health_info.get("connection_pool_size", 0),
                "active_connections": health_info.get("active_connections", 0),
                "expired_records_cleaned": health_info.get("expired_records_cleaned", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get history statistics: {e}")
            return {"total_entries": 0, "storage_type": "sqlite"}
    
    def cleanup_old_history(self, retention_days: int) -> int:
        """清理旧的历史记录
        
        Args:
            retention_days: 保留天数
            
        Returns:
            清理的记录数
        """
        try:
            # 运行异步方法
            count = self._run_async_method(self._backend.cleanup_old_data_impl, retention_days)
            if isinstance(count, int):
                return count
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup old history: {e}")
            return 0
    
    def export_history(
        self, 
        agent_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        format: str = "json"
    ) -> str:
        """导出历史记录
        
        Args:
            agent_id: 代理ID（可选）
            start_time: 开始时间戳（可选）
            end_time: 结束时间戳（可选）
            format: 导出格式（json, csv）
            
        Returns:
            导出数据路径
        """
        try:
            # 构建过滤器
            filters = {"type": "history_entry"}
            
            if agent_id:
                filters["agent_id"] = agent_id
            
            if start_time is not None:
                filters["created_at"] = str({"$gte": start_time})
                if end_time is not None:
                    filters["created_at"] = str({"$gte": start_time, "$lte": end_time})
            elif end_time is not None:
                filters["created_at"] = str({"$lte": end_time})
            
            # 获取历史记录
            entries = self._run_async_method(self._backend.list_impl, filters, limit=10000)
            
            # 导出数据
            import json
            import csv
            from pathlib import Path
            import time
            
            # 创建导出目录
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            # 生成导出文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            export_file = None
            
            if format.lower() == "json":
                export_file = export_dir / f"history_export_{timestamp}.json"
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(entries, f, ensure_ascii=False, indent=2)
                    
            elif format.lower() == "csv":
                export_file = export_dir / f"history_export_{timestamp}.csv"
                
                if entries:
                    with open(export_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                        writer.writeheader()
                        writer.writerows(entries)
            
            if export_file:
                logger.info(f"Exported {len(entries)} history entries to {export_file}")
                return str(export_file)
            else:
                logger.error("Failed to create export file")
                return ""
            
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return ""
    
    def import_history(self, file_path: str) -> int:
        """导入历史记录
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            导入的记录数
        """
        try:
            import json
            import csv
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"Import file not found: {file_path}")
                return 0
            
            # 读取数据
            entries = []
            
            if file_path_obj.suffix.lower() == '.json':
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
                    
            elif file_path_obj.suffix.lower() == '.csv':
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    entries = list(reader)
            
            # 导入数据
            imported_count = 0
            for entry_data in entries:
                try:
                    # 确保是历史记录条目
                    if entry_data.get("type") == "history_entry":
                        # 运行异步方法
                        result = self._run_async_method(self._backend.save_impl, entry_data)
                        if result:
                            imported_count += 1
                except Exception as e:
                    logger.error(f"Failed to import entry: {e}")
                    continue
            
            logger.info(f"Imported {imported_count} history entries from {file_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import history: {e}")
            return 0
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """备份数据库
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        try:
            from pathlib import Path
            import time
            
            # 如果未指定备份路径，使用默认路径
            if not backup_path:
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = str(backup_dir / f"storage_backup_{timestamp}.db")
            
            # 获取连接并创建备份
            # 获取连接并创建备份
            # 注意：这里需要通过后端的公共方法来操作，不能直接访问私有方法
            # 我们需要添加一个公共方法到后端来支持备份操作
            try:
                # 临时解决方案：直接使用工具类
                conn = SQLiteStorageUtils.create_connection(getattr(self._backend, 'db_path', 'storage.db'), getattr(self._backend, 'timeout', 30.0))
                try:
                    SQLiteStorageUtils.backup_database(conn, backup_path)
                    logger.info(f"Created backup: {backup_path}")
                    return backup_path
                finally:
                    conn.close()
            except Exception as e:
                logger.error(f"Failed to create backup connection: {e}")
                return ""
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return ""
    
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        try:
            # 断开当前连接
            self._run_async_method(self._backend.disconnect)
            
            # 恢复数据库
            SQLiteStorageUtils.restore_database(backup_path, getattr(self._backend, 'db_path', 'storage.db'))
            
            # 重新连接
            self._run_async_method(self._backend.connect)
            
            logger.info(f"Restored database from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """优化数据库
        
        Returns:
            是否优化成功
        """
        try:
            # 获取连接并优化
            # 使用公共方法而不是私有方法
            if hasattr(self._backend, '_get_connection') and hasattr(self._backend, '_return_connection'):
                conn = self._backend._get_connection()  # type: ignore
                try:
                    SQLiteStorageUtils.optimize_database(conn)
                    logger.info("Database optimized successfully")
                    return True
                finally:
                    self._backend._return_connection(conn)  # type: ignore
            else:
                logger.warning("Backend does not support connection management for optimization")
                return False
                
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return False