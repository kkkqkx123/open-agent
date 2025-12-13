"""SQLite Repository基类"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional

from .base import BaseRepository
from .utils import SQLiteUtils


logger = get_logger(__name__)


class SQLiteBaseRepository(BaseRepository):
    """SQLite Repository基类"""
    
    def __init__(self, config: Dict[str, Any], table_name: str, table_sql: str, indexes_sql: Optional[List[str]] = None):
        """初始化SQLite基类
        
        Args:
            config: 配置参数
            table_name: 表名
            table_sql: 创建表的SQL
            indexes_sql: 创建索引的SQL列表
        """
        super().__init__(config)
        self.table_name = table_name
        self.db_path = config.get("db_path", f"data/{table_name}.db")
        self._init_database(table_sql, indexes_sql or [])
    
    def _init_database(self, table_sql: str, indexes_sql: List[str]) -> None:
        """初始化数据库"""
        try:
            SQLiteUtils.init_database(self.db_path, table_sql, indexes_sql)
            self._log_operation("数据库初始化", True, self.db_path)
        except Exception as e:
            self._handle_exception("数据库初始化", e)
    
    def _insert_or_replace(self, data: Dict[str, Any]) -> None:
        """插入或替换数据"""
        try:
            SQLiteUtils.insert_or_replace(self.db_path, self.table_name, data)
        except Exception as e:
            self._handle_exception("插入或替换数据", e)
    
    def _delete_by_id(self, id_field: str, id_value: str) -> bool:
        """根据ID删除记录"""
        try:
            return SQLiteUtils.delete_by_id(self.db_path, self.table_name, id_field, id_value)
        except Exception as e:
            self._handle_exception("删除记录", e)
            return False
    
    def _find_by_id(self, id_field: str, id_value: str) -> Optional[tuple]:
        """根据ID查找记录"""
        try:
            return SQLiteUtils.find_by_id(self.db_path, self.table_name, id_field, id_value)
        except Exception as e:
            self._handle_exception("查找记录", e)
            return None
    
    def _count_records(self, condition: str = "", params: Optional[tuple] = None) -> int:
        """统计记录数"""
        try:
            return SQLiteUtils.count_records(self.db_path, self.table_name, condition, params or ())
        except Exception as e:
            self._handle_exception("统计记录", e)
            return 0