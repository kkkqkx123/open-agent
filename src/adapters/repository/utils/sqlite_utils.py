"""SQLite处理工具类

提供Repository中SQLite操作的通用方法。
"""

import sqlite3
from src.interfaces.dependency_injection import get_logger
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .json_utils import JsonUtils

logger = get_logger(__name__)


class SQLiteUtils:
    """SQLite处理工具类"""
    
    @staticmethod
    def init_database(db_path: str, table_sql: str, indexes_sql: Optional[List[str]] = None) -> None:
        """初始化数据库表
        
        Args:
            db_path: 数据库文件路径
            table_sql: 创建表的SQL语句
            indexes_sql: 创建索引的SQL语句列表
        """
        try:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                conn.execute(table_sql)
                
                if indexes_sql:
                    for index_sql in indexes_sql:
                        conn.execute(index_sql)
                
                conn.commit()
                logger.info(f"SQLite数据库初始化完成: {db_path}")
        except Exception as e:
            logger.error(f"初始化SQLite数据库失败: {e}")
            raise
    
    @staticmethod
    def execute_query(db_path: str, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """执行查询语句
        
        Args:
            db_path: 数据库文件路径
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query, params or ())
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
    
    @staticmethod
    def execute_update(db_path: str, query: str, params: Optional[Tuple] = None) -> int:
        """执行更新语句
        
        Args:
            db_path: 数据库文件路径
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            影响的行数
        """
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"执行更新失败: {e}")
            raise
    
    @staticmethod
    def insert_or_replace(db_path: str, table: str, data: Dict[str, Any]) -> None:
        """插入或替换数据
        
        Args:
            db_path: 数据库文件路径
            table: 表名
            data: 要插入的数据
        """
        try:
            columns = list(data.keys())
            placeholders = ["?"] * len(columns)
            values = list(data.values())
            
            query = f"""
                INSERT OR REPLACE INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            SQLiteUtils.execute_update(db_path, query, tuple(values))
        except Exception as e:
            logger.error(f"插入或替换数据失败: {e}")
            raise
    
    @staticmethod
    def delete_by_id(db_path: str, table: str, id_field: str, id_value: str) -> bool:
        """根据ID删除记录
        
        Args:
            db_path: 数据库文件路径
            table: 表名
            id_field: ID字段名
            id_value: ID值
            
        Returns:
            是否删除成功
        """
        try:
            query = f"DELETE FROM {table} WHERE {id_field} = ?"
            affected_rows = SQLiteUtils.execute_update(db_path, query, (id_value,))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"根据ID删除记录失败: {e}")
            raise
    
    @staticmethod
    def find_by_id(db_path: str, table: str, id_field: str, id_value: str) -> Optional[Tuple]:
        """根据ID查找记录
        
        Args:
            db_path: 数据库文件路径
            table: 表名
            id_field: ID字段名
            id_value: ID值
            
        Returns:
            查找结果，未找到返回None
        """
        try:
            query = f"SELECT * FROM {table} WHERE {id_field} = ?"
            results = SQLiteUtils.execute_query(db_path, query, (id_value,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"根据ID查找记录失败: {e}")
            raise
    
    @staticmethod
    def count_records(db_path: str, table: str, condition: str = "", params: Optional[Tuple] = None) -> int:
        """统计记录数
        
        Args:
            db_path: 数据库文件路径
            table: 表名
            condition: 查询条件
            params: 条件参数
            
        Returns:
            记录数
        """
        try:
            query = f"SELECT COUNT(*) FROM {table}"
            if condition:
                query += f" WHERE {condition}"
            
            results = SQLiteUtils.execute_query(db_path, query, params)
            return results[0][0] if results else 0
        except Exception as e:
            logger.error(f"统计记录数失败: {e}")
            raise
    
    @staticmethod
    def get_top_records(db_path: str, table: str, group_field: str, order_field: str, limit: int = 10) -> List[Tuple]:
        """获取分组统计的前N条记录
        
        Args:
            db_path: 数据库文件路径
            table: 表名
            group_field: 分组字段
            order_field: 排序字段
            limit: 返回记录数
            
        Returns:
            统计结果列表
        """
        try:
            query = f"""
                SELECT {group_field}, COUNT(*) as count
                FROM {table}
                GROUP BY {group_field}
                ORDER BY count DESC
                LIMIT ?
            """
            
            return SQLiteUtils.execute_query(db_path, query, (limit,))
        except Exception as e:
            logger.error(f"获取分组统计失败: {e}")
            raise