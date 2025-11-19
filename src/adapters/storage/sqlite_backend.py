"""SQLite存储后端

提供基于SQLite的存储后端实现，支持持久化、事务、索引等功能。
"""

import asyncio
import sqlite3
import threading
import time
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.core.state.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageCapacityError
)
from .base import BaseStorageBackend
from .sqlite_utils import SQLiteStorageUtils


logger = logging.getLogger(__name__)


class SQLiteStorageBackend(BaseStorageBackend):
    """SQLite存储后端实现
    
    提供基于SQLite的存储后端，支持持久化、事务、索引等功能。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化SQLite存储
        
        Args:
            **config: 配置参数
        """
        super().__init__(**config)
        
        # 解析配置
        self.db_path = config.get("db_path", "storage.db")
        self.timeout = config.get("timeout", 30.0)
        self.enable_wal_mode = config.get("enable_wal_mode", True)
        self.enable_foreign_keys = config.get("enable_foreign_keys", True)
        self.connection_pool_size = config.get("connection_pool_size", 5)
        self.enable_auto_vacuum = config.get("enable_auto_vacuum", False)
        self.cache_size = config.get("cache_size", 2000)
        self.temp_store = config.get("temp_store", "memory")  # memory, file, default
        self.synchronous_mode = config.get("synchronous_mode", "NORMAL")  # OFF, NORMAL, FULL, EXTRA
        self.journal_mode = config.get("journal_mode", "WAL")  # DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF
        self.enable_backup = config.get("enable_backup", False)
        self.backup_interval_hours = config.get("backup_interval_hours", 24)
        self.backup_path = config.get("backup_path", "backups")
        self.max_backup_files = config.get("max_backup_files", 7)
        
        # 连接池
        self._connection_pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()
        self._pool_semaphore = threading.Semaphore(self.connection_pool_size)
        
        # 线程锁
        self._lock = asyncio.Lock()
        self._thread_lock = threading.RLock()
        
        # 事务相关
        self._transaction_active = False
        self._transaction_connection: Optional[sqlite3.Connection] = None
        
        # 备份任务
        self._backup_task: Optional[asyncio.Task] = None
        self._last_backup_time = 0
        
        # 扩展统计信息
        self._stats.update({
            "connection_pool_size": 0,
            "active_connections": 0,
            "database_size_bytes": 0,
            "total_records": 0,
            "expired_records_cleaned": 0,
            "backup_count": 0,
            "last_backup_time": 0
        })
        
        logger.info(f"SQLiteStorageBackend initialized with db_path: {self.db_path}")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 初始化连接池
            await self._initialize_connection_pool()
            
            # 启动备份任务
            if self.enable_backup:
                self._backup_task = asyncio.create_task(self._backup_worker())
            
            self._connected = True
            logger.info("SQLiteStorageBackend connected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect SQLiteStorageBackend: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 停止备份任务
            if self._backup_task:
                self._backup_task.cancel()
                try:
                    await self._backup_task
                except asyncio.CancelledError:
                    pass
                self._backup_task = None
            
            # 关闭连接池
            await self._close_connection_pool()
            
            self._connected = False
            logger.info("SQLiteStorageBackend disconnected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect SQLiteStorageBackend: {e}")
    
    async def _initialize_connection_pool(self) -> None:
        """初始化连接池"""
        try:
            with self._pool_lock:
                for _ in range(self.connection_pool_size):
                    conn = SQLiteStorageUtils.create_connection(self.db_path, self.timeout)
                    
                    # 配置连接
                    self._configure_connection(conn)
                    
                    # 初始化表
                    SQLiteStorageUtils.initialize_tables(conn)
                    
                    self._connection_pool.append(conn)
                
                self._stats["connection_pool_size"] = len(self._connection_pool)
                
        except Exception as e:
            raise StorageConnectionError(f"Failed to initialize connection pool: {e}")
    
    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """配置连接
        
        Args:
            conn: SQLite连接对象
        """
        try:
            cursor = conn.cursor()
            
            # 设置缓存大小
            cursor.execute(f"PRAGMA cache_size = {self.cache_size}")
            
            # 设置临时存储位置
            if self.temp_store == "memory":
                cursor.execute("PRAGMA temp_store = MEMORY")
            elif self.temp_store == "file":
                cursor.execute("PRAGMA temp_store = FILE")
            
            # 设置同步模式
            cursor.execute(f"PRAGMA synchronous = {self.synchronous_mode}")
            
            # 设置日志模式
            cursor.execute(f"PRAGMA journal_mode = {self.journal_mode}")
            
            # 启用自动清理
            if self.enable_auto_vacuum:
                cursor.execute("PRAGMA auto_vacuum = INCREMENTAL")
            
            # 启用外键约束
            if self.enable_foreign_keys:
                cursor.execute("PRAGMA foreign_keys = ON")
            
            conn.commit()
            
        except Exception as e:
            raise StorageError(f"Failed to configure connection: {e}")
    
    async def _close_connection_pool(self) -> None:
        """关闭连接池"""
        try:
            with self._pool_lock:
                for conn in self._connection_pool:
                    conn.close()
                
                self._connection_pool.clear()
                self._stats["connection_pool_size"] = 0
                
        except Exception as e:
            raise StorageError(f"Failed to close connection pool: {e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """从连接池获取连接
        
        Returns:
            SQLite连接对象
        """
        self._pool_semaphore.acquire()
        
        with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
                self._stats["active_connections"] += 1
                return conn
            else:
                self._pool_semaphore.release()
                raise StorageConnectionError("No available connections in pool")
    
    def _return_connection(self, conn: sqlite3.Connection) -> None:
        """归还连接到连接池
        
        Args:
            conn: SQLite连接对象
        """
        try:
            with self._pool_lock:
                if len(self._connection_pool) < self.connection_pool_size:
                    self._connection_pool.append(conn)
                    self._stats["active_connections"] -= 1
                else:
                    conn.close()
            
            self._pool_semaphore.release()
            
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
    
    async def save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        conn = None
        try:
            # 生成ID（如果没有）
            if "id" not in data:
                import uuid
                data["id"] = str(uuid.uuid4())
            
            item_id: str = data["id"]
            current_time = time.time()
            
            # 序列化数据
            serialized_data = SQLiteStorageUtils.serialize_data(data)
            
            # 获取连接
            conn = self._get_connection()
            
            # 插入或更新记录
            query = """
                INSERT OR REPLACE INTO state_storage 
                (id, data, created_at, updated_at, expires_at, compressed, type, agent_id, thread_id, session_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = [
                item_id,
                serialized_data,
                data.get("created_at", current_time),
                current_time,
                data.get("expires_at"),
                data.get("compressed", 0),
                data.get("type"),
                data.get("agent_id"),
                data.get("thread_id"),
                data.get("session_id"),
                SQLiteStorageUtils.serialize_data(data.get("metadata", {}))
            ]
            
            SQLiteStorageUtils.execute_update(conn, query, params)
            
            self._update_stats("save")
            return item_id
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
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
            query = "SELECT * FROM state_storage WHERE id = ?"
            result = SQLiteStorageUtils.execute_query(conn, query, [id], fetch_one=True)
            
            if not result:
                return None
            
            # 检查是否过期
            if result["expires_at"] and result["expires_at"] < time.time():
                # 删除过期记录
                SQLiteStorageUtils.execute_update(conn, "DELETE FROM state_storage WHERE id = ?", [id])
                self._stats["expired_records_cleaned"] += 1
                return None
            
            # 反序列化数据
            data = SQLiteStorageUtils.deserialize_data(result["data"])
            
            self._update_stats("load")
            return data
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def update_impl(self, id: str, updates: Dict[str, Any]) -> bool:
        """实际更新实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 检查记录是否存在
            existing = SQLiteStorageUtils.execute_query(
                conn, "SELECT id FROM state_storage WHERE id = ?", [id], fetch_one=True
            )
            
            if not existing:
                return False
            
            # 获取当前数据
            current_data = await self.load_impl(id)
            if current_data is None:
                return False
            
            # 更新数据
            current_data.update(updates)
            current_data["updated_at"] = time.time()
            
            # 序列化更新后的数据
            serialized_data = SQLiteStorageUtils.serialize_data(current_data)
            
            # 更新记录
            query = """
                UPDATE state_storage 
                SET data = ?, updated_at = ?, expires_at = ?, compressed = ?, 
                    type = ?, agent_id = ?, thread_id = ?, session_id = ?, metadata = ?
                WHERE id = ?
            """
            
            params = [
                serialized_data,
                current_data["updated_at"],
                current_data.get("expires_at"),
                current_data.get("compressed", 0),
                current_data.get("type"),
                current_data.get("agent_id"),
                current_data.get("thread_id"),
                current_data.get("session_id"),
                SQLiteStorageUtils.serialize_data(current_data.get("metadata", {})),
                id
            ]
            
            SQLiteStorageUtils.execute_update(conn, query, params)
            
            self._update_stats("update")
            return True
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update data {id}: {e}")
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
            query = "DELETE FROM state_storage WHERE id = ?"
            affected_rows = SQLiteStorageUtils.execute_update(conn, query, [id])
            
            self._update_stats("delete")
            return affected_rows > 0
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def list_impl(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """实际列表实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 构建查询
            where_clause, params = SQLiteStorageUtils.build_where_clause(filters)
            
            query = f"SELECT * FROM state_storage {where_clause} ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            # 执行查询
            results = SQLiteStorageUtils.execute_query(conn, query, params)
            
            # 处理结果
            processed_results = []
            for row in results:
                # 检查是否过期
                if row["expires_at"] and row["expires_at"] < time.time():
                    continue
                
                # 反序列化数据
                try:
                    data = SQLiteStorageUtils.deserialize_data(row["data"])
                    processed_results.append(data)
                except Exception as e:
                    logger.error(f"Failed to deserialize data for record {row['id']}: {e}")
                    continue
            
            self._update_stats("list")
            return processed_results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def query_impl(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """实际查询实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 简单的查询实现（基于过滤器）
            if query.startswith("filters:"):
                filters_str = query[8:]  # 移除 "filters:" 前缀
                import json
                filters = json.loads(filters_str) if filters_str else {}
                return await self.list_impl(filters, params.get("limit"))
            
            # 原始SQL查询
            elif query.startswith("sql:"):
                sql_query = query[4:]  # 移除 "sql:" 前缀
                query_params = params.get("params", [])
                results = SQLiteStorageUtils.execute_query(conn, sql_query, query_params)
                
                # 处理结果
                processed_results = []
                for row in results:
                    # 如果包含data字段，反序列化
                    if "data" in row:
                        try:
                            data = SQLiteStorageUtils.deserialize_data(row["data"])
                            # 合并其他字段
                            for key, value in row.items():
                                if key != "data":
                                    data[key] = value
                            processed_results.append(data)
                        except Exception as e:
                            logger.error(f"Failed to deserialize data: {e}")
                            processed_results.append(dict(row))
                    else:
                        processed_results.append(dict(row))
                
                return processed_results
            
            # 其他查询类型暂不支持
            else:
                raise StorageError(f"Unsupported query type: {query}")
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to execute query: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def exists_impl(self, id: str) -> bool:
        """实际存在检查实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 查询记录
            query = "SELECT id, expires_at FROM state_storage WHERE id = ?"
            result = SQLiteStorageUtils.execute_query(conn, query, [id], fetch_one=True)
            
            if not result:
                return False
            
            # 检查是否过期
            if result["expires_at"] and result["expires_at"] < time.time():
                # 删除过期记录
                SQLiteStorageUtils.execute_update(conn, "DELETE FROM state_storage WHERE id = ?", [id])
                self._stats["expired_records_cleaned"] += 1
                return False
            
            return True
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to check existence of data {id}: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def count_impl(self, filters: Dict[str, Any]) -> int:
        """实际计数实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 构建查询
            where_clause, params = SQLiteStorageUtils.build_where_clause(filters)
            
            query = f"SELECT COUNT(*) as count FROM state_storage {where_clause}"
            
            # 执行查询
            result = SQLiteStorageUtils.execute_query(conn, query, params, fetch_one=True)
            
            return result["count"] if result else 0
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to count data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def transaction_impl(self, operations: List[Dict[str, Any]]) -> bool:
        """实际事务实现"""
        conn = None
        try:
            # 获取专用连接
            conn = self._get_connection()
            
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            
            # 执行操作
            for operation in operations:
                op_type = operation.get("type")
                
                if op_type == "save":
                    await self.save_impl(operation["data"])
                elif op_type == "update":
                    await self.update_impl(operation["id"], operation["data"])
                elif op_type == "delete":
                    await self.delete_impl(operation["id"])
                else:
                    raise StorageTransactionError(f"Unknown operation type: {op_type}")
            
            # 提交事务
            conn.commit()
            
            self._update_stats("transaction")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            if isinstance(e, StorageError):
                raise
            raise StorageTransactionError(f"Transaction failed: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def batch_save_impl(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """实际批量保存实现"""
        conn = None
        ids = []
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            
            # 批量插入
            for data in data_list:
                # 生成ID（如果没有）
                if "id" not in data:
                    import uuid
                    data["id"] = str(uuid.uuid4())
                
                item_id = data["id"]
                current_time = time.time()
                
                # 序列化数据
                serialized_data = SQLiteStorageUtils.serialize_data(data)
                
                # 插入记录
                query = """
                    INSERT OR REPLACE INTO state_storage 
                    (id, data, created_at, updated_at, expires_at, compressed, type, agent_id, thread_id, session_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = [
                    item_id,
                    serialized_data,
                    data.get("created_at", current_time),
                    current_time,
                    data.get("expires_at"),
                    data.get("compressed", 0),
                    data.get("type"),
                    data.get("agent_id"),
                    data.get("thread_id"),
                    data.get("session_id"),
                    SQLiteStorageUtils.serialize_data(data.get("metadata", {}))
                ]
                
                conn.execute(query, params)
                ids.append(item_id)
            
            # 提交事务
            conn.commit()
            
            self._update_stats("save")
            return ids
            
        except Exception as e:
            if conn:
                conn.rollback()
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch save data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def batch_delete_impl(self, ids: List[str]) -> int:
        """实际批量删除实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 构建IN查询
            placeholders = ",".join(["?" for _ in ids])
            query = f"DELETE FROM state_storage WHERE id IN ({placeholders})"
            
            # 执行删除
            affected_rows = SQLiteStorageUtils.execute_update(conn, query, ids)
            
            self._update_stats("delete")
            return affected_rows
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch delete data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 计算截止时间
            cutoff_time = time.time() - (retention_days * 24 * 3600)
            
            # 删除旧记录
            query = "DELETE FROM state_storage WHERE created_at < ?"
            affected_rows = SQLiteStorageUtils.execute_update(conn, query, [cutoff_time])
            
            return affected_rows
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    def stream_list_impl(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ):
        """实际流式列表实现"""
        async def _stream():
            conn = None
            try:
                # 获取连接
                conn = self._get_connection()
                
                # 构建查询
                where_clause, params = SQLiteStorageUtils.build_where_clause(filters)
                
                # 使用分页查询
                offset = 0
                while True:
                    query = f"""
                        SELECT * FROM state_storage 
                        {where_clause} 
                        ORDER BY created_at DESC 
                        LIMIT {batch_size} OFFSET {offset}
                    """
                    
                    # 执行查询
                    results = SQLiteStorageUtils.execute_query(conn, query, params)
                    
                    if not results:
                        break
                    
                    # 处理结果
                    batch = []
                    for row in results:
                        # 检查是否过期
                        if row["expires_at"] and row["expires_at"] < time.time():
                            continue
                        
                        # 反序列化数据
                        try:
                            data = SQLiteStorageUtils.deserialize_data(row["data"])
                            batch.append(data)
                        except Exception as e:
                            logger.error(f"Failed to deserialize data for record {row['id']}: {e}")
                            continue
                    
                    if batch:
                        yield batch
                    
                    # 如果结果少于批次大小，说明没有更多数据
                    if len(results) < batch_size:
                        break
                    
                    offset += batch_size
                
            except Exception as e:
                if isinstance(e, StorageError):
                    raise
                raise StorageError(f"Failed to stream list data: {e}")
            finally:
                if conn:
                    self._return_connection(conn)
        
        return _stream()
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 获取数据库信息
            db_info = SQLiteStorageUtils.get_database_info(conn)
            
            # 更新统计信息
            self._stats["database_size_bytes"] = db_info["database_size_bytes"]
            self._stats["total_records"] = db_info["total_records"]
            
            # 清理过期记录
            expired_count = SQLiteStorageUtils.cleanup_expired_records(conn)
            self._stats["expired_records_cleaned"] += expired_count
            
            return {
                "status": "healthy",
                "database_path": self.db_path,
                "database_size_bytes": self._stats["database_size_bytes"],
                "database_size_mb": db_info["database_size_mb"],
                "total_records": self._stats["total_records"],
                "connection_pool_size": self._stats["connection_pool_size"],
                "active_connections": self._stats["active_connections"],
                "expired_records_cleaned": self._stats["expired_records_cleaned"],
                "backup_count": self._stats["backup_count"],
                "last_backup_time": self._stats["last_backup_time"],
                "total_operations": self._stats["total_operations"],
                "config": {
                    "timeout": self.timeout,
                    "enable_wal_mode": self.enable_wal_mode,
                    "enable_foreign_keys": self.enable_foreign_keys,
                    "connection_pool_size": self.connection_pool_size,
                    "enable_backup": self.enable_backup,
                    "backup_interval_hours": self.backup_interval_hours
                }
            }
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def _backup_worker(self) -> None:
        """备份工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.backup_interval_hours * 3600)
                
                current_time = time.time()
                if current_time - self._last_backup_time >= self.backup_interval_hours * 3600:
                    await self._create_backup()
                    self._last_backup_time = int(current_time)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in backup task: {e}")
    
    async def _create_backup(self) -> None:
        """创建数据库备份"""
        try:
            # 确保备份目录存在
            backup_dir = Path(self.backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"storage_backup_{timestamp}.db"
            
            # 获取连接并创建备份
            conn = self._get_connection()
            try:
                SQLiteStorageUtils.backup_database(conn, str(backup_file))
                
                # 更新统计信息
                self._stats["backup_count"] += 1
                self._stats["last_backup_time"] = time.time()
                
                logger.info(f"Created backup: {backup_file}")
                
                # 清理旧备份
                await self._cleanup_old_backups()
                
            finally:
                self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    async def _cleanup_old_backups(self) -> None:
        """清理旧备份文件"""
        try:
            backup_dir = Path(self.backup_path)
            if not backup_dir.exists():
                return
            
            # 获取所有备份文件
            backup_files = list(backup_dir.glob("storage_backup_*.db"))
            
            # 按修改时间排序
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # 删除超出限制的备份文件
            if len(backup_files) > self.max_backup_files:
                for backup_file in backup_files[self.max_backup_files:]:
                    backup_file.unlink()
                    logger.debug(f"Deleted old backup: {backup_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")