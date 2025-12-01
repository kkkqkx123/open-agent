"""状态存储适配器实现

提供纯异步的状态存储适配器实现。
"""

from src.services.logger import get_logger
from typing import Dict, Any, List, Optional, Sequence

from src.interfaces.state.storage.adapter import IStateStorageAdapter
# 修复循环导入：直接从核心模块导入具体实现，不再需要接口层抽象类
from src.core.state.entities import StateSnapshot, StateHistoryEntry
# from src.interfaces.state.entities import AbstractStateSnapshot, AbstractStateHistoryEntry
from src.interfaces.state.storage.backend import IStorageBackend
from ..core.metrics import StorageMetrics, MetricsContext
from ..core.transaction import TransactionManager, TransactionContext
from ..core.error_handler import with_error_handling

logger = get_logger(__name__)


class AsyncStateStorageAdapter(IStateStorageAdapter):
    """纯异步状态存储适配器
    
    实现状态存储的异步接口，专注于存储逻辑。
    """
    
    def __init__(self, 
                 backend: IStorageBackend, 
                 metrics: Optional[StorageMetrics] = None,
                 transaction_manager: Optional[TransactionManager] = None):
        """初始化异步状态存储适配器
        
        Args:
            backend: 存储后端
            metrics: 指标收集器
            transaction_manager: 事务管理器
        """
        self._backend = backend
        self._metrics = metrics or StorageMetrics()
        self._transaction_manager = transaction_manager or TransactionManager(backend)
    
    @with_error_handling("save_history_entry")
    async def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """异步保存历史记录条目
        
        Args:
            entry: 历史记录条目
            
        Returns:
            是否保存成功
        """
        with MetricsContext(self._metrics, "save_history_entry"):
            # 转换为字典格式
            data = entry.to_dict()
            data["type"] = "history_entry"
            
            # 保存数据
            result = await self._backend.save_impl(data)
            return bool(result)
    
    @with_error_handling("get_history_entries")
    async def get_history_entries(self, agent_id: str, limit: int = 100) -> Sequence[StateHistoryEntry]:
        """异步获取历史记录条目
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            历史记录条目列表
        """
        with MetricsContext(self._metrics, "get_history_entries"):
            filters = {"type": "history_entry", "agent_id": agent_id}
            
            # 获取数据
            results = await self._backend.list_impl(filters, limit)
            
            # 转换为历史记录条目
            entries: List[StateHistoryEntry] = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
    
    @with_error_handling("delete_history_entry")
    async def delete_history_entry(self, history_id: str) -> bool:
        """异步删除历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        with MetricsContext(self._metrics, "delete_history_entry"):
            result = await self._backend.delete_impl(history_id)
            return bool(result)
    
    @with_error_handling("clear_agent_history")
    async def clear_agent_history(self, agent_id: str) -> bool:
        """异步清空代理的历史记录
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否清空成功
        """
        with MetricsContext(self._metrics, "clear_agent_history"):
            # 获取所有历史记录
            entries = await self.get_history_entries(agent_id, limit=10000)  # 大限制获取所有
            
            # 删除所有历史记录
            success = True
            for entry in entries:
                if not await self.delete_history_entry(entry.history_id):
                    success = False
            
            return success
    
    @with_error_handling("save_snapshot")
    async def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """异步保存状态快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            是否保存成功
        """
        with MetricsContext(self._metrics, "save_snapshot"):
            # 转换为字典格式
            data = snapshot.to_dict()
            data["type"] = "snapshot"
            
            # 保存数据
            result = await self._backend.save_impl(data)
            return bool(result)
    
    @with_error_handling("load_snapshot")
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """异步加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果不存在则返回None
        """
        with MetricsContext(self._metrics, "load_snapshot"):
            # 加载数据
            data = await self._backend.load_impl(snapshot_id)
            
            if data is None:
                return None
            
            # 转换为快照对象
            return StateSnapshot.from_dict(data)
    
    @with_error_handling("get_snapshots_by_agent")
    async def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> Sequence[StateSnapshot]:
        """异步获取指定代理的快照列表
        
        Args:
            agent_id: 代理ID
            limit: 返回快照数限制
            
        Returns:
            快照列表
        """
        with MetricsContext(self._metrics, "get_snapshots_by_agent"):
            filters = {"type": "snapshot", "agent_id": agent_id}
            
            # 获取数据
            results = await self._backend.list_impl(filters, limit)
            
            # 转换为快照对象
            snapshots: List[StateSnapshot] = []
            for data in results:
                snapshot = StateSnapshot.from_dict(data)
                snapshots.append(snapshot)
            
            return snapshots
    
    @with_error_handling("delete_snapshot")
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """异步删除状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否删除成功
        """
        with MetricsContext(self._metrics, "delete_snapshot"):
            result = await self._backend.delete_impl(snapshot_id)
            return bool(result)
    
    @with_error_handling("get_history_statistics")
    async def get_history_statistics(self) -> Dict[str, Any]:
        """异步获取历史记录统计信息
        
        Returns:
            统计信息字典
        """
        with MetricsContext(self._metrics, "get_history_statistics"):
            # 获取计数
            count = await self._backend.count_impl({"type": "history_entry"})
            
            # 获取指标
            metrics_data = self._metrics.get_metrics()
            
            return {
                "total_entries": count,
                "storage_type": self.__class__.__name__.replace("StateStorageAdapter", "").lower(),
                "operations": metrics_data.get("operation_counts", {}),
                "average_times": metrics_data.get("average_times", {}),
                "error_rates": metrics_data.get("error_rates", {})
            }
    
    @with_error_handling("get_snapshot_statistics")
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """异步获取快照统计信息
        
        Returns:
            统计信息字典
        """
        with MetricsContext(self._metrics, "get_snapshot_statistics"):
            # 获取计数
            count = await self._backend.count_impl({"type": "snapshot"})
            
            # 获取指标
            metrics_data = self._metrics.get_metrics()
            
            return {
                "total_snapshots": count,
                "storage_type": self.__class__.__name__.replace("StateStorageAdapter", "").lower(),
                "operations": metrics_data.get("operation_counts", {}),
                "average_times": metrics_data.get("average_times", {}),
                "error_rates": metrics_data.get("error_rates", {})
            }
    
    @with_error_handling("begin_transaction")
    async def begin_transaction(self) -> None:
        """异步开始事务"""
        await self._transaction_manager.begin_transaction()
    
    @with_error_handling("commit_transaction")
    async def commit_transaction(self) -> None:
        """异步提交事务"""
        await self._transaction_manager.commit_transaction()
    
    @with_error_handling("rollback_transaction")
    async def rollback_transaction(self) -> None:
        """异步回滚事务"""
        await self._transaction_manager.rollback_transaction()
    
    @with_error_handling("close")
    async def close(self) -> None:
        """异步关闭存储连接"""
        await self._backend.disconnect()
    
    @with_error_handling("health_check")
    async def health_check(self) -> bool:
        """异步健康检查
        
        Returns:
            存储是否健康
        """
        try:
            # 获取健康检查信息
            health_info = await self._backend.health_check_impl()
            if isinstance(health_info, dict):
                return health_info.get("status") == "healthy"
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据
        
        Returns:
            指标数据字典
        """
        return self._metrics.get_metrics()
    
    def reset_metrics(self) -> None:
        """重置指标数据"""
        self._metrics.reset_metrics()
    
    def is_transaction_active(self) -> bool:
        """检查是否有活跃事务
        
        Returns:
            是否有活跃事务
        """
        return self._transaction_manager.is_transaction_active()
    
    def get_active_transactions(self) -> List[str]:
        """获取活跃事务列表
        
        Returns:
            活跃事务ID列表
        """
        return self._transaction_manager.get_active_transactions()
    
    def transaction_context(self) -> TransactionContext:
        """获取事务上下文管理器
        
        Returns:
            事务上下文管理器
        """
        return TransactionContext(self._transaction_manager)

    @property
    def _backend(self) -> IStorageBackend:
        """获取存储后端"""
        return self.__backend

    @_backend.setter
    def _backend(self, value: IStorageBackend) -> None:
        """设置存储后端"""
        self.__backend = value

    @with_error_handling("backup_database")
    async def backup_database(self, backup_path: Optional[str] = None) -> str:
        """备份数据库
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        # 默认实现：不支持备份
        logger.warning("backup_database not implemented for this adapter type")
        return ""

    @with_error_handling("restore_database")
    async def restore_database(self, backup_path: str) -> bool:
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        # 默认实现：不支持恢复
        logger.warning("restore_database not implemented for this adapter type")
        return False

    @with_error_handling("backup_storage")
    async def backup_storage(self, backup_path: Optional[str] = None) -> str:
        """备份存储
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        # 默认实现：不支持备份
        logger.warning("backup_storage not implemented for this adapter type")
        return ""

    @with_error_handling("restore_storage")
    async def restore_storage(self, backup_path: str) -> bool:
        """恢复存储
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        # 默认实现：不支持恢复
        logger.warning("restore_storage not implemented for this adapter type")
        return False