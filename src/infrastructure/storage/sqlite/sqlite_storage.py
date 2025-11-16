"""
SQLite存储实现

提供基于SQLite的存储后端实现，支持数据持久化、事务和高级查询功能。
"""

import asyncio
import time
import uuid
import json
import sqlite3
import threading
import os
import shutil
import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import aiosqlite
import weakref

from ....domain.storage.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageValidationError,
    StorageNotFoundError,
    StorageTimeoutError,
    StorageCapacityError
)
from ..interfaces import IStorageBackend
from .sqlite_config import SQLiteStorageConfig


logger = logging.getLogger(__name__)


class SQLiteStorage(IStorageBackend):
    """SQLite存储实现
    
    提供基于SQLite的存储后端，支持数据持久化、事务和高级查询功能。
    """
    
    def __init__(self, **config):
        """初始化SQLite存储
        
        Args:
            **config: 配置参数
        """
        # 解析配置
        self.config = SQLiteStorageConfig(**config)
        
        # 连接池
        self._pool = None
        self._pool_lock = threading.Lock()
        
        # 连接状态
        self._connected = False
        
        # 统计信息
        self._stats = {
            "total_operations": 0,
            "save_operations": 0,
            "load_operations": 0,
            "update_operations": 0,
            "delete_operations": 0,
            "list_operations": 0,
            "query_operations": 0,
            "transaction_operations": 0,
            "connection_errors": 0,
            "query_errors": 0,
            "total_query_time": 0.0,
            "average_query_time": 0.0
        }
        
        # 后台任务
        self._vacuum_task = None
        self._backup_task = None
        
        # 数据库版本
        self._db_version = 1
        
        logger.info(f"SQLiteStorage initialized with database: {self.config.database_path}")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 确保数据库目录存在
            db_dir = os.path.dirname(self.config.database_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            
            # 创建连接池
            await self._create_pool()
            
            # 初始化数据库
            await self._initialize_database()
            
            # 启动后台任务
            if self.config.enable_auto_vacuum:
                self._vacuum_task = asyncio.create_task(self._vacuum_worker())
            
            if self.config.enable_backup:
                self._backup_task = asyncio.create_task(self._backup_worker())
            
            self._connected = True
            logger.info("SQLiteStorage connected")
            
        except Exception as e:
            self._stats["connection_errors"] += 1
            raise StorageConnectionError(f"Failed to connect SQLiteStorage: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 停止后台任务
            if self._vacuum_task:
                self._vacuum_task.cancel()
                try:
                    await self._vacuum_task
                except asyncio.CancelledError:
                    pass
                self._vacuum_task = None
            
            if self._backup_task:
                self._backup_task.cancel()
                try:
                    await self._backup_task
                except asyncio.CancelledError:
                    pass
                self._backup_task = None
            
            # 关闭连接池
            await self._close_pool()
            
            self._connected = False
            logger.info("SQLiteStorage disconnected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect SQLiteStorage: {e}")
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self._pool is not None
    
    async def save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        start_time = time.time()
        
        try:
            # 生成ID（如果没有）
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            item_id = data["id"]
            
            # 序列化数据
            serialized_data = json.dumps(data, default=str)
            
            # 插入数据
            async with self._get_connection() as conn:
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO storage_data (
                        id, type, data, session_id, thread_id, 
                        metadata, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        data.get("type", ""),
                        serialized_data,
                        data.get("session_id"),
                        data.get("thread_id"),
                        json.dumps(data.get("metadata", {}), default=str),
                        data.get("created_at", datetime.now().isoformat()),
                        data.get("updated_at", datetime.now().isoformat())
                    )
                )
                await conn.commit()
            
            self._update_stats("save", time.time() - start_time)
            return item_id
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
    
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        start_time = time.time()
        
        try:
            async with self._get_connection() as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    """
                    SELECT id, type, data, session_id, thread_id, 
                           metadata, created_at, updated_at
                    FROM storage_data
                    WHERE id = ?
                    """,
                    (id,)
                )
                row = await cursor.fetchone()
                
                if row is None:
                    return None
                
                # 反序列化数据
                data = json.loads(row["data"])
                data["id"] = row["id"]
                data["type"] = row["type"]
                data["session_id"] = row["session_id"]
                data["thread_id"] = row["thread_id"]
                data["metadata"] = json.loads(row["metadata"]) if row["metadata"] else {}
                data["created_at"] = row["created_at"]
                data["updated_at"] = row["updated_at"]
            
            self._update_stats("load", time.time() - start_time)
            return data
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
    
    async def update_impl(self, id: str, updates: Dict[str, Any]) -> bool:
        """实际更新实现"""
        start_time = time.time()
        
        try:
            # 获取现有数据
            existing = await self.load_impl(id)
            if existing is None:
                return False
            
            # 合并更新
            existing.update(updates)
            existing["updated_at"] = datetime.now().isoformat()
            
            # 序列化数据
            serialized_data = json.dumps(existing, default=str)
            
            # 更新数据
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    """
                    UPDATE storage_data
                    SET data = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (serialized_data, existing["updated_at"], id)
                )
                await conn.commit()
                
                success = cursor.rowcount > 0
            
            self._update_stats("update", time.time() - start_time)
            return success
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update data {id}: {e}")
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        start_time = time.time()
        
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    "DELETE FROM storage_data WHERE id = ?",
                    (id,)
                )
                await conn.commit()
                
                success = cursor.rowcount > 0
            
            self._update_stats("delete", time.time() - start_time)
            return success
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
    
    async def list_impl(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """实际列表实现"""
        start_time = time.time()
        
        try:
            # 构建查询
            query, params = self._build_select_query(filters, limit)
            
            async with self._get_connection() as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                
                # 转换结果
                results = []
                for row in rows:
                    data = json.loads(row["data"])
                    data["id"] = row["id"]
                    data["type"] = row["type"]
                    data["session_id"] = row["session_id"]
                    data["thread_id"] = row["thread_id"]
                    data["metadata"] = json.loads(row["metadata"]) if row["metadata"] else {}
                    data["created_at"] = row["created_at"]
                    data["updated_at"] = row["updated_at"]
                    results.append(data)
            
            self._update_stats("list", time.time() - start_time)
            return results
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
    
    async def query_impl(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """实际查询实现"""
        start_time = time.time()
        
        try:
            # 执行查询
            async with self._get_connection() as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                
                # 转换结果
                results = []
                for row in rows:
                    # 如果查询包含data字段，需要反序列化
                    if "data" in row.keys():
                        data = json.loads(row["data"])
                        # 添加其他字段
                        for key in row.keys():
                            if key != "data":
                                data[key] = row[key]
                        results.append(data)
                    else:
                        results.append(dict(row))
            
            self._update_stats("query", time.time() - start_time)
            return results
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to execute query: {e}")
    
    async def exists_impl(self, id: str) -> bool:
        """实际存在检查实现"""
        start_time = time.time()
        
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT 1 FROM storage_data WHERE id = ? LIMIT 1",
                    (id,)
                )
                result = await cursor.fetchone()
                
                exists = result is not None
            
            self._update_stats("load", time.time() - start_time)
            return exists
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to check existence of data {id}: {e}")
    
    async def count_impl(self, filters: Dict[str, Any]) -> int:
        """实际计数实现"""
        start_time = time.time()
        
        try:
            # 构建查询
            where_clause, params = self._build_where_clause(filters)
            query = f"SELECT COUNT(*) FROM storage_data{where_clause}"
            
            async with self._get_connection() as conn:
                cursor = await conn.execute(query, params)
                result = await cursor.fetchone()
                count = result[0] if result else 0
            
            self._update_stats("query", time.time() - start_time)
            return count
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to count data: {e}")
    
    async def transaction_impl(self, operations: List[Dict[str, Any]]) -> bool:
        """实际事务实现"""
        start_time = time.time()
        
        try:
            async with self._get_connection() as conn:
                await conn.execute("BEGIN TRANSACTION")
                
                try:
                    for operation in operations:
                        op_type = operation.get("type")
                        
                        if op_type == "save":
                            data = operation["data"]
                            if "id" not in data:
                                data["id"] = str(uuid.uuid4())
                            
                            serialized_data = json.dumps(data, default=str)
                            await conn.execute(
                                """
                                INSERT OR REPLACE INTO storage_data (
                                    id, type, data, session_id, thread_id, 
                                    metadata, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    data["id"],
                                    data.get("type", ""),
                                    serialized_data,
                                    data.get("session_id"),
                                    data.get("thread_id"),
                                    json.dumps(data.get("metadata", {}), default=str),
                                    data.get("created_at", datetime.now().isoformat()),
                                    data.get("updated_at", datetime.now().isoformat())
                                )
                            )
                        
                        elif op_type == "update":
                            id = operation["id"]
                            updates = operation["data"]
                            
                            # 获取现有数据
                            cursor = await conn.execute(
                                "SELECT data FROM storage_data WHERE id = ?",
                                (id,)
                            )
                            row = await cursor.fetchone()
                            
                            if row:
                                existing = json.loads(row[0])
                                existing.update(updates)
                                existing["updated_at"] = datetime.now().isoformat()
                                
                                serialized_data = json.dumps(existing, default=str)
                                await conn.execute(
                                    "UPDATE storage_data SET data = ?, updated_at = ? WHERE id = ?",
                                    (serialized_data, existing["updated_at"], id)
                                )
                        
                        elif op_type == "delete":
                            id = operation["id"]
                            await conn.execute(
                                "DELETE FROM storage_data WHERE id = ?",
                                (id,)
                            )
                        
                        else:
                            raise StorageTransactionError(f"Unknown operation type: {op_type}")
                    
                    await conn.commit()
                    
                except Exception:
                    await conn.rollback()
                    raise
            
            self._update_stats("transaction", time.time() - start_time)
            return True
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageTransactionError(f"Transaction failed: {e}")
    
    async def batch_save_impl(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """实际批量保存实现"""
        start_time = time.time()
        
        try:
            ids = []
            
            async with self._get_connection() as conn:
                await conn.execute("BEGIN TRANSACTION")
                
                try:
                    for data in data_list:
                        # 生成ID（如果没有）
                        if "id" not in data:
                            data["id"] = str(uuid.uuid4())
                        
                        item_id = data["id"]
                        ids.append(item_id)
                        
                        # 序列化数据
                        serialized_data = json.dumps(data, default=str)
                        
                        # 插入数据
                        await conn.execute(
                            """
                            INSERT OR REPLACE INTO storage_data (
                                id, type, data, session_id, thread_id, 
                                metadata, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                item_id,
                                data.get("type", ""),
                                serialized_data,
                                data.get("session_id"),
                                data.get("thread_id"),
                                json.dumps(data.get("metadata", {}), default=str),
                                data.get("created_at", datetime.now().isoformat()),
                                data.get("updated_at", datetime.now().isoformat())
                            )
                        )
                    
                    await conn.commit()
                    
                except Exception:
                    await conn.rollback()
                    raise
            
            self._update_stats("save", time.time() - start_time)
            return ids
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch save data: {e}")
    
    async def batch_delete_impl(self, ids: List[str]) -> int:
        """实际批量删除实现"""
        start_time = time.time()
        
        try:
            async with self._get_connection() as conn:
                # 构建IN查询
                placeholders = ",".join(["?"] * len(ids))
                cursor = await conn.execute(
                    f"DELETE FROM storage_data WHERE id IN ({placeholders})",
                    ids
                )
                await conn.commit()
                
                count = cursor.rowcount
            
            self._update_stats("delete", time.time() - start_time)
            return count
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch delete data: {e}")
    
    async def get_by_session_impl(self, session_id: str) -> List[Dict[str, Any]]:
        """实际根据会话ID获取数据实现"""
        filters = {"session_id": session_id}
        return await self.list_impl(filters)
    
    async def get_by_thread_impl(self, thread_id: str) -> List[Dict[str, Any]]:
        """实际根据线程ID获取数据实现"""
        filters = {"thread_id": thread_id}
        return await self.list_impl(filters)
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        start_time = time.time()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
            
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    "DELETE FROM storage_data WHERE created_at < ?",
                    (cutoff_date,)
                )
                await conn.commit()
                
                count = cursor.rowcount
            
            self._update_stats("delete", time.time() - start_time)
            return count
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
    
    async def stream_list_impl(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """实际流式列表实现"""
        try:
            offset = 0
            
            while True:
                # 构建查询
                query, params = self._build_select_query(filters, batch_size, offset)
                
                async with self._get_connection() as conn:
                    conn.row_factory = aiosqlite.Row
                    cursor = await conn.execute(query, params)
                    rows = await cursor.fetchall()
                    
                    if not rows:
                        break
                    
                    # 转换结果
                    batch = []
                    for row in rows:
                        data = json.loads(row["data"])
                        data["id"] = row["id"]
                        data["type"] = row["type"]
                        data["session_id"] = row["session_id"]
                        data["thread_id"] = row["thread_id"]
                        data["metadata"] = json.loads(row["metadata"]) if row["metadata"] else {}
                        data["created_at"] = row["created_at"]
                        data["updated_at"] = row["updated_at"]
                        batch.append(data)
                    
                    yield batch
                    offset += batch_size
            
        except Exception as e:
            self._stats["query_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to stream list data: {e}")
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        try:
            start_time = time.time()
            
            # 测试连接
            async with self._get_connection() as conn:
                cursor = await conn.execute("SELECT 1")
                await cursor.fetchone()
                
                # 获取数据库信息
                cursor = await conn.execute("PRAGMA database_list")
                db_info = await cursor.fetchone()
                
                # 获取表信息
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM storage_data"
                )
                count_result = await cursor.fetchone()
                item_count = count_result["count"] if count_result else 0
                
                # 获取数据库大小
                db_size = os.path.getsize(self.config.database_path) if os.path.exists(self.config.database_path) else 0
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "database_path": self.config.database_path,
                "item_count": item_count,
                "database_size_bytes": db_size,
                "response_time_ms": response_time,
                "total_operations": self._stats["total_operations"],
                "connection_errors": self._stats["connection_errors"],
                "query_errors": self._stats["query_errors"],
                "average_query_time_ms": self._stats["average_query_time"] * 1000,
                "config": self.config.to_dict()
            }
            
        except Exception as e:
            self._stats["connection_errors"] += 1
            raise StorageConnectionError(f"Health check failed: {e}")
    
    async def _create_pool(self) -> None:
        """创建连接池"""
        with self._pool_lock:
            if self._pool is not None:
                return
            
            # 创建连接池
            self._pool = aiosqlite.connect(
                self.config.database_path,
                **self.config.get_connection_params()
            )
            
            logger.info(f"Created SQLite connection pool for {self.config.database_path}")
    
    async def _close_pool(self) -> None:
        """关闭连接池"""
        with self._pool_lock:
            if self._pool is not None:
                await self._pool.close()
                self._pool = None
                logger.info("Closed SQLite connection pool")
    
    @asynccontextmanager
    async def _get_connection(self):
        """获取数据库连接"""
        if self._pool is None:
            raise StorageConnectionError("Database not connected")
        
        # 获取连接
        async with aiosqlite.connect(
            self.config.database_path,
            **self.config.get_connection_params()
        ) as conn:
            try:
                yield conn
            except Exception:
                await conn.rollback()
                raise
    
    async def _initialize_database(self) -> None:
        """初始化数据库"""
        async with self._get_connection() as conn:
            # 创建存储表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS storage_data (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    session_id TEXT,
                    thread_id TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            
            # 创建索引
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON storage_data(type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON storage_data(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_thread_id ON storage_data(thread_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON storage_data(created_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON storage_data(updated_at)")
            
            # 创建元数据表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS storage_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            
            # 设置PRAGMA
            pragmas = self.config.get_pragmas()
            for pragma, value in pragmas.items():
                await conn.execute(f"PRAGMA {pragma} = {value}")
            
            # 检查/更新数据库版本
            await self._check_database_version(conn)
            
            await conn.commit()
    
    async def _check_database_version(self, conn) -> None:
        """检查/更新数据库版本"""
        cursor = await conn.execute(
            "SELECT value FROM storage_metadata WHERE key = 'db_version'"
        )
        result = await cursor.fetchone()
        
        current_version = int(result["value"]) if result else 0
        
        if current_version < self._db_version:
            # 执行数据库迁移
            await self._migrate_database(conn, current_version, self._db_version)
            
            # 更新版本号
            await conn.execute(
                "INSERT OR REPLACE INTO storage_metadata (key, value) VALUES (?, ?)",
                ("db_version", str(self._db_version))
            )
    
    async def _migrate_database(self, conn, from_version: int, to_version: int) -> None:
        """迁移数据库"""
        # 这里可以添加数据库迁移逻辑
        logger.info(f"Migrating database from version {from_version} to {to_version}")
    
    def _build_select_query(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> tuple:
        """构建SELECT查询"""
        where_clause, params = self._build_where_clause(filters)
        
        query = f"""
        SELECT id, type, data, session_id, thread_id, 
               metadata, created_at, updated_at
        FROM storage_data{where_clause}
        ORDER BY updated_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        return query, params
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> tuple:
        """构建WHERE子句"""
        if not filters:
            return "", []
        
        conditions = []
        params = []
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # 支持操作符
                if "$eq" in value:
                    conditions.append(f"{key} = ?")
                    params.append(value["$eq"])
                elif "$ne" in value:
                    conditions.append(f"{key} != ?")
                    params.append(value["$ne"])
                elif "$in" in value:
                    placeholders = ",".join(["?"] * len(value["$in"]))
                    conditions.append(f"{key} IN ({placeholders})")
                    params.extend(value["$in"])
                elif "$nin" in value:
                    placeholders = ",".join(["?"] * len(value["$nin"]))
                    conditions.append(f"{key} NOT IN ({placeholders})")
                    params.extend(value["$nin"])
                elif "$gt" in value:
                    conditions.append(f"{key} > ?")
                    params.append(value["$gt"])
                elif "$gte" in value:
                    conditions.append(f"{key} >= ?")
                    params.append(value["$gte"])
                elif "$lt" in value:
                    conditions.append(f"{key} < ?")
                    params.append(value["$lt"])
                elif "$lte" in value:
                    conditions.append(f"{key} <= ?")
                    params.append(value["$lte"])
                elif "$like" in value:
                    conditions.append(f"{key} LIKE ?")
                    params.append(value["$like"])
            else:
                conditions.append(f"{key} = ?")
                params.append(value)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return where_clause, params
    
    def _update_stats(self, operation: str, duration: float) -> None:
        """更新统计信息"""
        self._stats["total_operations"] += 1
        if f"{operation}_operations" in self._stats:
            self._stats[f"{operation}_operations"] += 1
        
        # 更新查询时间统计
        self._stats["total_query_time"] += duration
        if self._stats["total_operations"] > 0:
            self._stats["average_query_time"] = (
                self._stats["total_query_time"] / self._stats["total_operations"]
            )
    
    async def _vacuum_worker(self) -> None:
        """清理工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.config.vacuum_interval_hours * 3600)
                
                async with self._get_connection() as conn:
                    await conn.execute("VACUUM")
                    await conn.commit()
                
                logger.info("Database vacuum completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in vacuum task: {e}")
    
    async def _backup_worker(self) -> None:
        """备份工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.config.backup_interval_hours * 3600)
                
                await self._create_backup()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in backup task: {e}")
    
    async def _create_backup(self) -> None:
        """创建数据库备份"""
        if not self.config.backup_path:
            return
        
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.config.backup_path}.{timestamp}.db"
            
            # 创建备份
            async with self._get_connection() as conn:
                await conn.execute(f"VACUUM INTO '{backup_file}'")
            
            # 清理旧备份
            await self._cleanup_old_backups()
            
            logger.info(f"Created database backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    async def _cleanup_old_backups(self) -> None:
        """清理旧备份文件"""
        if not self.config.backup_path:
            return
        
        try:
            # 获取备份文件列表
            backup_dir = os.path.dirname(self.config.backup_path)
            backup_name = os.path.basename(self.config.backup_path)
            
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith(backup_name) and filename.endswith(".db"):
                    filepath = os.path.join(backup_dir, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除多余的备份
            for filepath, _ in backup_files[self.config.max_backup_files:]:
                os.remove(filepath)
                logger.debug(f"Removed old backup: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")