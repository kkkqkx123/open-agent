"""SQLite存储工具类

提供SQLite存储相关的静态工具方法。
"""

import sqlite3
import time
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from src.interfaces.storage.exceptions import StorageError, StorageConnectionError
from src.core.state.filters import SQLiteFilterBuilder

logger = get_logger(__name__)


class SQLiteStorageUtils:
    """SQLite存储工具类
    
    提供SQLite存储特定的静态工具方法。
    """
    
    @staticmethod
    def create_connection(db_path: str, timeout: float = 30.0) -> sqlite3.Connection:
        """创建SQLite连接
        
        Args:
            db_path: 数据库文件路径
            timeout: 连接超时时间
            
        Returns:
            SQLite连接对象
            
        Raises:
            StorageConnectionError: 连接失败
        """
        try:
            # 确保目录存在
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 创建连接
            conn = sqlite3.connect(
                db_path,
                timeout=timeout,
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
    
    @staticmethod
    def initialize_tables(conn: sqlite3.Connection) -> None:
        """初始化数据库表
        
        Args:
            conn: SQLite连接对象
        """
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
                    agent_id TEXT,
                    thread_id TEXT,
                    session_id TEXT,
                    metadata TEXT
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_type ON state_storage(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_agent_id ON state_storage(agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_thread_id ON state_storage(thread_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_session_id ON state_storage(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_expires_at ON state_storage(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_created_at ON state_storage(created_at)")
            
            # 提交更改
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise StorageError(f"Failed to initialize database tables: {e}")
    
    @staticmethod
    def build_where_clause(filters: Dict[str, Any]) -> tuple:
        """构建WHERE子句
        
        委托给 src/core/state/filters.py 中的 SQLiteFilterBuilder。
        
        Args:
            filters: 过滤条件
            
        Returns:
            (where_clause, params) WHERE子句和参数
        """
        builder = SQLiteFilterBuilder()
        return builder.build_where_clause(filters)
    
    @staticmethod
    def execute_query(
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
    
    @staticmethod
    def execute_update(
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
    
    # 过期记录清理已移至 ExpirationManager
    # 使用 ExpirationManager 代替 cleanup_expired_records()
    
    @staticmethod
    def get_database_info(conn: sqlite3.Connection) -> Dict[str, Any]:
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
    
    @staticmethod
    def optimize_database(conn: sqlite3.Connection) -> None:
        """优化数据库
        
        Args:
            conn: SQLite连接对象
        """
        try:
            cursor = conn.cursor()
            
            # 分析表统计信息
            cursor.execute("ANALYZE")
            
            # 清理数据库
            cursor.execute("VACUUM")
            
            conn.commit()
            
        except Exception as e:
            raise StorageError(f"Failed to optimize database: {e}")
    
    # 备份和恢复功能已移至 src/core/state/backup_policy.py
    # 使用 BackupManager(DatabaseBackupStrategy()) 代替 backup_database() 和 restore_database()
    
    @staticmethod
    def configure_connection(conn: sqlite3.Connection, config: Dict[str, Any]) -> None:
        """配置SQLite连接参数
        
        根据配置字典设置各种SQLite PRAGMA选项。
        
        Args:
            conn: SQLite连接对象
            config: 配置字典，包含以下可选键：
                - enable_wal_mode: 是否启用WAL模式 (True)
                - enable_foreign_keys: 是否启用外键约束 (True)
                - enable_auto_vacuum: 是否启用自动清理 (False)
                - cache_size: 缓存页数 (2000)
                - temp_store: 临时存储位置 'memory'|'file'|'default' ('memory')
                - synchronous_mode: 同步模式 'OFF'|'NORMAL'|'FULL'|'EXTRA' ('NORMAL')
                - journal_mode: 日志模式 'DELETE'|'TRUNCATE'|'PERSIST'|'MEMORY'|'WAL'|'OFF' ('WAL')
                - busy_timeout: 忙碌超时时间(毫秒) (30000)
                - query_timeout: 查询超时时间(毫秒) (30000)
        
        Raises:
            StorageError: 配置失败时抛出
        """
        try:
            cursor = conn.cursor()
            
            # WAL模式 - 提高并发性能
            enable_wal = config.get("enable_wal_mode", True)
            if enable_wal:
                cursor.execute("PRAGMA journal_mode = WAL")
            else:
                journal_mode = config.get("journal_mode", "DELETE")
                cursor.execute(f"PRAGMA journal_mode = {journal_mode}")
            
            # 外键约束
            enable_fk = config.get("enable_foreign_keys", True)
            cursor.execute(f"PRAGMA foreign_keys = {'ON' if enable_fk else 'OFF'}")
            
            # 自动清理
            enable_vacuum = config.get("enable_auto_vacuum", False)
            vacuum_mode = 2 if enable_vacuum else 0  # 2 = INCREMENTAL
            cursor.execute(f"PRAGMA auto_vacuum = {vacuum_mode}")
            
            # 缓存大小（页数）
            cache_size = config.get("cache_size", 2000)
            cursor.execute(f"PRAGMA cache_size = -{cache_size}")  # 负数表示字节数
            
            # 临时存储位置
            temp_store = config.get("temp_store", "memory")
            temp_mode = {"memory": 1, "file": 2, "default": 0}.get(temp_store, 1)
            cursor.execute(f"PRAGMA temp_store = {temp_mode}")
            
            # 同步模式
            sync_mode = config.get("synchronous_mode", "NORMAL")
            sync_values = {"OFF": 0, "NORMAL": 1, "FULL": 2, "EXTRA": 3}
            cursor.execute(f"PRAGMA synchronous = {sync_values.get(sync_mode, 1)}")
            
            # 忙碌超时时间（毫秒）
            busy_timeout = config.get("busy_timeout", 30000)
            cursor.execute(f"PRAGMA busy_timeout = {busy_timeout}")
            
            conn.commit()
            logger.debug("SQLite connection configured successfully")
            
        except Exception as e:
            conn.rollback()
            raise StorageError(f"Failed to configure SQLite connection: {e}")
    
    @staticmethod
    def get_database_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
        """获取数据库详细统计信息
        
        获取关于数据库的详细统计信息，包括表统计、索引统计、
        性能指标等。
        
        Args:
            conn: SQLite连接对象
            
        Returns:
            包含以下信息的字典：
                - page_count: 总页数
                - page_size: 每页大小（字节）
                - database_size_bytes: 数据库大小（字节）
                - database_size_mb: 数据库大小（MB）
                - total_records: state_storage表总记录数
                - expired_records: 过期记录数
                - compressed_records: 压缩记录数
                - tables: 所有表列表
                - indexes: 所有索引列表
                - record_stats: 各类型记录统计
                - cache_stats: 缓存统计信息
        
        Raises:
            StorageError: 获取统计信息失败时抛出
        """
        try:
            cursor = conn.cursor()
            stats: Dict[str, Any] = {}
            
            # 页面统计
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            db_size = page_count * page_size
            stats["page_count"] = page_count
            stats["page_size"] = page_size
            stats["database_size_bytes"] = db_size
            stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
            
            # 表统计
            cursor.execute("SELECT COUNT(*) FROM state_storage")
            total_records = cursor.fetchone()[0]
            stats["total_records"] = total_records
            
            # 过期记录统计
            cursor.execute("""
                SELECT COUNT(*) FROM state_storage 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, [time.time()])
            expired_records = cursor.fetchone()[0]
            stats["expired_records"] = expired_records
            
            # 压缩记录统计
            cursor.execute("SELECT COUNT(*) FROM state_storage WHERE compressed = 1")
            compressed_records = cursor.fetchone()[0]
            stats["compressed_records"] = compressed_records
            
            # 表列表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            stats["tables"] = tables
            
            # 索引列表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            stats["indexes"] = indexes
            
            # 按类型统计记录
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM state_storage 
                WHERE type IS NOT NULL 
                GROUP BY type
            """)
            record_stats = {row[0]: row[1] for row in cursor.fetchall()}
            stats["record_stats"] = record_stats
            
            # 缓存统计
            try:
                cursor.execute("PRAGMA cache_stats")
                cache_rows = cursor.fetchall()
                if cache_rows:
                    stats["cache_stats"] = {
                        "pages_in_cache": cache_rows[0][0] if cache_rows[0] else 0,
                        "pages_unused": cache_rows[0][1] if len(cache_rows[0]) > 1 else 0
                    }
            except Exception:
                # 某些SQLite版本不支持cache_stats
                stats["cache_stats"] = {}
            
            return stats
            
        except Exception as e:
            raise StorageError(f"Failed to get database stats: {e}")
    
    @staticmethod
    def get_table_info(conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
        """获取表的详细信息
        
        Args:
            conn: SQLite连接对象
            table_name: 表名
            
        Returns:
            表信息，包含：
                - columns: 列定义列表
                - record_count: 记录数
                - indexes: 表的索引列表
                - size_bytes: 表大小（字节）
        
        Raises:
            StorageError: 获取信息失败时抛出
        """
        try:
            cursor = conn.cursor()
            info: Dict[str, Any] = {}
            
            # 列信息
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "notnull": row[3],
                    "default": row[4],
                    "pk": row[5]
                })
            info["columns"] = columns
            
            # 记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            info["record_count"] = cursor.fetchone()[0]
            
            # 表的索引
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = [row[1] for row in cursor.fetchall()]
            info["indexes"] = indexes
            
            return info
            
        except Exception as e:
            raise StorageError(f"Failed to get table info for {table_name}: {e}")
    
    @staticmethod
    def analyze_query(conn: sqlite3.Connection, query: str) -> List[Dict[str, Any]]:
        """分析SQL查询的执行计划
        
        Args:
            conn: SQLite连接对象
            query: SQL查询语句
            
        Returns:
            执行计划列表
            
        Raises:
            StorageError: 分析失败时抛出
        """
        try:
            cursor = conn.cursor()
            
            # 使用EXPLAIN QUERY PLAN
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor.execute(explain_query)
            
            plan = []
            for row in cursor.fetchall():
                plan.append({
                    "id": row[0],
                    "parent": row[1],
                    "notused": row[2],
                    "detail": row[3]
                })
            
            return plan
            
        except Exception as e:
            raise StorageError(f"Failed to analyze query: {e}")