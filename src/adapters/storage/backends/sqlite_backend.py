"""优化的SQLite存储后端

提供基于SQLite的存储后端实现，使用增强基类减少重复代码。
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
from ..adapters.base import StorageBackend, ConnectionPooledStorageBackend, ConnectionPoolMixin
from ..utils.common_utils import StorageCommonUtils
from ..utils.memory_optimizer import get_global_optimizer


logger = get_logger(__name__)


class SQLiteStorageBackend(ConnectionPooledStorageBackend):
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
                - 其他StorageBackend配置参数
        """
        # 初始化带连接池的基类
        pool_size = config.get("connection_pool_size", 5)
        super().__init__(pool_size=pool_size, **config)
        
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
        
        # 事务相关
        self._transaction_active = False
        self._transaction_connection: Optional[sqlite3.Connection] = None
        
        # 扩展统计信息
        self._stats.update({
            "connection_pool_size": 0,
            "active_connections": 0,
            "database_size_bytes": 0,
            "total_records": 0,
            "expired_records_cleaned": 0,
        })
        
        logger.info(f"SQLiteStorageBackend initialized with db_path: {self.db_path}")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 初始化连接池（使用本地实现）
            await self._initialize_sqlite_connection_pool()
            
            # 调用父类连接逻辑（启动清理和备份任务）
            await ConnectionPooledStorageBackend.connect(self)
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect SQLiteStorageBackend: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 调用父类断开逻辑
            await StorageBackend.disconnect(self)
            
            # 关闭连接池
            self._close_connection_pool()
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect SQLiteStorageBackend: {e}")
    
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
    
    async def save_impl(self, data: Union[Dict[str, Any], bytes], compressed: bool = False) -> str:
        """实际保存实现"""
        conn = None
        try:
            # 生成ID（如果没有）
            if isinstance(data, dict):
                item_id = StorageCommonUtils.validate_data_id(data)
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
                    int(compressed),
                    data.get("type"),
                    data.get("thread_id"),
                    data.get("session_id"),
                    StorageCommonUtils.serialize_data(data.get("metadata", {}))
                ]
                
                affected_rows = self._execute_update(conn, query, params)
                
                if affected_rows > 0:
                    self._update_stats("save")
                
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
    
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
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
                self._stats["expired_records_cleaned"] += 1
                return None
            
            # 反序列化数据
            data_str = result.get("data")
            if not isinstance(data_str, str):
                raise StorageError(f"Invalid data type in database: {type(data_str)}")
            data = StorageCommonUtils.deserialize_data(data_str)
            
            self._update_stats("load")
            return data
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
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
            affected_rows = self._execute_update(conn, query, [id])
            
            if affected_rows > 0:
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
            
            self._update_stats("list")
            return processed_results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def stream_list_impl(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100,
        max_memory_mb: int = 100
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
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
                    if len(batch) >= current_batch_size or memory_usage >= max_memory_mb:
                        yield batch
                        batch = []
                        memory_usage = 0
                        
                except Exception as e:
                    logger.error(f"Failed to deserialize data for record {row_dict.get('id', 'unknown')}: {e}")
                    continue
            
            # 更新统计信息
            self._update_stats("list")
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to stream list data: {e}")
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
            self._stats["total_records"] = db_info["total_records"]
            
            # 清理过期记录
            expired_count = self._cleanup_expired_records(conn)
            self._stats["expired_records_cleaned"] += expired_count
            
            # 使用健康检查助手准备响应
            from src.core.state.statistics import DatabaseStorageStatistics, HealthCheckHelper
            import time as time_module
            stats = DatabaseStorageStatistics(
                status="healthy",
                timestamp=time_module.time(),
                total_size_bytes=self._stats["database_size_bytes"],
                total_size_mb=round(self._stats["database_size_bytes"] / (1024 * 1024), 2),
                total_records=self._stats["total_records"],
                database_path=self.db_path,
                page_count=db_info.get("page_count", 0),
                page_size=4096,
            )
            return HealthCheckHelper.prepare_health_check_response(
                status="healthy",
                stats=stats,
                config={
                    "timeout": self.timeout,
                    "enable_wal_mode": self.enable_wal_mode,
                    "enable_foreign_keys": self.enable_foreign_keys,
                    "connection_pool_size": self._pool_size,
                    "enable_backup": self.enable_backup,
                    "backup_interval_hours": self.backup_interval_hours
                },
                database_path=self.db_path,
                database_size_bytes=self._stats["database_size_bytes"],
                database_size_mb=db_info["database_size_mb"],
                total_records=self._stats["total_records"],
                connection_pool_size=self._stats["connection_pool_size"],
                active_connections=self._active_connections,
            )
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
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
            backup_strategy.cleanup_old_backups(str(backup_dir), self.max_backup_files)
            
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
            
            self._stats["expired_items_cleaned"] += affected_rows
            
            if affected_rows > 0:
                logger.debug(f"Cleaned {affected_rows} expired items from SQLite")
                
        except Exception as e:
            logger.error(f"Error cleaning expired items in SQLite: {e}")
        finally:
            if conn:
                self._return_connection(conn)