"""SQLite存储后端实现

通过组合SQLite提供者和业务逻辑混入来创建具体的SQLite存储后端。
"""

from typing import Dict, Any, Optional, List
from src.services.logger.injection import get_logger

from ..core.base_backend import BaseStorageBackend
from ..core.mixins import SessionStorageMixin, ThreadStorageMixin
from ..providers.sqlite_provider import SQLiteProvider
from src.interfaces.storage import ISessionStorage, IThreadStorage
from ..core.exceptions import StorageBackendError


logger = get_logger(__name__)


class SQLiteSessionBackend(BaseStorageBackend, ISessionStorage):
    """SQLite会话存储后端
    
    通过组合SQLite提供者和会话存储混入来实现。
    """
    
    def __init__(self, db_path: str = "./data/sessions.db", **config: Any) -> None:
        """初始化SQLite会话后端
        
        Args:
            db_path: 数据库文件路径
            **config: 其他配置参数
        """
        super().__init__(db_path=db_path, **config)
        
        # 创建SQLite提供者
        self._provider = SQLiteProvider(db_path=db_path, **config)
        
        # 创建会话存储混入
        self._session_mixin = SessionStorageMixin(self._provider)
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # 连接到SQLite提供者
        await self._provider.connect()
        
        # 创建会话表
        session_schema = {
            "columns": {
                "id": {"type": "TEXT", "constraints": "PRIMARY KEY"},
                "status": {"type": "TEXT", "constraints": "NOT NULL"},
                "message_count": {"type": "INTEGER", "constraints": "DEFAULT 0"},
                "checkpoint_count": {"type": "INTEGER", "constraints": "DEFAULT 0"},
                "created_at": {"type": "REAL", "constraints": "NOT NULL"},
                "updated_at": {"type": "REAL", "constraints": "NOT NULL"},
                "metadata": {"type": "TEXT", "constraints": ""},
                "tags": {"type": "TEXT", "constraints": ""},
                "thread_ids": {"type": "TEXT", "constraints": ""}
            },
            "indexes": [
                {"name": "idx_sessions_status", "column": "status"},
                {"name": "idx_sessions_created_at", "column": "created_at"},
                {"name": "idx_sessions_updated_at", "column": "updated_at"}
            ]
        }
        
        await self._provider.create_table("sessions", session_schema)
        logger.debug("SQLite session backend connected and initialized")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        await self._provider.disconnect()
        logger.debug("SQLite session backend disconnected")
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        provider_health = await self._provider.health_check()
        
        return {
            "status": "healthy" if self._connected else "disconnected",
            "provider": provider_health,
            "table_exists": await self._provider.table_exists("sessions")
        }
    
    # === ISessionStorage 接口实现 ===
    
    async def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        return await self._session_mixin.save_session(session_id, data)
    
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据"""
        return await self._session_mixin.load_session(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话数据"""
        return await self._session_mixin.delete_session(session_id)
    
    async def list_sessions(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话"""
        return await self._session_mixin.list_sessions(filters, limit)
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return await self._session_mixin.session_exists(session_id)
    
    async def get_session_threads(self, session_id: str) -> List[str]:
        """获取会话关联的线程ID列表"""
        return await self._session_mixin.get_session_threads(session_id)
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        return await self._session_mixin.update_session_status(session_id, status)
    
    # === IStorage 接口实现（委托给提供者）===
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        return await self._provider.save("sessions", data)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        return await self._provider.load("sessions", id)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        return await self._provider.update("sessions", id, updates)
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        return await self._provider.delete("sessions", id)
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        return await self._provider.exists("sessions", id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        return await self._provider.list("sessions", filters, limit)
    
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        return await self._provider.query("sessions", query, params)
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        return await self._provider.count("sessions", filters)
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        return await self._provider.batch_save("sessions", data_list)
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        return await self._provider.batch_delete("sessions", ids)
    
    async def stream_list(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """流式列出数据（简化实现）"""
        results = await self.list(filters, batch_size)
        return results


class SQLiteThreadBackend(BaseStorageBackend, IThreadStorage):
    """SQLite线程存储后端
    
    通过组合SQLite提供者和线程存储混入来实现。
    """
    
    def __init__(self, db_path: str = "./data/threads.db", **config: Any) -> None:
        """初始化SQLite线程后端
        
        Args:
            db_path: 数据库文件路径
            **config: 其他配置参数
        """
        super().__init__(db_path=db_path, **config)
        
        # 创建SQLite提供者
        self._provider = SQLiteProvider(db_path=db_path, **config)
        
        # 创建线程存储混入
        self._thread_mixin = ThreadStorageMixin(self._provider)
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # 连接到SQLite提供者
        await self._provider.connect()
        
        # 创建线程表
        thread_schema = {
            "columns": {
                "id": {"type": "TEXT", "constraints": "PRIMARY KEY"},
                "session_id": {"type": "TEXT", "constraints": "NOT NULL"},
                "status": {"type": "TEXT", "constraints": "NOT NULL"},
                "created_at": {"type": "REAL", "constraints": "NOT NULL"},
                "updated_at": {"type": "REAL", "constraints": "NOT NULL"},
                "metadata": {"type": "TEXT", "constraints": ""},
                "tags": {"type": "TEXT", "constraints": ""},
                "branch_ids": {"type": "TEXT", "constraints": ""}
            },
            "indexes": [
                {"name": "idx_threads_session_id", "column": "session_id"},
                {"name": "idx_threads_status", "column": "status"},
                {"name": "idx_threads_created_at", "column": "created_at"},
                {"name": "idx_threads_updated_at", "column": "updated_at"}
            ]
        }
        
        await self._provider.create_table("threads", thread_schema)
        logger.debug("SQLite thread backend connected and initialized")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        await self._provider.disconnect()
        logger.debug("SQLite thread backend disconnected")
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        provider_health = await self._provider.health_check()
        
        return {
            "status": "healthy" if self._connected else "disconnected",
            "provider": provider_health,
            "table_exists": await self._provider.table_exists("threads")
        }
    
    # === IThreadStorage 接口实现 ===
    
    async def save_thread(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据"""
        return await self._thread_mixin.save_thread(thread_id, data)
    
    async def load_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据"""
        return await self._thread_mixin.load_thread(thread_id)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程数据"""
        return await self._thread_mixin.delete_thread(thread_id)
    
    async def list_threads(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出线程"""
        return await self._thread_mixin.list_threads(filters, limit)
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查线程是否存在"""
        return await self._thread_mixin.thread_exists(thread_id)
    
    async def get_threads_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取线程列表"""
        return await self._thread_mixin.get_threads_by_session(session_id)
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新线程状态"""
        return await self._thread_mixin.update_thread_status(thread_id, status)
    
    async def get_thread_branches(self, thread_id: str) -> List[str]:
        """获取线程关联的分支ID列表"""
        return await self._thread_mixin.get_thread_branches(thread_id)
    
    # === IStorage 接口实现（委托给提供者）===
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        return await self._provider.save("threads", data)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        return await self._provider.load("threads", id)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        return await self._provider.update("threads", id, updates)
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        return await self._provider.delete("threads", id)
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        return await self._provider.exists("threads", id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        return await self._provider.list("threads", filters, limit)
    
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        return await self._provider.query("threads", query, params)
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        return await self._provider.count("threads", filters)
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        return await self._provider.batch_save("threads", data_list)
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        return await self._provider.batch_delete("threads", ids)
    
    async def stream_list(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """流式列出数据（简化实现）"""
        results = await self.list(filters, batch_size)
        return results