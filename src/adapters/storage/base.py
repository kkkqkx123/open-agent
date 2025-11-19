"""存储适配器基类

提供存储适配器的通用基类实现，包含共同的代码段。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.state.interfaces import IStateStorageAdapter, IStorageBackend
from src.core.state.entities import StateSnapshot, StateHistoryEntry


logger = logging.getLogger(__name__)


class BaseStateStorageAdapter(IStateStorageAdapter):
    """状态存储适配器基类
    
    提供状态存储适配器的通用实现，包含共同的代码段。
    """
    
    def __init__(self, backend: IStorageBackend):
        """初始化基础状态存储适配器
        
        Args:
            backend: 存储后端实例
        """
        self._backend = backend
        self._transaction_active = False
    
    def _run_async_method(self, method, *args, **kwargs):
        """运行异步方法的辅助函数
        
        Args:
            method: 异步方法
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            方法执行结果
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在事件循环中，创建新的任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, method(*args, **kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(method(*args, **kwargs))
        except Exception as e:
            logger.error(f"Failed to run async method {method.__name__}: {e}")
            raise
    
    def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """保存历史记录条目"""
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
        """获取历史记录条目"""
        try:
            filters = {"type": "history_entry", "agent_id": agent_id}
            
            # 运行异步方法
            results = self._run_async_method(self._backend.list_impl, filters, limit)
            
            # 转换为历史记录条目
            entries = []
            for data in results:
                entry = StateHistoryEntry.from_dict(data)
                entries.append(entry)
            
            return entries
        except Exception as e:
            logger.error(f"Failed to get history entries: {e}")
            return []
    
    def delete_history_entry(self, history_id: str) -> bool:
        """删除历史记录条目"""
        try:
            # 运行异步方法
            result = self._run_async_method(self._backend.delete_impl, history_id)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete history entry: {e}")
            return False
    
    def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            # 获取所有历史记录
            entries = self.get_history_entries(agent_id, limit=10000)  # 大限制获取所有
            
            # 删除所有历史记录
            success = True
            for entry in entries:
                if not self.delete_history_entry(entry.history_id):
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Failed to clear agent history: {e}")
            return False
    
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存状态快照"""
        try:
            # 转换为字典格式
            data = snapshot.to_dict()
            data["type"] = "snapshot"
            
            # 运行异步方法
            result = self._run_async_method(self._backend.save_impl, data)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False
    
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载状态快照"""
        try:
            # 运行异步方法
            data = self._run_async_method(self._backend.load_impl, snapshot_id)
            
            if data is None:
                return None
            
            # 转换为快照对象
            return StateSnapshot.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None
    
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定代理的快照列表"""
        try:
            filters = {"type": "snapshot", "agent_id": agent_id}
            
            # 运行异步方法
            results = self._run_async_method(self._backend.list_impl, filters, limit)
            
            # 转换为快照对象
            snapshots = []
            for data in results:
                snapshot = StateSnapshot.from_dict(data)
                snapshots.append(snapshot)
            
            return snapshots
        except Exception as e:
            logger.error(f"Failed to get snapshots by agent: {e}")
            return []
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除状态快照"""
        try:
            # 运行异步方法
            result = self._run_async_method(self._backend.delete_impl, snapshot_id)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return False
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            # 运行异步方法
            count = self._run_async_method(self._backend.count_impl, {"type": "history_entry"})
            
            return {
                "total_entries": count,
                "storage_type": self.__class__.__name__.replace("StateStorageAdapter", "").lower()
            }
        except Exception as e:
            logger.error(f"Failed to get history statistics: {e}")
            return {"total_entries": 0, "storage_type": "unknown"}
    
    def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            # 运行异步方法
            count = self._run_async_method(self._backend.count_impl, {"type": "snapshot"})
            
            return {
                "total_snapshots": count,
                "storage_type": self.__class__.__name__.replace("StateStorageAdapter", "").lower()
            }
        except Exception as e:
            logger.error(f"Failed to get snapshot statistics: {e}")
            return {"total_snapshots": 0, "storage_type": "unknown"}
    
    def begin_transaction(self) -> None:
        """开始事务"""
        try:
            self._transaction_active = True
            # 运行异步方法
            self._run_async_method(self._backend.begin_transaction)
        except Exception as e:
            logger.error(f"Failed to begin transaction: {e}")
            self._transaction_active = False
            raise
    
    def commit_transaction(self) -> None:
        """提交事务"""
        try:
            if not self._transaction_active:
                return
            
            # 运行异步方法
            self._run_async_method(self._backend.commit_transaction)
            self._transaction_active = False
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            self._transaction_active = False
            raise
    
    def rollback_transaction(self) -> None:
        """回滚事务"""
        try:
            if not self._transaction_active:
                return
            
            # 运行异步方法
            self._run_async_method(self._backend.rollback_transaction)
            self._transaction_active = False
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            self._transaction_active = False
    
    def close(self) -> None:
        """关闭存储连接"""
        try:
            # 运行异步方法
            self._run_async_method(self._backend.disconnect)
        except Exception as e:
            logger.error(f"Failed to close storage: {e}")
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 运行异步方法
            health_info = self._run_async_method(self._backend.health_check_impl)
            return health_info.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Failed health check: {e}")
            return False


class BaseStorageBackend(IStorageBackend):
    """存储后端基类
    
    提供存储后端的通用实现，包含共同的代码段。
    """
    
    def __init__(self, **config: Any):
        """初始化基础存储后端
        
        Args:
            **config: 配置参数
        """
        self._connected = False
        self._config = config
        self._stats: Dict[str, Any] = {
            "total_operations": 0,
            "save_operations": 0,
            "load_operations": 0,
            "update_operations": 0,
            "delete_operations": 0,
            "list_operations": 0,
            "query_operations": 0,
            "transaction_operations": 0,
        }
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def _update_stats(self, operation: str) -> None:
        """更新统计信息"""
        self._stats["total_operations"] += 1
        if f"{operation}_operations" in self._stats:
            self._stats[f"{operation}_operations"] += 1
    
    def _matches_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in data:
                return False
            
            if isinstance(value, dict):
                # 支持操作符
                if "$eq" in value and data[key] != value["$eq"]:
                    return False
                elif "$ne" in value and data[key] == value["$ne"]:
                    return False
                elif "$in" in value and data[key] not in value["$in"]:
                    return False
                elif "$nin" in value and data[key] in value["$nin"]:
                    return False
                elif "$gt" in value and data[key] <= value["$gt"]:
                    return False
                elif "$gte" in value and data[key] < value["$gte"]:
                    return False
                elif "$lt" in value and data[key] >= value["$lt"]:
                    return False
                elif "$lte" in value and data[key] > value["$lte"]:
                    return False
            elif data[key] != value:
                return False
        
        return True
    
    async def begin_transaction(self) -> None:
        """开始事务"""
        # 默认实现：简单标记事务开始
        pass
    
    async def commit_transaction(self) -> None:
        """提交事务"""
        # 默认实现：简单标记事务提交
        pass
    
    async def rollback_transaction(self) -> None:
        """回滚事务"""
        # 默认实现：简单标记事务回滚
        pass
    
    async def get_by_session_impl(self, session_id: str) -> List[Dict[str, Any]]:
        """实际根据会话ID获取数据实现"""
        filters = {"session_id": session_id}
        return await self.list_impl(filters)
    
    async def get_by_thread_impl(self, thread_id: str) -> List[Dict[str, Any]]:
        """实际根据线程ID获取数据实现"""
        filters = {"thread_id": thread_id}
        return await self.list_impl(filters)