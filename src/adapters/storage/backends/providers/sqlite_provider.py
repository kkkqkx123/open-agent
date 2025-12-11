"""SQLite存储提供者

提供SQLite数据库的底层存储操作实现。
"""

import asyncio
import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from .base_provider import BaseStorageProvider
from ..core.exceptions import ProviderError


logger = get_logger(__name__)


class SQLiteProvider(BaseStorageProvider):
    """SQLite存储提供者
    
    专注于SQLite数据库的底层存储操作。
    """
    
    def __init__(self, db_path: str = "./data/storage.db", **config: Any) -> None:
        """初始化SQLite提供者
        
        Args:
            db_path: 数据库文件路径
            **config: 其他配置参数
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 连接池
        self._connections = {}
        self._max_connections = config.get("max_connections", 10)
        
        super().__init__(db_path=db_path, **config)
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # SQLite不需要显式连接，按需创建连接
        logger.debug(f"SQLite provider ready for database: {self.db_path}")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        # 关闭所有连接
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to close connection: {e}")
        
        self._connections.clear()
        logger.debug("SQLite provider connections closed")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接
        
        Returns:
            数据库连接
        """
        thread_id = id(asyncio.current_task())
        
        if thread_id not in self._connections:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self._config.get("timeout", 30.0),
                isolation_level=None  # 自动提交模式
            )
            conn.row_factory = sqlite3.Row
            self._connections[thread_id] = conn
        
        return self._connections[thread_id]
    
    async def save(self, table: str, data: Dict[str, Any]) -> str:
        """保存数据到指定表
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            数据ID
        """
        try:
            conn = self._get_connection()
            
            # 确保有ID字段
            if "id" not in data:
                data["id"] = str(time.time()) + str(id(data))
            
            # 构建SQL
            columns = list(data.keys())
            placeholders = ["?"] * len(columns)
            values = [self._serialize_value(data[col]) for col in columns]
            
            sql = f"""
                INSERT OR REPLACE INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            conn.execute(sql, values)
            
            self._record_operation("save", True)
            logger.debug(f"Data saved to {table}: {data['id']}")
            return data["id"]
            
        except Exception as e:
            self._record_operation("save", False)
            raise ProviderError(f"Failed to save data to {table}: {e}", provider_type="sqlite")
    
    async def load(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """从指定表加载数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            数据字典，不存在返回None
        """
        try:
            conn = self._get_connection()
            
            cursor = conn.execute(
                f"SELECT * FROM {table} WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 转换数据
            data = dict(row)
            data = self._deserialize_data(data)
            
            self._record_operation("load", True)
            logger.debug(f"Data loaded from {table}: {id}")
            return data
            
        except Exception as e:
            self._record_operation("load", False)
            raise ProviderError(f"Failed to load data from {table}: {e}", provider_type="sqlite")
    
    async def update(self, table: str, id: str, updates: Dict[str, Any]) -> bool:
        """更新指定表中的数据
        
        Args:
            table: 表名
            id: 数据ID
            updates: 更新内容
            
        Returns:
            是否更新成功
        """
        try:
            conn = self._get_connection()
            
            if not updates:
                return True
            
            # 构建SQL
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(self._serialize_value(value))
            
            values.append(id)
            
            sql = f"""
                UPDATE {table}
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor = conn.execute(sql, values)
            
            success = cursor.rowcount > 0
            self._record_operation("update", success)
            
            if success:
                logger.debug(f"Data updated in {table}: {id}")
            
            return success
            
        except Exception as e:
            self._record_operation("update", False)
            raise ProviderError(f"Failed to update data in {table}: {e}", provider_type="sqlite")
    
    async def delete(self, table: str, id: str) -> bool:
        """从指定表删除数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        try:
            conn = self._get_connection()
            
            cursor = conn.execute(
                f"DELETE FROM {table} WHERE id = ?",
                (id,)
            )
            
            success = cursor.rowcount > 0
            self._record_operation("delete", success)
            
            if success:
                logger.debug(f"Data deleted from {table}: {id}")
            
            return success
            
        except Exception as e:
            self._record_operation("delete", False)
            raise ProviderError(f"Failed to delete data from {table}: {e}", provider_type="sqlite")
    
    async def exists(self, table: str, id: str) -> bool:
        """检查指定表中数据是否存在
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否存在
        """
        try:
            conn = self._get_connection()
            
            cursor = conn.execute(
                f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1",
                (id,)
            )
            
            exists = cursor.fetchone() is not None
            self._record_operation("exists", True)
            
            return exists
            
        except Exception as e:
            self._record_operation("exists", False)
            raise ProviderError(f"Failed to check existence in {table}: {e}", provider_type="sqlite")
    
    async def list(self, table: str, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出指定表中的数据
        
        Args:
            table: 表名
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            数据列表
        """
        try:
            conn = self._get_connection()
            
            # 构建WHERE子句
            where_clauses = []
            values = []
            
            for key, value in filters.items():
                if isinstance(value, dict) and "op" in value:
                    # 支持操作符
                    op = value["op"]
                    val = value["value"]
                    
                    if op == "like":
                        where_clauses.append(f"{key} LIKE ?")
                        values.append(f"%{val}%")
                    elif op == ">":
                        where_clauses.append(f"{key} > ?")
                        values.append(val)
                    elif op == "<":
                        where_clauses.append(f"{key} < ?")
                        values.append(val)
                    elif op == ">=":
                        where_clauses.append(f"{key} >= ?")
                        values.append(val)
                    elif op == "<=":
                        where_clauses.append(f"{key} <= ?")
                        values.append(val)
                    else:
                        where_clauses.append(f"{key} = ?")
                        values.append(val)
                else:
                    where_clauses.append(f"{key} = ?")
                    values.append(value)
            
            # 构建SQL
            sql = f"SELECT * FROM {table}"
            if where_clauses:
                sql += f" WHERE {' AND '.join(where_clauses)}"
            
            if limit:
                sql += f" LIMIT {limit}"
            
            cursor = conn.execute(sql, values)
            rows = cursor.fetchall()
            
            # 转换数据
            results = []
            for row in rows:
                data = dict(row)
                data = self._deserialize_data(data)
                results.append(data)
            
            self._record_operation("list", True)
            logger.debug(f"Listed {len(results)} records from {table}")
            return results
            
        except Exception as e:
            self._record_operation("list", False)
            raise ProviderError(f"Failed to list data from {table}: {e}", provider_type="sqlite")
    
    async def query(self, table: str, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """在指定表中执行查询
        
        Args:
            table: 表名
            query: 查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        try:
            conn = self._get_connection()
            
            # 替换表名占位符
            query = query.replace("{table}", table)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # 转换数据
            results = []
            for row in rows:
                data = dict(row)
                data = self._deserialize_data(data)
                results.append(data)
            
            self._record_operation("query", True)
            logger.debug(f"Query executed on {table}, returned {len(results)} results")
            return results
            
        except Exception as e:
            self._record_operation("query", False)
            raise ProviderError(f"Failed to query {table}: {e}", provider_type="sqlite")
    
    async def count(self, table: str, filters: Dict[str, Any]) -> int:
        """统计指定表中符合条件的数据数量
        
        Args:
            table: 表名
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
        """
        try:
            conn = self._get_connection()
            
            # 构建WHERE子句
            where_clauses = []
            values = []
            
            for key, value in filters.items():
                where_clauses.append(f"{key} = ?")
                values.append(value)
            
            # 构建SQL
            sql = f"SELECT COUNT(*) as count FROM {table}"
            if where_clauses:
                sql += f" WHERE {' AND '.join(where_clauses)}"
            
            cursor = conn.execute(sql, values)
            row = cursor.fetchone()
            count = row["count"] if row else 0
            
            self._record_operation("count", True)
            logger.debug(f"Counted {count} records in {table}")
            return count
            
        except Exception as e:
            self._record_operation("count", False)
            raise ProviderError(f"Failed to count data in {table}: {e}", provider_type="sqlite")
    
    async def batch_save(self, table: str, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存数据到指定表
        
        Args:
            table: 表名
            data_list: 数据列表
            
        Returns:
            数据ID列表
        """
        try:
            conn = self._get_connection()
            
            result_ids = []
            
            for data in data_list:
                # 确保有ID字段
                if "id" not in data:
                    data["id"] = str(time.time()) + str(id(data))
                
                # 构建SQL
                columns = list(data.keys())
                placeholders = ["?"] * len(columns)
                values = [self._serialize_value(data[col]) for col in columns]
                
                sql = f"""
                    INSERT OR REPLACE INTO {table} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                conn.execute(sql, values)
                result_ids.append(data["id"])
            
            self._record_operation("batch_save", True)
            logger.debug(f"Batch saved {len(result_ids)} records to {table}")
            return result_ids
            
        except Exception as e:
            self._record_operation("batch_save", False)
            raise ProviderError(f"Failed to batch save data to {table}: {e}", provider_type="sqlite")
    
    async def batch_delete(self, table: str, ids: List[str]) -> int:
        """从指定表批量删除数据
        
        Args:
            table: 表名
            ids: 数据ID列表
            
        Returns:
            删除的数量
        """
        try:
            conn = self._get_connection()
            
            if not ids:
                return 0
            
            # 构建SQL
            placeholders = ["?"] * len(ids)
            sql = f"DELETE FROM {table} WHERE id IN ({', '.join(placeholders)})"
            
            cursor = conn.execute(sql, ids)
            count = cursor.rowcount
            
            self._record_operation("batch_delete", True)
            logger.debug(f"Batch deleted {count} records from {table}")
            return count
            
        except Exception as e:
            self._record_operation("batch_delete", False)
            raise ProviderError(f"Failed to batch delete data from {table}: {e}", provider_type="sqlite")
    
    async def create_table(self, table: str, schema: Dict[str, Any]) -> None:
        """创建表
        
        Args:
            table: 表名
            schema: 表结构定义
        """
        try:
            conn = self._get_connection()
            
            # 构建列定义
            columns = []
            for col_name, col_def in schema.get("columns", {}).items():
                col_type = col_def.get("type", "TEXT")
                constraints = col_def.get("constraints", "")
                columns.append(f"{col_name} {col_type} {constraints}".strip())
            
            # 构建SQL
            sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
            
            conn.execute(sql)
            
            # 创建索引
            for index in schema.get("indexes", []):
                index_name = index.get("name", f"idx_{table}_{index['column']}")
                column = index["column"]
                unique = "UNIQUE" if index.get("unique", False) else ""
                
                index_sql = f"CREATE {unique} INDEX IF NOT EXISTS {index_name} ON {table} ({column})"
                conn.execute(index_sql)
            
            logger.debug(f"Table created: {table}")
            
        except Exception as e:
            raise ProviderError(f"Failed to create table {table}: {e}", provider_type="sqlite")
    
    async def drop_table(self, table: str) -> None:
        """删除表
        
        Args:
            table: 表名
        """
        try:
            conn = self._get_connection()
            conn.execute(f"DROP TABLE IF EXISTS {table}")
            logger.debug(f"Table dropped: {table}")
            
        except Exception as e:
            raise ProviderError(f"Failed to drop table {table}: {e}", provider_type="sqlite")
    
    async def table_exists(self, table: str) -> bool:
        """检查表是否存在
        
        Args:
            table: 表名
            
        Returns:
            是否存在
        """
        try:
            conn = self._get_connection()
            
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            
            exists = cursor.fetchone() is not None
            return exists
            
        except Exception as e:
            raise ProviderError(f"Failed to check table existence {table}: {e}", provider_type="sqlite")
    
    async def list_tables(self) -> List[str]:
        """列出所有表
        
        Returns:
            表名列表
        """
        try:
            conn = self._get_connection()
            
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            
            tables = [row["name"] for row in cursor.fetchall()]
            return tables
            
        except Exception as e:
            raise ProviderError(f"Failed to list tables: {e}", provider_type="sqlite")
    
    def _serialize_value(self, value: Any) -> Any:
        """序列化值
        
        Args:
            value: 要序列化的值
            
        Returns:
            序列化后的值
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value
    
    def _deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """反序列化数据
        
        Args:
            data: 要反序列化的数据
            
        Returns:
            反序列化后的数据
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    # 尝试解析JSON
                    if value.startswith('{') and value.endswith('}'):
                        result[key] = json.loads(value)
                    elif value.startswith('[') and value.endswith(']'):
                        result[key] = json.loads(value)
                    else:
                        result[key] = value
                except (json.JSONDecodeError, ValueError):
                    result[key] = value
            else:
                result[key] = value
        
        return result