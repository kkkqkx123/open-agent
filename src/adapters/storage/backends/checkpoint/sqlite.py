"""Checkpoint SQLite存储后端

提供基于SQLite的checkpoint存储实现，实现IThreadCheckpointStorage接口。
"""

import sqlite3
import time
import uuid
from typing import Dict, Any, Optional, List, Union, cast, Sequence, Iterator
from pathlib import Path
import threading
from datetime import datetime

from src.core.threads.checkpoints.models import ThreadCheckpoint, CheckpointMetadata
from src.core.threads.checkpoints.extensions import ThreadCheckpointExtension
from src.interfaces.threads.checkpoint import IThreadCheckpointStorage
from src.services.logger.injection import get_logger
from src.interfaces.threads.checkpoint import (
    CheckpointValidationError,
    CheckpointNotFoundError,
    CheckpointStorageError,
)

from src.core.threads.checkpoints.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointStatistics
)


logger = get_logger(__name__)


class CheckpointSqliteBackend(IThreadCheckpointStorage):
    """Checkpoint SQLite存储后端实现

    提供基于SQLite的checkpoint存储功能，实现IThreadCheckpointStorage接口。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化checkpoint SQLite存储
        """
        # SQLite特定配置
        self.db_path = config.get("db_path", "checkpoints.db")
        self.timeout = config.get("timeout", 30.0)
        self.enable_wal_mode = config.get("enable_wal_mode", True)
        self.enable_foreign_keys = config.get("enable_foreign_keys", True)
        
        # 连接池配置
        self._pool_size = config.get("connection_pool_size", 5)
        self._connection_pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()
        self._pool_semaphore = threading.Semaphore(self._pool_size)
        self._active_connections = 0
        
        # 扩展统计信息
        self._stats: Dict[str, Any] = {
            "database_size_bytes": 0,
            "total_checkpoints": 0,
            "expired_checkpoints_cleaned": 0,
            "connection_pool_size": 0,
            "active_connections": 0,
        }
        
        # 连接状态
        self._connected = False
        self._config = config
        
        # 初始化数据库
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """从连接池获取连接"""
        self._pool_semaphore.acquire()
        
        with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
                self._active_connections += 1
                return conn
            else:
                self._pool_semaphore.release()
                raise CheckpointStorageError("No available connections in pool")
    
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
                    
                self._pool_semaphore.release()
                
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
    
    async def connect(self) -> None:
        """连接到SQLite数据库"""
        try:
            if self._connected:
                return
            
            # 初始化连接池
            for _ in range(self._pool_size):
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=self.timeout,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                self._connection_pool.append(conn)
            
            self._stats["connection_pool_size"] = len(self._connection_pool)
            self._connected = True
            logger.info(f"Connected to SQLite database: {self.db_path}")
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to connect to SQLite: {e}")
    
    async def disconnect(self) -> None:
        """断开与SQLite数据库的连接"""
        try:
            if not self._connected:
                return
            
            self._close_connection_pool()
            self._connected = False
            logger.info("Disconnected from SQLite database")
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to disconnect from SQLite: {e}")
    
    def _initialize_database(self) -> None:
        """初始化数据库表结构"""
        conn = None
        try:
            # 确保数据库目录存在
            db_path = Path(self.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            
            # 启用WAL模式和外键约束
            if self.enable_wal_mode:
                conn.execute("PRAGMA journal_mode=WAL")
            if self.enable_foreign_keys:
                conn.execute("PRAGMA foreign_keys=ON")
            
            # 创建checkpoint存储表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoint_storage (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    checkpoint_data TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    channel_values TEXT NOT NULL,
                    channel_versions TEXT NOT NULL,
                    versions_seen TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(thread_id, checkpoint_ns, checkpoint_id)
                )
            """)
            
            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoint_thread_id 
                ON checkpoint_storage(thread_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoint_created_at 
                ON checkpoint_storage(created_at)
            """)
            
            # 创建线程checkpoint表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS thread_checkpoints (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (checkpoint_id) REFERENCES checkpoint_storage(id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_thread_checkpoints_thread_id 
                ON thread_checkpoints(thread_id)
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise CheckpointStorageError(f"Failed to initialize database: {e}")
        finally:
            if conn:
                conn.close()
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点"""
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"]["checkpoint_ns"]
            checkpoint_id = config["configurable"].get("checkpoint_id")
            
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                if checkpoint_id:
                    # 获取特定检查点
                    cursor.execute("""
                        SELECT * FROM checkpoint_storage 
                        WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                    """, (thread_id, checkpoint_ns, checkpoint_id))
                else:
                    # 获取最新检查点
                    cursor.execute("""
                        SELECT * FROM checkpoint_storage 
                        WHERE thread_id = ? AND checkpoint_ns = ?
                        ORDER BY created_at DESC LIMIT 1
                    """, (thread_id, checkpoint_ns))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_checkpoint_dict(row)
                return None
                
            finally:
                self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"Failed to get checkpoint: {e}")
            raise CheckpointStorageError(f"获取checkpoint失败: {e}")
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点元组"""
        try:
            checkpoint = self.get(config)
            if checkpoint:
                return {
                    "config": config,
                    "checkpoint": checkpoint,
                    "metadata": checkpoint.get("metadata", {}),
                    "parent_config": None
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint tuple: {e}")
            return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """列出匹配给定条件的检查点"""
        try:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                # 构建查询
                query = "SELECT * FROM checkpoint_storage"
                params = []
                conditions = []
                
                if config:
                    thread_id = config.get("configurable", {}).get("thread_id")
                    checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns")
                    
                    if thread_id:
                        conditions.append("thread_id = ?")
                        params.append(thread_id)
                    if checkpoint_ns:
                        conditions.append("checkpoint_ns = ?")
                        params.append(checkpoint_ns)
                
                if filter:
                    for key, value in filter.items():
                        conditions.append(f"metadata LIKE ?")
                        params.append(f'%"{key}": "{value}"%')
                
                if before:
                    before_time = before.get("step", 0)
                    conditions.append("created_at < ?")
                    params.append(before_time)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    checkpoint_data = self._row_to_checkpoint_dict(row)
                    yield {
                        "config": {
                            "configurable": {
                                "thread_id": row["thread_id"],
                                "checkpoint_ns": row["checkpoint_ns"],
                                "checkpoint_id": row["checkpoint_id"]
                            }
                        },
                        "checkpoint": checkpoint_data,
                        "metadata": checkpoint_data.get("metadata", {}),
                        "parent_config": None
                    }
                    
            finally:
                self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}")
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """存储带有其配置和元数据的检查点"""
        conn = None
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"]["checkpoint_ns"]
            checkpoint_id = config["configurable"].get("checkpoint_id", str(uuid.uuid4()))
            
            # 序列化数据
            import json
            checkpoint_data = json.dumps(checkpoint)
            metadata_data = json.dumps(metadata)
            channel_values = json.dumps(checkpoint.get("channel_values", {}))
            channel_versions = json.dumps(checkpoint.get("channel_versions", {}))
            versions_seen = json.dumps(checkpoint.get("versions_seen", {}))
            
            current_time = time.time()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 插入或更新检查点
            cursor.execute("""
                INSERT OR REPLACE INTO checkpoint_storage (
                    id, thread_id, checkpoint_ns, checkpoint_id,
                    checkpoint_data, metadata, channel_values, channel_versions,
                    versions_seen, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint_id, thread_id, checkpoint_ns, checkpoint_id,
                checkpoint_data, metadata_data, channel_values, channel_versions,
                versions_seen, current_time, current_time
            ))
            
            # 更新配置中的checkpoint_id
            updated_config = config.copy()
            updated_config["configurable"]["checkpoint_id"] = checkpoint_id
            
            conn.commit()
            self._stats["total_checkpoints"] += 1
            
            return updated_config
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to put checkpoint: {e}")
            raise CheckpointValidationError(f"保存checkpoint失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储与检查点关联的中间写入"""
        conn = None
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"]["checkpoint_ns"]
            checkpoint_id = config["configurable"]["checkpoint_id"]
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 创建写入记录表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoint_writes (
                    id TEXT PRIMARY KEY,
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    task_path TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (checkpoint_id) REFERENCES checkpoint_storage(id)
                )
            """)
            
            # 插入写入记录
            for channel, value in writes:
                write_id = str(uuid.uuid4())
                import json
                value_data = json.dumps(value)
                
                cursor.execute("""
                    INSERT INTO checkpoint_writes (
                        id, checkpoint_id, task_id, task_path,
                        channel_name, channel_value, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    write_id, checkpoint_id, task_id, task_path,
                    channel, value_data, time.time()
                ))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to put writes: {e}")
            raise CheckpointStorageError(f"保存写入记录失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    def _row_to_checkpoint_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为检查点字典"""
        import json
        
        checkpoint_data = json.loads(row["checkpoint_data"])
        metadata = json.loads(row["metadata"])
        channel_values = json.loads(row["channel_values"])
        channel_versions = json.loads(row["channel_versions"])
        versions_seen = json.loads(row["versions_seen"])
        
        return {
            "id": row["id"],
            "thread_id": row["thread_id"],
            "checkpoint_ns": row["checkpoint_ns"],
            "checkpoint_id": row["checkpoint_id"],
            "checkpoint_data": checkpoint_data,
            "metadata": metadata,
            "channel_values": channel_values,
            "channel_versions": channel_versions,
            "versions_seen": versions_seen,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    
    # 实现IThreadCheckpointStorage接口
    async def save_thread_checkpoint(self, checkpoint: ThreadCheckpoint) -> str:
        """保存线程检查点"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            current_time = time.time()
            import json
            metadata_data = json.dumps(checkpoint.metadata) if checkpoint.metadata else "{}"
            
            cursor.execute("""
                INSERT OR REPLACE INTO thread_checkpoints (
                    id, thread_id, checkpoint_id, status, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint.id, checkpoint.thread_id, checkpoint.id,
                checkpoint.status.value, current_time, current_time, metadata_data
            ))
            
            conn.commit()
            return checkpoint.id
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise CheckpointStorageError(f"保存线程检查点失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def load_thread_checkpoint(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """加载线程检查点"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM thread_checkpoints WHERE checkpoint_id = ?
            """, (checkpoint_id,))
            
            row = cursor.fetchone()
            if row:
                import json
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                return ThreadCheckpoint(
                    id=row["id"],
                    thread_id=row["thread_id"],
                    state_data={},  # 需要从checkpoint_storage加载
                    status=CheckpointStatus(row["status"]),
                    created_at=datetime.fromtimestamp(row["created_at"]),
                    updated_at=datetime.fromtimestamp(row["updated_at"]),
                    metadata=metadata
                )
            return None
            
        except Exception as e:
            raise CheckpointStorageError(f"加载线程检查点失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def list_thread_checkpoints(
        self, 
        thread_id: str, 
        status: Optional[CheckpointStatus] = None,
        limit: Optional[int] = None
    ) -> List[ThreadCheckpoint]:
        """列出线程检查点"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM thread_checkpoints WHERE thread_id = ?"
            params = [thread_id]
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(str(limit))
            
            cursor.execute(query, params)
            
            checkpoints = []
            for row in cursor.fetchall():
                import json
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                checkpoints.append(ThreadCheckpoint(
                    id=row["id"],
                    thread_id=row["thread_id"],
                    state_data={},  # 需要从checkpoint_storage加载
                    status=CheckpointStatus(row["status"]),
                    created_at=datetime.fromtimestamp(row["created_at"]),
                    updated_at=datetime.fromtimestamp(row["updated_at"]),
                    metadata=metadata
                ))
            
            return checkpoints
            
        except Exception as e:
            raise CheckpointStorageError(f"列出线程检查点失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def delete_thread_checkpoint(self, checkpoint_id: str) -> bool:
        """删除线程检查点"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM thread_checkpoints WHERE checkpoint_id = ?
            """, (checkpoint_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise CheckpointStorageError(f"删除线程检查点失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def get_thread_checkpoint_statistics(self, thread_id: str) -> CheckpointStatistics:
        """获取线程检查点统计信息"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute("""
                SELECT COUNT(*) as total FROM thread_checkpoints WHERE thread_id = ?
            """, (thread_id,))
            total = cursor.fetchone()["total"]
            
            # 按状态分组统计
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM thread_checkpoints 
                WHERE thread_id = ? 
                GROUP BY status
            """, (thread_id,))
            
            status_counts = {}
            for row in cursor.fetchall():
                status_counts[CheckpointStatus(row["status"])] = row["count"]
            
            # 获取最新检查点时间
            cursor.execute("""
                SELECT MAX(created_at) as latest FROM thread_checkpoints WHERE thread_id = ?
            """, (thread_id,))
            latest = cursor.fetchone()["latest"]
            
            stats = CheckpointStatistics(
                total_checkpoints=total
            )
            
            # 设置各状态计数
            stats.active_checkpoints = status_counts.get(CheckpointStatus.ACTIVE, 0)
            stats.expired_checkpoints = status_counts.get(CheckpointStatus.EXPIRED, 0)
            stats.corrupted_checkpoints = status_counts.get(CheckpointStatus.CORRUPTED, 0)
            stats.archived_checkpoints = status_counts.get(CheckpointStatus.ARCHIVED, 0)
            
            return stats
            
        except Exception as e:
            raise CheckpointStorageError(f"获取线程检查点统计失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    async def cleanup_old_thread_checkpoints(self, thread_id: str, retention_days: int) -> int:
        """清理旧的线程检查点"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cutoff_time = time.time() - (retention_days * 24 * 3600)
            
            cursor.execute("""
                DELETE FROM thread_checkpoints 
                WHERE thread_id = ? AND created_at < ?
            """, (thread_id, cutoff_time))
            
            conn.commit()
            return cursor.rowcount
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise CheckpointStorageError(f"清理旧线程检查点失败: {e}")
        finally:
            if conn:
                self._return_connection(conn)