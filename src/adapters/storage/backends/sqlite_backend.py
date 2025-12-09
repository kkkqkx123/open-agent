"""优化的SQLite存储后端

提供基于SQLite的存储后端实现，使用新的基类和基础设施组件。
"""

import asyncio
import sqlite3
import threading
import time
from src.services.logger.injection import get_logger
from typing import Dict, Any, Optional, List, Union, AsyncIterator, AsyncGenerator
from pathlib import Path

from src.interfaces.storage.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageCapacityError
)
from .base import BaseStorageBackend
from ..utils.common_utils import StorageCommonUtils
from ..utils.memory_optimizer import get_global_optimizer


logger = get_logger(__name__)


class SQLiteStorageBackend(BaseStorageBackend):
    """优化的SQLite存储后端实现
    
    提供基于SQLite的存储后端，支持持久化、事务、索引等功能。
    使用增强基类减少重复代码，继承自ConnectionPooledStorageBackend以获得连接池支持。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化SQLite存储
        
        Args:
            **config: 配置参数，包括：
                - db_path: 数据库文件路径
                - connection_pool_size: 连接池大小 (默认5)
                - timeout: 连接超时时间 (默认30秒)
                - enable_wal_mode: 是否启用WAL模式 (默认True)
                - 其他BaseStorageBackend配置参数
        """
        # 初始化基类
        super().__init__(**config)
        
        # SQLite特定配置
        self.db_path = config.get("db_path", "storage.db")
        self.timeout = config.get("timeout", 30.0)
        self.enable_wal_mode = config.get("enable_wal_mode", True)
        self.enable_foreign_keys = config.get("enable_foreign_keys", True)
        self.enable_auto_vacuum = config.get("enable_auto_vacuum", False)
        self.cache_size = config.get("cache_size", 2000)
        self.temp_store = config.get("temp_store", "memory")  # memory, file, default
        self.synchronous_mode = config.get("synchronous_mode", "NORMAL")  # OFF, NORMAL, FULL, EXTRA
        self.journal_mode = config.get("journal_mode", "WAL")  # DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF
        self.backup_path = config.get("backup_path", "backups")
        
        # 连接池相关
        self._connection_pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()
        self._pool_size = config.get("connection_pool_size", 5)
        self._active_connections = 0
        
        # 事务相关
        self._transaction_active = False
        self._transaction_connection: Optional[sqlite3.Connection] = None
        
        logger.info(f"SQLiteStorageBackend initialized with db_path: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """从连接池获取连接"""
        with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
                self._active_connections += 1
                return conn
            else:
                raise StorageConnectionError("No available connections in pool")
    
    def _return_connection(self, conn: sqlite3.Connection) -> None:
        """归还连接到连接池"""
        try:
            with self._pool_lock:
                if len(self._connection_pool) < self._pool_size:
                    self._connection_pool.append(conn)
                    self._active_connections -= 1
                else:
                    # 连接池满，关闭连接
                    conn.close()
                    self._active_connections -= 1
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
    
    def _close_connection_pool(self) -> None:
        """关闭连接池中的所有连接"""
        try:
            with self._pool_lock:
                for conn in self._connection_pool:
                    try:
                        conn.close()
                    except Exception as e:
                        logger.error(f"Error closing connection: {e}")
                
                self._connection_pool.clear()
                self._active_connections = 0
                logger.info("Closed all connections in pool")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # 初始化连接池
        await self._initialize_sqlite_connection_pool()
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        # 关闭连接池
        self._close_connection_pool()
    
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
                
                logger.info(f"Initialized connection pool with {len(self._connection_pool)} connections")
                
        except Exception as e:
            raise StorageConnectionError(f"Failed to initialize connection pool: {e}")
    
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
            raise StorageConnectionError(f"Failed to create SQLite connection: {e}")
    
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
    
    def _initialize_tables(self, conn: sqlite3.Connection) -> None:
        """初始化数据库表"""
        try:
            cursor = conn.cursor()
            
            # 创建状态存储表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS state_storage (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL,
                    compressed INTEGER DEFAULT 0,
                    type TEXT,
                    thread_id TEXT,
                    session_id TEXT,
                    metadata TEXT
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_type ON state_storage(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_thread_id ON state_storage(thread_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_session_id ON state_storage(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_expires_at ON state_storage(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_created_at ON state_storage(created_at)")
            
            # 提交更改
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise StorageError(f"Failed to initialize database tables: {e}")
    
    async def _save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        conn = None
        try:
            # 生成ID（如果没有）
            if isinstance(data, dict):
                item_id = data.get("id") or StorageCommonUtils.validate_data_id(data)
                current_time = time.time()
                
                # 序列化数据
                serialized_data = StorageCommonUtils.serialize_data(data)
                
                # 获取连接
                conn = self._get_connection()
                
                # 插入或更新记录
                query = """
                    INSERT OR REPLACE INTO state_storage
                    (id, data, created_at, updated_at, expires_at, compressed, type, thread_id, session_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = [
                    item_id,
                    serialized_data,
                    data.get("created_at", current_time),
                    current_time,
                    data.get("expires_at"),
                    0,  # compressed flag
                    data.get("type"),
                    data.get("thread_id"),
                    data.get("session_id"),
                    StorageCommonUtils.serialize_data(data.get("metadata", {}))
                ]
                
                affected_rows = self._execute_update(conn, query, params)
                return item_id
            else:
                raise StorageError(f"Expected dict for data, got {type(data)}")
                
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def _load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 查询记录
            query = "SELECT * FROM state_storage WHERE id = ?"
            result = self._execute_query(conn, query, [id], fetch_one=True)
            
            if not result or not isinstance(result, dict):
                return None
            
            # 检查是否过期
            expires_at = result.get("expires_at")
            if expires_at and isinstance(expires_at, (int, float)) and expires_at < time.time():
                # 删除过期记录
                self._execute_update(conn, "DELETE FROM state_storage WHERE id = ?", [id])
                # 过期记录清理完成
                return None
            
            # 反序列化数据
            data_str = result.get("data")
            if not isinstance(data_str, str):
                raise StorageError(f"Invalid data type in database: {type(data_str)}")
            data = StorageCommonUtils.deserialize_data(data_str)
            
            return data
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def _delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 删除记录
            query = "DELETE FROM state_storage WHERE id = ?"
            affected_rows = self._execute_update(conn, query, [id])
            
            return affected_rows > 0
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def _list_impl(
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
            where_clause, params = self._build_where_clause(filters)
            
            query = f"SELECT * FROM state_storage {where_clause} ORDER BY created_at DESC"
            
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
                        data_str = row.get("data")
                        if not isinstance(data_str, str):
                            logger.error(f"Invalid data type in record {row.get('id', 'unknown')}: {type(data_str)}")
                            continue
                        data = StorageCommonUtils.deserialize_data(data_str)
                        processed_results.append(data)
                    except Exception as e:
                        logger.error(f"Failed to deserialize data for record {row.get('id', 'unknown')}: {e}")
                        continue
            
            return processed_results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    def _stream_list_impl(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列表实现
        
        使用数据库游标进行真正的流式处理，避免一次性加载所有数据到内存。
        集成内存优化器，根据内存使用情况自适应调整批次大小。
        
        Args:
            filters: 过滤条件
            batch_size: 每批处理的记录数
            max_memory_mb: 最大内存使用限制（MB）
            
        Returns:
            异步生成器，每次产生一批数据
        """
        return self._stream_list_impl_async(filters, batch_size)
    
    async def _stream_list_impl_async(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列表异步实现"""
        conn = None
        try:
            # 获取内存优化器
            memory_optimizer = get_global_optimizer()
            
            # 获取连接
            conn = self._get_connection()
            
            # 构建查询
            where_clause, params = self._build_where_clause(filters)
            query = f"SELECT * FROM state_storage {where_clause} ORDER BY created_at DESC"
            
            # 创建游标
            cursor = conn.cursor()
            
            # 执行查询
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 流式处理结果
            batch: List[Dict[str, Any]] = []
            memory_usage: float = 0.0
            current_batch_size = batch_size
            record_count = 0
            
            while True:
                # 获取一行
                row = cursor.fetchone()
                if not row:
                    # 处理最后一批
                    if batch:
                        yield batch
                    break
                
                # 转换为字典
                row_dict = dict(row)
                
                # 检查是否过期
                expires_at = row_dict.get("expires_at")
                if expires_at and isinstance(expires_at, (int, float)) and expires_at < time.time():
                    continue
                
                # 反序列化数据
                try:
                    data_str = row_dict.get("data")
                    if not isinstance(data_str, str):
                        logger.error(f"Invalid data type in record {row_dict.get('id', 'unknown')}: {type(data_str)}")
                        continue
                    
                    data = StorageCommonUtils.deserialize_data(data_str)
                    batch.append(data)
                    record_count += 1
                    
                    # 估算内存使用（简单估算）
                    record_size = len(str(data)) / (1024 * 1024)  # MB
                    memory_usage += record_size
                    
                    # 检查是否需要调整批次大小
                    if record_count % 10 == 0:  # 每10条记录检查一次
                        # 获取最优批次大小
                        optimal_batch_size = memory_optimizer.get_optimal_batch_size(
                            data_size_hint=int(record_size * 1024) if record_size > 0 else None
                        )
                        
                        # 如果最优批次大小与当前不同，调整当前批次大小
                        if optimal_batch_size != current_batch_size:
                            logger.debug(f"Adjusting batch size from {current_batch_size} to {optimal_batch_size}")
                            current_batch_size = optimal_batch_size
                    
                    # 检查是否达到批次大小或内存限制
                    if len(batch) >= current_batch_size:
                        yield batch
                        batch = []
                        memory_usage = 0
                        
                except Exception as e:
                    logger.error(f"Failed to deserialize data for record {row_dict.get('id', 'unknown')}: {e}")
                    continue
            
            # 流式处理完成
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to stream list data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 获取数据库信息
            db_info = self._get_database_info(conn)
            
            # 清理过期记录
            expired_count = self._cleanup_expired_records(conn)
            
            # 返回健康检查信息
            return {
                "status": "healthy",
                "database_path": self.db_path,
                "database_size_bytes": db_info["database_size_bytes"],
                "database_size_mb": db_info["database_size_mb"],
                "total_records": db_info["total_records"],
                "expired_records_cleaned": expired_count,
                "config": {
                    "timeout": self.timeout,
                    "enable_wal_mode": self.enable_wal_mode,
                    "enable_foreign_keys": self.enable_foreign_keys,
                    "connection_pool_size": self._pool_size,
                }
            }
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def _cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 计算截止时间
            cutoff_time = StorageCommonUtils.calculate_cutoff_time(retention_days)
            
            # 删除旧记录
            query = "DELETE FROM state_storage WHERE created_at < ?"
            affected_rows = self._execute_update(conn, query, [cutoff_time])
            
            return affected_rows
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
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
        """执行查询
        
        Args:
            conn: SQLite连接对象
            query: SQL查询语句
            params: 查询参数
            fetch_one: 是否只获取一条记录
            fetch_all: 是否获取所有记录
            
        Returns:
            查询结果
        """
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
            raise StorageError(f"Failed to execute query: {e}")
    
    def _execute_update(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: Optional[List[Any]] = None
    ) -> int:
        """执行更新操作
        
        Args:
            conn: SQLite连接对象
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
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
            raise StorageError(f"Failed to execute update: {e}")
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> tuple:
        """构建WHERE子句
        
        Args:
            filters: 过滤条件
            
        Returns:
            (where_clause, params) WHERE子句和参数
        """
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
        """获取数据库信息
        
        Args:
            conn: SQLite连接对象
            
        Returns:
            数据库信息
        """
        try:
            cursor = conn.cursor()
            
            # 获取表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 获取记录数
            cursor.execute("SELECT COUNT(*) FROM state_storage")
            total_records = cursor.fetchone()[0]
            
            # 获取数据库大小
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            return {
                "tables": tables,
                "total_records": total_records,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            raise StorageError(f"Failed to get database info: {e}")
    
    def _cleanup_expired_records(self, conn: sqlite3.Connection) -> int:
        """清理过期记录
        
        Args:
            conn: SQLite连接对象
            
        Returns:
            清理的记录数
        """
        try:
            current_time = time.time()
            query = "DELETE FROM state_storage WHERE expires_at IS NOT NULL AND expires_at < ?"
            return self._execute_update(conn, query, [current_time])
            
        except Exception as e:
            raise StorageError(f"Failed to cleanup expired records: {e}")
    
    async def _create_backup_impl(self) -> None:
        """创建数据库备份的具体实现
        
        执行实际的SQLite数据库备份操作。
        """
        # 确保备份目录存在
        backup_dir = Path(self.backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成备份文件名
        backup_file = backup_dir / StorageCommonUtils.generate_timestamp_filename("storage_backup", "db")
        
        # 获取连接并创建备份
        conn = self._get_connection()
        try:
            # 执行备份
            backup_conn = sqlite3.connect(str(backup_file))
            conn.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"Created SQLite backup: {backup_file}")
            
            # 清理旧备份
            from src.core.state.backup_policy import FileBackupStrategy
            backup_strategy = FileBackupStrategy()
            backup_strategy.cleanup_old_backups(str(backup_dir), self._config.get("max_backup_files", 7))
            
        finally:
            self._return_connection(conn)
    
    async def _cleanup_expired_items_impl(self) -> None:
        """清理过期项的SQLite特定实现
        
        使用SQL DELETE语句一次性清理所有过期项，比逐个删除更高效。
        """
        conn = None
        try:
            conn = self._get_connection()
            current_time = time.time()
            
            # 使用SQL直接删除过期项
            query = "DELETE FROM state_storage WHERE expires_at IS NOT NULL AND expires_at < ?"
            affected_rows = self._execute_update(conn, query, [current_time])
            
            # 过期记录清理完成
            
            if affected_rows > 0:
                logger.debug(f"Cleaned {affected_rows} expired items from SQLite")
                
        except Exception as e:
            logger.error(f"Error cleaning expired items in SQLite: {e}")
        finally:
            if conn:
                self._return_connection(conn)