"""SQLite状态存储适配器

提供基于SQLite的异步状态存储适配器实现。
"""

from src.services.logger.injection import get_logger
from typing import Dict, Any

from src.interfaces.state.storage.adapter import IStateStorageAdapter
from ..backends.sqlite_backend import SQLiteStorageBackend
from ..core.metrics import StorageMetrics
from ..core.transaction import TransactionManager

logger = get_logger(__name__)


class SQLiteStateStorageAdapter(IStateStorageAdapter):
    """SQLite状态存储适配器
    
    提供基于SQLite的异步状态存储功能。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化SQLite状态存储适配器
        
        Args:
            **config: 配置参数，包括：
                - db_path: 数据库文件路径
                - connection_pool_size: 连接池大小 (默认5)
                - timeout: 连接超时时间 (默认30秒)
                - enable_wal_mode: 是否启用WAL模式 (默认True)
                - 其他SQLite配置参数
        """
        # 创建SQLite后端
        self._sqlite_backend = SQLiteStorageBackend(**config)
        
        # 创建指标收集器
        self._metrics = StorageMetrics()
        
        # 创建事务管理器
        self._transaction_manager = TransactionManager(self._sqlite_backend)
        
        logger.info(f"SQLiteStateStorageAdapter initialized with db_path: {config.get('db_path', 'storage.db')}")
    
    async def save_history_entry(self, entry) -> bool:
        """保存历史记录条目"""
        from src.core.state.entities import StateHistoryEntry
        
        # 转换为字典格式
        data = entry.to_dict()
        data["type"] = "history_entry"
        
        # 保存数据
        result = await self._sqlite_backend.save_impl(data)
        return bool(result)
    
    async def get_history_entries(self, agent_id: str, limit: int = 100):
        """获取历史记录条目"""
        from src.core.state.entities import StateHistoryEntry
        
        filters = {"type": "history_entry", "agent_id": agent_id}
        
        # 获取数据
        results = await self._sqlite_backend.list_impl(filters, limit)
        
        # 转换为历史记录条目
        entries = []
        for data in results:
            entry = StateHistoryEntry.from_dict(data)
            entries.append(entry)
        
        return entries
    
    async def delete_history_entry(self, history_id: str) -> bool:
        """删除历史记录条目"""
        result = await self._sqlite_backend.delete_impl(history_id)
        return bool(result)
    
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        # 获取所有历史记录
        entries = await self.get_history_entries(agent_id, limit=10000)  # 大限制获取所有
        
        # 删除所有历史记录
        success = True
        for entry in entries:
            if not await self.delete_history_entry(entry.history_id):
                success = False
        
        return success
    
    async def save_snapshot(self, snapshot) -> bool:
        """保存状态快照"""
        from src.core.state.entities import StateSnapshot
        
        # 转换为字典格式
        data = snapshot.to_dict()
        data["type"] = "snapshot"
        
        # 保存数据
        result = await self._sqlite_backend.save_impl(data)
        return bool(result)
    
    async def load_snapshot(self, snapshot_id: str):
        """加载状态快照"""
        from src.core.state.entities import StateSnapshot
        
        # 加载数据
        data = await self._sqlite_backend.load_impl(snapshot_id)
        
        if data is None:
            return None
        
        # 转换为快照对象
        return StateSnapshot.from_dict(data)
    
    async def get_snapshots_by_agent(self, agent_id: str, limit: int = 50):
        """获取指定代理的快照列表"""
        from src.core.state.entities import StateSnapshot
        
        filters = {"type": "snapshot", "agent_id": agent_id}
        
        # 获取数据
        results = await self._sqlite_backend.list_impl(filters, limit)
        
        # 转换为快照对象
        snapshots = []
        for data in results:
            snapshot = StateSnapshot.from_dict(data)
            snapshots.append(snapshot)
        
        return snapshots
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除状态快照"""
        result = await self._sqlite_backend.delete_impl(snapshot_id)
        return bool(result)
    
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        # 获取计数
        count = await self._sqlite_backend.count_impl({"type": "history_entry"})
        
        # 获取指标
        metrics_data = self._metrics.get_metrics()
        
        return {
            "total_entries": count,
            "storage_type": "sqlite",
            "operations": metrics_data.get("operation_counts", {}),
            "average_times": metrics_data.get("average_times", {}),
            "error_rates": metrics_data.get("error_rates", {})
        }
    
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        # 获取计数
        count = await self._sqlite_backend.count_impl({"type": "snapshot"})
        
        # 获取指标
        metrics_data = self._metrics.get_metrics()
        
        return {
            "total_snapshots": count,
            "storage_type": "sqlite",
            "operations": metrics_data.get("operation_counts", {}),
            "average_times": metrics_data.get("average_times", {}),
            "error_rates": metrics_data.get("error_rates", {})
        }
    
    async def begin_transaction(self) -> None:
        """开始事务"""
        await self._transaction_manager.begin_transaction()
    
    async def commit_transaction(self) -> None:
        """提交事务"""
        await self._transaction_manager.commit_transaction()
    
    async def rollback_transaction(self) -> None:
        """回滚事务"""
        await self._transaction_manager.rollback_transaction()
    
    async def close(self) -> None:
        """关闭存储连接"""
        await self._sqlite_backend.disconnect()
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 获取健康检查信息
            health_info = await self._sqlite_backend.health_check_impl()
            if isinstance(health_info, dict):
                return health_info.get("status") == "healthy"
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据"""
        return self._metrics.get_metrics()
    
    def reset_metrics(self) -> None:
        """重置指标数据"""
        self._metrics.reset_metrics()
    
    def is_transaction_active(self) -> bool:
        """检查是否有活跃事务"""
        return self._transaction_manager.is_transaction_active()
    
    def get_active_transactions(self) -> list:
        """获取活跃事务列表"""
        return self._transaction_manager.get_active_transactions()
    
    def transaction_context(self):
        """获取事务上下文管理器"""
        from ..core.transaction import TransactionContext
        return TransactionContext(self._transaction_manager)

    @property
    def _backend(self):
        """获取存储后端"""
        return self._sqlite_backend

    @_backend.setter
    def _backend(self, value):
        """设置存储后端"""
        self._sqlite_backend = value

    async def backup_database(self, backup_path: str | None = None) -> str:
        """备份数据库"""
        if backup_path is None:
            import time
            from pathlib import Path
            
            # 生成默认备份路径
            backup_dir = Path("backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = str(backup_dir / f"sqlite_backup_{timestamp}.db")
        
        try:
            # 确保备份目录存在
            from pathlib import Path
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 获取连接并创建备份
            conn = self._sqlite_backend._get_connection()
            try:
                backup_conn = self._sqlite_backend._create_connection()
                conn.backup(backup_conn)
                backup_conn.close()
                
                logger.info(f"Created SQLite backup: {backup_path}")
                return backup_path
            finally:
                self._sqlite_backend._return_connection(conn)
                
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return ""

    async def restore_database(self, backup_path: str) -> bool:
        """恢复数据库"""
        try:
            from pathlib import Path
            import shutil
            
            if not Path(backup_path).exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # 关闭当前连接
            await self._sqlite_backend.disconnect()
            
            # 复制备份文件到数据库路径
            shutil.copy2(backup_path, self._sqlite_backend.db_path)
            
            # 重新连接
            await self._sqlite_backend.connect()
            
            logger.info(f"Restored SQLite database from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False

    async def backup_storage(self, backup_path: str | None = None) -> str:
        """备份存储（与数据库备份相同）"""
        return await self.backup_database(backup_path)

    async def restore_storage(self, backup_path: str) -> bool:
        """恢复存储（与数据库恢复相同）"""
        return await self.restore_database(backup_path)