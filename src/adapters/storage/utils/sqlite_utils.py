"""SQLite存储工具类

提供SQLite存储相关的静态工具方法。
"""

import json
import sqlite3
import threading
import time
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from src.core.state.exceptions import StorageError, StorageConnectionError
from .common_utils import StorageCommonUtils


logger = logging.getLogger(__name__)


class SQLiteStorageUtils:
    """SQLite存储工具类
    
    提供SQLite存储特定的静态工具方法。
    """
    
    # 数据序列化/反序列化方法已移到 StorageCommonUtils
    serialize_data = StorageCommonUtils.serialize_data
    deserialize_data = StorageCommonUtils.deserialize_data
    
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
    def serialize_data(data: Dict[str, Any]) -> str:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            
        Returns:
            序列化后的JSON字符串
        """
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    @staticmethod
    def deserialize_data(data: str) -> Dict[str, Any]:
        """反序列化数据
        
        Args:
            data: 要反序列化的JSON字符串
            
        Returns:
            反序列化后的数据
        """
        result = json.loads(data)
        if isinstance(result, dict):
            return result
        raise ValueError(f"Expected dict, got {type(result)}")
    
    @staticmethod
    def build_where_clause(filters: Dict[str, Any]) -> tuple:
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
    
    @staticmethod
    def cleanup_expired_records(conn: sqlite3.Connection) -> int:
        """清理过期记录
        
        Args:
            conn: SQLite连接对象
            
        Returns:
            清理的记录数
        """
        try:
            current_time = time.time()
            query = "DELETE FROM state_storage WHERE expires_at IS NOT NULL AND expires_at < ?"
            return SQLiteStorageUtils.execute_update(conn, query, [current_time])
            
        except Exception as e:
            raise StorageError(f"Failed to cleanup expired records: {e}")
    
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
    
    @staticmethod
    def backup_database(conn: sqlite3.Connection, backup_path: str) -> None:
        """备份数据库
        
        Args:
            conn: SQLite连接对象
            backup_path: 备份文件路径
        """
        try:
            # 确保备份目录存在
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 创建备份连接
            backup_conn = sqlite3.connect(backup_path)
            
            # 执行备份
            conn.backup(backup_conn)
            
            # 关闭备份连接
            backup_conn.close()
            
        except Exception as e:
            raise StorageError(f"Failed to backup database: {e}")
    
    @staticmethod
    def restore_database(backup_path: str, target_path: str) -> None:
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
            target_path: 目标数据库路径
        """
        try:
            # 确保目标目录存在
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 复制备份文件
            import shutil
            shutil.copy2(backup_path, target_path)
            
        except Exception as e:
            raise StorageError(f"Failed to restore database: {e}")