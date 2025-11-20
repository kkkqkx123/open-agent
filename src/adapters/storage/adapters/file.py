"""文件存储适配器

提供基于文件的状态存储适配器实现。
"""

import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.core.state.entities import StateSnapshot, StateHistoryEntry
from src.core.state.exceptions import StorageError
from .sync_adapter import SyncStateStorageAdapter
from ..backends.file_backend import FileStorageBackend
from ..core.metrics import StorageMetrics
from ..core.transaction import TransactionManager
from ..utils.file_utils import FileStorageUtils


logger = logging.getLogger(__name__)


class FileStateStorageAdapter(SyncStateStorageAdapter):
    """文件状态存储适配器
    
    提供基于文件的状态存储适配器实现。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化文件状态存储适配器
        
        Args:
            **config: 配置参数
        """
        # 创建文件存储后端
        backend = FileStorageBackend(**config)
        
        # 创建指标收集器
        metrics = StorageMetrics()
        
        # 创建事务管理器
        transaction_manager = TransactionManager(backend)
        
        # 初始化基类
        super().__init__(
            backend=backend,
            metrics=metrics,
            transaction_manager=transaction_manager
        )
        
        # 存储配置
        self._config = config
        
        logger.info("FileStateStorageAdapter initialized")
    
    def get_history_entry(self, history_id: str) -> Optional[StateHistoryEntry]:
        """获取指定ID的历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            历史记录条目对象或None
        """
        try:
            # 使用基类的 load_snapshot 方法，但需要适配历史记录
            data = self._backend.load_impl(history_id)
            
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
            # 使用后端的更新方法
            result = self._backend.update_impl(history_id, updates)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to update history entry: {e}")
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
            
            # 使用后端的列表方法
            results = self._backend.list_impl(filters, limit)
            
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
            
            # 使用后端的列表方法
            results = self._backend.list_impl(filters, limit)
            
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
            
            # 使用后端的列表方法
            results = self._backend.list_impl(filters, limit)
            
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
            # 使用文件路径查询进行搜索
            # 由于文件存储不支持复杂的文本搜索，我们使用简单的过滤器
            filters = {"type": "history_entry"}
            
            # 获取更多结果进行过滤
            results = self._backend.list_impl(filters, limit=1000)
            
            # 手动过滤包含查询字符串的结果
            filtered_results = []
            for data in results:
                # 检查是否包含查询字符串
                data_str = str(data).lower()
                if query.lower() in data_str:
                    filtered_results.append(data)
                    
                    # 检查限制
                    if len(filtered_results) >= limit:
                        break
            
            # 转换为历史记录条目对象
            entries = []
            for data in filtered_results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to search history entries: {e}")
            return []
    
    def cleanup_old_history(self, retention_days: int) -> int:
        """清理旧的历史记录
        
        Args:
            retention_days: 保留天数
            
        Returns:
            清理的记录数
        """
        try:
            count = self._backend.cleanup_old_data_impl(retention_days)
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
            filters: Dict[str, Any] = {"type": "history_entry"}
            
            if agent_id:
                filters["agent_id"] = agent_id
            
            if start_time is not None:
                created_at_filter: Dict[str, Any] = {"$gte": start_time}
                if end_time is not None:
                    created_at_filter["$lte"] = end_time
                filters["created_at"] = created_at_filter
            elif end_time is not None:
                filters["created_at"] = {"$lte": end_time}
            
            # 获取历史记录
            entries = self._backend.list_impl(filters, limit=10000)
            
            # 导出数据
            import json
            import csv
            
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
            
            if export_file and export_file.exists():
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
                        result = self._backend.save_impl(entry_data)
                        if result:
                            imported_count += 1
                except Exception as e:
                    logger.error(f"Failed to import entry: {e}")
                    continue
            
            logger.info(f"Imported {imported_count} history entries from {file_path_obj}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import history: {e}")
            return 0
    
    def backup_storage(self, backup_path: Optional[str] = None) -> str:
        """备份存储
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        try:
            from src.core.state.backup_policy import FileBackupStrategy
            
            # 如果未指定备份路径，使用默认路径
            if not backup_path:
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = str(backup_dir / f"storage_backup_{timestamp}")
            
            # 获取基础路径
            base_path = getattr(self._backend, 'base_path', 'file_storage')
            
            # 备份目录
            backup_strategy = FileBackupStrategy()
            success = backup_strategy.backup(base_path, backup_path)
            
            if success:
                logger.info(f"Created backup: {backup_path}")
                return backup_path
            else:
                logger.error("Failed to create backup")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to backup storage: {e}")
            return ""
    
    def restore_storage(self, backup_path: str) -> bool:
        """恢复存储
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        try:
            from src.core.state.backup_policy import FileBackupStrategy
            
            # 断开当前连接
            if hasattr(self._backend, 'disconnect'):
                self._backend.disconnect()
            
            # 获取基础路径
            base_path = getattr(self._backend, 'base_path', 'file_storage')
            
            # 恢复存储
            backup_strategy = FileBackupStrategy()
            success = backup_strategy.restore(backup_path, base_path)
            
            # 重新连接
            if hasattr(self._backend, 'connect'):
                self._backend.connect()
            
            if success:
                logger.info(f"Restored storage from: {backup_path}")
                return True
            else:
                logger.error("Failed to restore storage")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore storage: {e}")
            return False
    
    def compact_storage(self) -> bool:
        """压缩存储
        
        Returns:
            是否压缩成功
        """
        try:
            # 文件存储的压缩主要是清理过期文件和重新组织目录结构
            # 这里我们简单地触发一次清理
            current_time = time.time()
            
            # 获取基础路径
            base_path = getattr(self._backend, 'base_path', 'file_storage')
            
            # 清理过期文件 - 获取所有文件并检查TTL
            expired_count = 0
            all_files = FileStorageUtils.list_files_in_directory(
                base_path,
                pattern="*.json",
                recursive=True
            )
            default_ttl = getattr(self._backend, 'default_ttl_seconds', 3600)
            for file_path in all_files:
                modified_time = FileStorageUtils.get_file_modified_time(file_path)
                if current_time - modified_time > default_ttl:
                    if FileStorageUtils.delete_file(file_path):
                        expired_count += 1
            
            logger.info(f"Compacted storage, cleaned up {expired_count} expired files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to compact storage: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息
        
        Returns:
            存储信息
        """
        try:
            # 获取基础路径
            base_path = getattr(self._backend, 'base_path', 'file_storage')
            
            # 获取存储信息 - 使用directory_structure_info
            dir_info = FileStorageUtils.get_directory_structure_info(
                base_path,
                getattr(self._backend, 'directory_structure', 'flat')
            )
            
            # 计算目录大小
            total_size = FileStorageUtils.calculate_directory_size(base_path)
            total_files = FileStorageUtils.count_files_in_directory(base_path)
            
            # 添加存储信息
            storage_info = {
                "storage_type": "file",
                "directory_structure": getattr(self._backend, 'directory_structure', 'flat'),
                "enable_compression": getattr(self._backend, 'enable_compression', False),
                "enable_ttl": getattr(self._backend, 'enable_ttl', False),
                "enable_backup": getattr(self._backend, 'enable_backup', False),
                "base_path": base_path,
                "directory_exists": dir_info.get("directory_exists", False),
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }
            
            # 合并目录信息
            storage_info.update(dir_info)
            
            return storage_info
            
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {"storage_type": "file", "error": str(e)}