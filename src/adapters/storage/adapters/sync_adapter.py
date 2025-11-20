"""同步状态存储适配器

提供纯同步的状态存储适配器实现。
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

from src.interfaces.state.storage.adapter import IStateStorageAdapter
from src.interfaces.state.entities import StateSnapshot, StateHistoryEntry
from ..core.metrics import StorageMetrics, MetricsContext
from ..core.transaction import TransactionManager, transaction_context
from ..core.error_handler import with_error_handling

logger = logging.getLogger(__name__)


class SyncStateStorageAdapter(IStateStorageAdapter):
    """纯同步状态存储适配器
    
    实现状态存储的同步接口，专注于存储逻辑。
    """
    
    def __init__(self, 
                 backend: Any,  # 同步存储后端
                 metrics: Optional[StorageMetrics] = None,
                 transaction_manager: Optional[TransactionManager] = None):
        """初始化同步状态存储适配器
        
        Args:
            backend: 存储后端
            metrics: 指标收集器
            transaction_manager: 事务管理器
        """
        self._backend = backend
        self._metrics = metrics or StorageMetrics()
        self._transaction_manager = transaction_manager
    
    @with_error_handling("save_history_entry")
    def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """同步保存历史记录条目
        
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
            result = self._backend.save_impl(data)
            return bool(result)
    
    @with_error_handling("get_history_entries")
    def get_history_entries(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """同步获取历史记录条目
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            历史记录条目列表
        """
        with MetricsContext(self._metrics, "get_history_entries"):
            filters = {"type": "history_entry", "agent_id": agent_id}
            
            # 获取数据
            results = self._backend.list_impl(filters, limit)
            
            # 转换为历史记录条目
            entries = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
    
    @with_error_handling("delete_history_entry")
    def delete_history_entry(self, history_id: str) -> bool:
        """同步删除历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        with MetricsContext(self._metrics, "delete_history_entry"):
            result = self._backend.delete_impl(history_id)
            return bool(result)
    
    @with_error_handling("clear_agent_history")
    def clear_agent_history(self, agent_id: str) -> bool:
        """同步清空代理的历史记录
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否清空成功
        """
        with MetricsContext(self._metrics, "clear_agent_history"):
            # 获取所有历史记录
            entries = self.get_history_entries(agent_id, limit=10000)  # 大限制获取所有
            
            # 删除所有历史记录
            success = True
            for entry in entries:
                if not self.delete_history_entry(entry.history_id):
                    success = False
            
            return success
    
    @with_error_handling("save_snapshot")
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """同步保存状态快照
        
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
            result = self._backend.save_impl(data)
            return bool(result)
    
    @with_error_handling("load_snapshot")
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """同步加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果不存在则返回None
        """
        with MetricsContext(self._metrics, "load_snapshot"):
            # 加载数据
            data = self._backend.load_impl(snapshot_id)
            
            if data is None:
                return None
            
            # 转换为快照对象
            return StateSnapshot.from_dict(data)
    
    @with_error_handling("get_snapshots_by_agent")
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """同步获取指定代理的快照列表
        
        Args:
            agent_id: 代理ID
            limit: 返回快照数限制
            
        Returns:
            快照列表
        """
        with MetricsContext(self._metrics, "get_snapshots_by_agent"):
            filters = {"type": "snapshot", "agent_id": agent_id}
            
            # 获取数据
            results = self._backend.list_impl(filters, limit)
            
            # 转换为快照对象
            snapshots = []
            for data in results:
                snapshot = StateSnapshot.from_dict(data)
                snapshots.append(snapshot)
            
            return snapshots
    
    @with_error_handling("delete_snapshot")
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """同步删除状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否删除成功
        """
        with MetricsContext(self._metrics, "delete_snapshot"):
            result = self._backend.delete_impl(snapshot_id)
            return bool(result)
    
    @with_error_handling("get_history_statistics")
    def get_history_statistics(self) -> Dict[str, Any]:
        """同步获取历史记录统计信息
        
        Returns:
            统计信息字典
        """
        with MetricsContext(self._metrics, "get_history_statistics"):
            # 获取计数
            count = self._backend.count_impl({"type": "history_entry"})
            
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
    def get_snapshot_statistics(self) -> Dict[str, Any]:
        """同步获取快照统计信息
        
        Returns:
            统计信息字典
        """
        with MetricsContext(self._metrics, "get_snapshot_statistics"):
            # 获取计数
            count = self._backend.count_impl({"type": "snapshot"})
            
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
    def begin_transaction(self) -> None:
        """同步开始事务"""
        if self._transaction_manager:
            # 使用同步上下文管理器
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在事件循环中，使用线程池
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._transaction_manager.begin_transaction())
                        future.result()
                else:
                    asyncio.run(self._transaction_manager.begin_transaction())
            except Exception as e:
                logger.error(f"Failed to begin transaction: {e}")
                raise
    
    @with_error_handling("commit_transaction")
    def commit_transaction(self) -> None:
        """同步提交事务"""
        if self._transaction_manager:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在事件循环中，使用线程池
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._transaction_manager.commit_transaction())
                        future.result()
                else:
                    asyncio.run(self._transaction_manager.commit_transaction())
            except Exception as e:
                logger.error(f"Failed to commit transaction: {e}")
                raise
    
    @with_error_handling("rollback_transaction")
    def rollback_transaction(self) -> None:
        """同步回滚事务"""
        if self._transaction_manager:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在事件循环中，使用线程池
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._transaction_manager.rollback_transaction())
                        future.result()
                else:
                    asyncio.run(self._transaction_manager.rollback_transaction())
            except Exception as e:
                logger.error(f"Failed to rollback transaction: {e}")
                raise
    
    @with_error_handling("close")
    def close(self) -> None:
        """同步关闭存储连接"""
        if hasattr(self._backend, 'disconnect'):
            if asyncio.iscoroutinefunction(self._backend.disconnect):
                # 如果是异步方法，需要特殊处理
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果已经在事件循环中，使用线程池
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self._backend.disconnect())
                            future.result()
                    else:
                        asyncio.run(self._backend.disconnect())
                except Exception as e:
                    logger.error(f"Failed to close storage: {e}")
            else:
                # 同步方法，直接调用
                self._backend.disconnect()
    
    @with_error_handling("health_check")
    def health_check(self) -> bool:
        """同步健康检查
        
        Returns:
            存储是否健康
        """
        try:
            # 获取健康检查信息
            if hasattr(self._backend, 'health_check_impl'):
                if asyncio.iscoroutinefunction(self._backend.health_check_impl):
                    # 如果是异步方法，需要特殊处理
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 如果已经在事件循环中，使用线程池
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, self._backend.health_check_impl())
                                health_info = future.result()
                        else:
                            health_info = asyncio.run(self._backend.health_check_impl())
                    except Exception as e:
                        logger.error(f"Health check failed: {e}")
                        return False
                else:
                    # 同步方法，直接调用
                    health_info = self._backend.health_check_impl()
            else:
                return True
            
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
        if self._transaction_manager:
            return self._transaction_manager.is_transaction_active()
        return False
    
    def get_active_transactions(self) -> List[str]:
        """获取活跃事务列表
        
        Returns:
            活跃事务ID列表
        """
        if self._transaction_manager:
            return self._transaction_manager.get_active_transactions()
        return []
    
    def transaction_context(self):
        """获取事务上下文管理器
        
        Returns:
            事务上下文管理器
        """
        if self._transaction_manager:
            return transaction_context(self._transaction_manager)
        else:
            # 如果没有事务管理器，返回空的上下文管理器
            from contextlib import nullcontext
            return nullcontext()

    @property
    def _backend(self) -> Any:
        """获取存储后端"""
        return self.__backend

    @_backend.setter
    def _backend(self, value: Any) -> None:
        """设置存储后端"""
        self.__backend = value

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """备份数据库
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        # 默认实现：不支持备份
        logger.warning("backup_database not implemented for this adapter type")
        return ""

    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        # 默认实现：不支持恢复
        logger.warning("restore_database not implemented for this adapter type")
        return False

    def backup_storage(self, backup_path: Optional[str] = None) -> str:
        """备份存储
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        # 默认实现：不支持备份
        logger.warning("backup_storage not implemented for this adapter type")
        return ""

    def restore_storage(self, backup_path: str) -> bool:
        """恢复存储
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        # 默认实现：不支持恢复
        logger.warning("restore_storage not implemented for this adapter type")
        return False