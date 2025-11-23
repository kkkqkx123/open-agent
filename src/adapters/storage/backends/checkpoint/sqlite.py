"""Checkpoint SQLite存储后端

提供基于SQLite的checkpoint存储实现，实现ICheckpointStore接口。
"""

import asyncio
import sqlite3
import threading
import time
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.interfaces.checkpoint import ICheckpointStore
from src.adapters.storage.adapters.base import ConnectionPooledStorageBackend
from src.core.common.exceptions import (
    CheckpointNotFoundError,
    CheckpointStorageError
)
from src.adapters.storage.utils.common_utils import StorageCommonUtils


logger = logging.getLogger(__name__)


class CheckpointSqliteBackend(ConnectionPooledStorageBackend, ICheckpointStore):
    """Checkpoint SQLite存储后端实现
    
    提供基于SQLite的checkpoint存储功能，实现ICheckpointStore接口。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化checkpoint SQLite存储
        """
        # 初始化连接池基类
        pool_size = config.get("connection_pool_size", 5)
        super().__init__(pool_size=pool_size, **config)
        
        # SQLite特定配置
        self.db_path = config.get("db_path", "checkpoints.db")
        self.timeout = config.get("timeout", 30.0)
        self.enable_wal_mode = config.get("enable_wal_mode", True)
        self.enable_foreign_keys = config.get("enable_foreign_keys", True)
        
        # 扩展统计信息
        self._stats.update({
            "database_size_bytes": 0,
            "total_checkpoints": 0,
            "expired_checkpoints_cleaned": 0,
        })
        
        logger.info(f"CheckpointSqliteBackend initialized with db_path: {self.db_path}")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 初始化连接池
            await self._initialize_sqlite_connection_pool()
            
            # 调用父类连接逻辑
            await ConnectionPooledStorageBackend.connect(self)
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to connect CheckpointSqliteBackend: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 调用父类断开逻辑
            await ConnectionPooledStorageBackend.disconnect(self)
            
            # 关闭连接池
            self._close_connection_pool()
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to disconnect CheckpointSqliteBackend: {e}")
    
    async def _initialize_sqlite_connection_pool(self) -> None:
        """初始化SQLite连接池"""
        try:
            with self._pool_lock:
                for _ in range(self._pool_size):
                    conn = self._create_connection()
                    
                    # 配置连接
                    self._configure_connection(conn)
                    
                    # 初始化表
                    self._initialize_tables(conn)
                    
                    self._connection_pool.append(conn)
                
                self._stats["connection_pool_size"] = len(self._connection_pool)
                
        except Exception as e:
            raise CheckpointStorageError(f"Failed to initialize connection pool: {e}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建SQLite连接"""
        try:
            # 确保目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 创建连接
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False
            )
            
            # 设置行工厂，返回字典
            conn.row_factory = sqlite3.Row
            
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            
            # 设置WAL模式以提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            
            return conn
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to create SQLite connection: {e}")
    
    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """配置连接"""
        try:
            cursor = conn.cursor()
            
            # 设置缓存大小
            cache_size = self._config.get("cache_size", 2000)
            cursor.execute(f"PRAGMA cache_size = {cache_size}")
            
            # 设置临时存储位置
            temp_store = self._config.get("temp_store", "memory")
            if temp_store == "memory":
                cursor.execute("PRAGMA temp_store = MEMORY")
            elif temp_store == "file":
                cursor.execute("PRAGMA temp_store = FILE")
            
            # 设置同步模式
            synchronous_mode = self._config.get("synchronous_mode", "NORMAL")
            cursor.execute(f"PRAGMA synchronous = {synchronous_mode}")
            
            # 设置日志模式
            journal_mode = self._config.get("journal_mode", "WAL")
            cursor.execute(f"PRAGMA journal_mode = {journal_mode}")
            
            # 启用外键约束
            if self.enable_foreign_keys:
                cursor.execute("PRAGMA foreign_keys = ON")
            
            conn.commit()
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to configure connection: {e}")
    
    def _initialize_tables(self, conn: sqlite3.Connection) -> None:
        """初始化数据库表"""
        try:
            cursor = conn.cursor()
            
            # 创建checkpoint存储表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoint_storage (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    session_id TEXT,
                    workflow_id TEXT,
                    state_data TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL,
                    compressed INTEGER DEFAULT 0
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoint_thread_id ON checkpoint_storage(thread_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoint_session_id ON checkpoint_storage(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoint_workflow_id ON checkpoint_storage(workflow_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoint_expires_at ON checkpoint_storage(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoint_created_at ON checkpoint_storage(created_at)")
            
            # 提交更改
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise CheckpointStorageError(f"Failed to initialize database tables: {e}")
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据
        
        Args:
            checkpoint_data: checkpoint数据字典
            
        Returns:
            bool: 是否保存成功
        """
        conn = None
        try:
            # 验证必需字段
            thread_id = checkpoint_data.get("thread_id")
            if not thread_id:
                raise CheckpointStorageError("checkpoint_data必须包含'thread_id'")
            
            # 生成ID（如果没有）
            if "id" not in checkpoint_data:
                import uuid
                checkpoint_data["id"] = str(uuid.uuid4())
            
            checkpoint_id = checkpoint_data["id"]
            current_time = time.time()
            
            # 添加时间戳
            checkpoint_data["created_at"] = checkpoint_data.get("created_at", current_time)
            checkpoint_data["updated_at"] = current_time
            
            # 序列化元数据
            metadata = checkpoint_data.get("metadata", {})
            serialized_metadata = StorageCommonUtils.serialize_data(metadata)
            
            # 获取连接
            conn = self._get_connection()
            
            # 插入或更新记录
            query = """
                INSERT OR REPLACE INTO checkpoint_storage 
                (id, thread_id, session_id, workflow_id, state_data, metadata, created_at, updated_at, expires_at, compressed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = [
                checkpoint_id,
                thread_id,
                checkpoint_data.get("session_id", ""),
                checkpoint_data.get("workflow_id", ""),
                StorageCommonUtils.serialize_data(checkpoint_data.get("state_data", {})),
                serialized_metadata,
                checkpoint_data["created_at"],
                checkpoint_data["updated_at"],
                checkpoint_data.get("expires_at"),
                int(checkpoint_data.get("compressed", False))
            ]
            
            affected_rows = self._execute_update(conn, query, params)
            
            logger.debug(f"Saved checkpoint {checkpoint_id} for thread {thread_id}")
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise CheckpointStorageError(f"保存checkpoint失败: {e}") from e
        finally:
            if conn:
                self._return_connection(conn)
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 查询记录
            query = """
                SELECT * FROM checkpoint_storage 
                WHERE thread_id = ? 
                ORDER BY created_at DESC
            """
            results = self._execute_query(conn, query, [thread_id])
            
            checkpoints = []
            if results and isinstance(results, list):
                for row in results:
                    if not isinstance(row, dict):
                        continue
                    
                    # 检查是否过期
                    expires_at = row.get("expires_at")
                    if expires_at and isinstance(expires_at, (int, float)) and expires_at < time.time():
                        continue
                    
                    # 反序列化数据
                    try:
                        checkpoint_data = {
                            "id": row["id"],
                            "thread_id": row["thread_id"],
                            "session_id": row["session_id"],
                            "workflow_id": row["workflow_id"],
                            "state_data": StorageCommonUtils.deserialize_data(row["state_data"]),
                            "metadata": StorageCommonUtils.deserialize_data(row["metadata"]),
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "expires_at": row["expires_at"],
                            "compressed": bool(row["compressed"])
                        }
                        checkpoints.append(checkpoint_data)
                    except Exception as e:
                        logger.error(f"Failed to deserialize checkpoint data for {row.get('id', 'unknown')}: {e}")
                        continue
            
            logger.debug(f"Listed {len(checkpoints)} checkpoints for thread {thread_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}") from e
        finally:
            if conn:
                self._return_connection(conn)
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        conn = None
        try:
            if checkpoint_id:
                # 根据ID加载特定checkpoint
                conn = self._get_connection()
                
                query = "SELECT * FROM checkpoint_storage WHERE id = ? AND thread_id = ?"
                result = self._execute_query(conn, query, [checkpoint_id, thread_id], fetch_one=True)
                
                if not result or not isinstance(result, dict):
                    return None
                
                # 检查是否过期
                expires_at = result.get("expires_at")
                if expires_at and isinstance(expires_at, (int, float)) and expires_at < time.time():
                    # 删除过期记录
                    self._execute_update(conn, "DELETE FROM checkpoint_storage WHERE id = ?", [checkpoint_id])
                    self._stats["expired_checkpoints_cleaned"] += 1
                    return None
                
                # 反序列化数据
                checkpoint_data = {
                    "id": result["id"],
                    "thread_id": result["thread_id"],
                    "session_id": result["session_id"],
                    "workflow_id": result["workflow_id"],
                    "state_data": StorageCommonUtils.deserialize_data(result["state_data"]),
                    "metadata": StorageCommonUtils.deserialize_data(result["metadata"]),
                    "created_at": result["created_at"],
                    "updated_at": result["updated_at"],
                    "expires_at": result["expires_at"],
                    "compressed": bool(result["compressed"])
                }
                
                return checkpoint_data
            else:
                # 加载最新checkpoint
                checkpoints = await self.list_by_thread(thread_id)
                return checkpoints[0] if checkpoints else None
                
        except Exception as e:
            logger.error(f"Failed to load checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"加载checkpoint失败: {e}") from e
        finally:
            if conn:
                self._return_connection(conn)
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID，如果为None则删除所有
            
        Returns:
            bool: 是否删除成功
        """
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            if checkpoint_id:
                # 删除特定checkpoint
                query = "DELETE FROM checkpoint_storage WHERE id = ? AND thread_id = ?"
                params = [checkpoint_id, thread_id]
            else:
                # 删除thread的所有checkpoint
                query = "DELETE FROM checkpoint_storage WHERE thread_id = ?"
                params = [thread_id]
            
            affected_rows = self._execute_update(conn, query, params)
            
            logger.debug(f"Deleted {affected_rows} checkpoints for thread {thread_id}")
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"删除checkpoint失败: {e}") from e
        finally:
            if conn:
                self._return_connection(conn)
    
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        try:
            # 获取thread的所有checkpoint（已按时间倒序排列）
            checkpoints = await self.list_by_thread(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"获取最新checkpoint失败: {e}") from e
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个
        
        Args:
            thread_id: thread ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 获取thread的所有checkpoint（按创建时间倒序）
            query = """
                SELECT id, created_at FROM checkpoint_storage 
                WHERE thread_id = ? 
                ORDER BY created_at DESC
            """
            results = self._execute_query(conn, query, [thread_id])
            
            if not results or not isinstance(results, list) or len(results) <= max_count:
                # 不需要清理
                return 0
            
            # 获取需要删除的checkpoint ID（保留最新的max_count个）
            checkpoints_to_delete = results[max_count:]
            ids_to_delete = [row["id"] for row in checkpoints_to_delete]
            
            if not ids_to_delete:
                return 0
            
            # 构建删除查询
            placeholders = ",".join(["?" for _ in ids_to_delete])
            delete_query = f"DELETE FROM checkpoint_storage WHERE id IN ({placeholders})"
            
            # 执行删除
            affected_rows = self._execute_update(conn, delete_query, ids_to_delete)
            
            logger.debug(f"Cleaned up {affected_rows} old checkpoints for thread {thread_id}")
            return affected_rows
            
        except Exception as e:
            logger.error(f"Failed to cleanup old checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"清理旧checkpoint失败: {e}") from e
        finally:
            if conn:
                self._return_connection(conn)
    
    # 实现StorageBackend的抽象方法
    async def save_impl(self, data: Union[Dict[str, Any], bytes], compressed: bool = False) -> str:
        """实际保存实现"""
        conn = None
        try:
            # 生成ID（如果没有）
            if isinstance(data, dict):
                import uuid
                item_id = data.get("id", str(uuid.uuid4()))
                data["id"] = item_id
                current_time = time.time()
                
                # 添加元数据时间戳
                StorageCommonUtils.add_metadata_timestamps(
                    data, self.enable_ttl, self.default_ttl_seconds, current_time
                )
                
                # 序列化数据
                serialized_data = StorageCommonUtils.serialize_data(data)
                
                # 获取连接
                conn = self._get_connection()
                
                # 插入或更新记录
                query = """
                    INSERT OR REPLACE INTO checkpoint_storage 
                    (id, thread_id, session_id, workflow_id, state_data, metadata, created_at, updated_at, expires_at, compressed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = [
                    item_id,
                    data.get("thread_id", ""),
                    data.get("session_id", ""),
                    data.get("workflow_id", ""),
                    serialized_data,
                    StorageCommonUtils.serialize_data(data.get("metadata", {})),
                    data.get("created_at", current_time),
                    current_time,
                    data.get("expires_at"),
                    int(compressed)
                ]
                
                affected_rows = self._execute_update(conn, query, params)
                
                if affected_rows > 0:
                    self._update_stats("save")
                
                return item_id
            else:
                raise CheckpointStorageError(f"Expected dict for data, got {type(data)}")
                
        except Exception as e:
            if isinstance(e, CheckpointStorageError):
                raise
            raise CheckpointStorageError(f"Failed to save data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 查询记录
            query = "SELECT * FROM checkpoint_storage WHERE id = ?"
            result = self._execute_query(conn, query, [id], fetch_one=True)
            
            if not result or not isinstance(result, dict):
                return None
            
            # 检查是否过期
            expires_at = result.get("expires_at")
            if expires_at and isinstance(expires_at, (int, float)) and expires_at < time.time():
                # 删除过期记录
                self._execute_update(conn, "DELETE FROM checkpoint_storage WHERE id = ?", [id])
                self._stats["expired_checkpoints_cleaned"] += 1
                return None
            
            # 反序列化数据
            data_str = result.get("state_data")
            if not isinstance(data_str, str):
                raise CheckpointStorageError(f"Invalid data type in database: {type(data_str)}")
            data = StorageCommonUtils.deserialize_data(data_str)
            
            self._update_stats("load")
            return data
            
        except Exception as e:
            if isinstance(e, CheckpointStorageError):
                raise
            raise CheckpointStorageError(f"Failed to load data {id}: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 删除记录
            query = "DELETE FROM checkpoint_storage WHERE id = ?"
            affected_rows = self._execute_update(conn, query, [id])
            
            if affected_rows > 0:
                self._update_stats("delete")
            
            return affected_rows > 0
            
        except Exception as e:
            if isinstance(e, CheckpointStorageError):
                raise
            raise CheckpointStorageError(f"Failed to delete data {id}: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def list_impl(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """实际列表实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 构建查询
            where_clause, params = self._build_where_clause(filters)
            
            query = f"SELECT * FROM checkpoint_storage {where_clause} ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            # 执行查询
            results = self._execute_query(conn, query, params)
            
            # 处理结果
            processed_results = []
            if results and isinstance(results, list):
                for row in results:
                    if not isinstance(row, dict):
                        continue
                        
                    # 检查是否过期
                    expires_at = row.get("expires_at")
                    if expires_at and isinstance(expires_at, (int, float)) and expires_at < time.time():
                        continue
                    
                    # 反序列化数据
                    try:
                        data_str = row.get("state_data")
                        if not isinstance(data_str, str):
                            logger.error(f"Invalid data type in record {row.get('id', 'unknown')}: {type(data_str)}")
                            continue
                        data = StorageCommonUtils.deserialize_data(data_str)
                        processed_results.append(data)
                    except Exception as e:
                        logger.error(f"Failed to deserialize data for record {row.get('id', 'unknown')}: {e}")
                        continue
            
            self._update_stats("list")
            return processed_results
            
        except Exception as e:
            if isinstance(e, CheckpointStorageError):
                raise
            raise CheckpointStorageError(f"Failed to list data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 获取数据库信息
            db_info = self._get_database_info(conn)
            
            # 更新统计信息
            self._stats["database_size_bytes"] = db_info["database_size_bytes"]
            self._stats["total_checkpoints"] = db_info["total_checkpoints"]
            
            # 清理过期记录
            expired_count = self._cleanup_expired_records(conn)
            self._stats["expired_checkpoints_cleaned"] += expired_count
            
            return {
                "status": "healthy",
                "backend_type": "checkpoint_sqlite",
                "database_path": self.db_path,
                "database_size_bytes": self._stats["database_size_bytes"],
                "database_size_mb": db_info["database_size_mb"],
                "total_checkpoints": self._stats["total_checkpoints"],
                "connection_pool_size": self._pool_size,
                "active_connections": self._active_connections,
                "expired_checkpoints_cleaned": self._stats["expired_checkpoints_cleaned"],
                "config": {
                    "timeout": self.timeout,
                    "enable_wal_mode": self.enable_wal_mode,
                    "enable_foreign_keys": self.enable_foreign_keys,
                    "connection_pool_size": self._pool_size,
                }
            }
            
        except Exception as e:
            raise CheckpointStorageError(f"Health check failed: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    # SQLite特定的辅助方法
    def _execute_query(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: Optional[List[Any]] = None,
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """执行查询"""
        try:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch_all:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                return None
                
        except Exception as e:
            raise CheckpointStorageError(f"Failed to execute query: {e}")
    
    def _execute_update(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: Optional[List[Any]] = None
    ) -> int:
        """执行更新操作"""
        try:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            return cursor.rowcount
            
        except Exception as e:
            conn.rollback()
            raise CheckpointStorageError(f"Failed to execute update: {e}")
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> tuple:
        """构建WHERE子句"""
        if not filters:
            return "", []
        
        conditions = []
        params: List[Any] = []
        
        for key, value in filters.items():
            if isinstance(value, (list, tuple)):
                # IN查询
                placeholders = ",".join(["?" for _ in value])
                conditions.append(f"{key} IN ({placeholders})")
                params.extend(value)
            elif isinstance(value, dict) and "$gt" in value:
                # 大于查询
                conditions.append(f"{key} > ?")
                params.append(value["$gt"])
            elif isinstance(value, dict) and "$lt" in value:
                # 小于查询
                conditions.append(f"{key} < ?")
                params.append(value["$lt"])
            elif isinstance(value, dict) and "$gte" in value:
                # 大于等于查询
                conditions.append(f"{key} >= ?")
                params.append(value["$gte"])
            elif isinstance(value, dict) and "$lte" in value:
                # 小于等于查询
                conditions.append(f"{key} <= ?")
                params.append(value["$lte"])
            elif isinstance(value, dict) and "$ne" in value:
                # 不等于查询
                conditions.append(f"{key} != ?")
                params.append(value["$ne"])
            elif isinstance(value, dict) and "$like" in value:
                # LIKE查询
                conditions.append(f"{key} LIKE ?")
                params.append(value["$like"])
            else:
                # 等于查询
                conditions.append(f"{key} = ?")
                params.append(value)
        
        where_clause = "WHERE " + " AND ".join(conditions)
        return where_clause, params
    
    def _get_database_info(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            cursor = conn.cursor()
            
            # 获取表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 获取checkpoint记录数
            cursor.execute("SELECT COUNT(*) FROM checkpoint_storage")
            total_checkpoints = cursor.fetchone()[0]
            
            # 获取数据库大小
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            return {
                "tables": tables,
                "total_checkpoints": total_checkpoints,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to get database info: {e}")
    
    def _cleanup_expired_records(self, conn: sqlite3.Connection) -> int:
        """清理过期记录"""
        try:
            current_time = time.time()
            query = "DELETE FROM checkpoint_storage WHERE expires_at IS NOT NULL AND expires_at < ?"
            return self._execute_update(conn, query, [current_time])
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to cleanup expired records: {e}")
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 计算截止时间
            cutoff_time = StorageCommonUtils.calculate_cutoff_time(retention_days)
            
            # 删除旧记录
            query = "DELETE FROM checkpoint_storage WHERE created_at < ?"
            affected_rows = self._execute_update(conn, query, [cutoff_time])
            
            return affected_rows
            
        except Exception as e:
            if isinstance(e, CheckpointStorageError):
                raise
            raise CheckpointStorageError(f"Failed to cleanup old data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def _cleanup_expired_items_impl(self) -> None:
        """清理过期项的SQLite特定实现"""
        conn = None
        try:
            conn = self._get_connection()
            current_time = time.time()
            
            # 使用SQL直接删除过期项
            query = "DELETE FROM checkpoint_storage WHERE expires_at IS NOT NULL AND expires_at < ?"
            affected_rows = self._execute_update(conn, query, [current_time])
            
            self._stats["expired_checkpoints_cleaned"] += affected_rows
            
            if affected_rows > 0:
                logger.debug(f"Cleaned {affected_rows} expired checkpoints from SQLite")
                
        except Exception as e:
            logger.error(f"Error cleaning expired checkpoints in SQLite: {e}")
        finally:
            if conn:
                self._return_connection(conn)