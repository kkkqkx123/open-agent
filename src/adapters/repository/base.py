"""Repository基类

提供所有Repository实现的通用基类和功能。
"""

import logging
from abc import ABC
from typing import Dict, Any, List, Optional
from datetime import datetime

from .utils import JsonUtils, TimeUtils, FileUtils, SQLiteUtils, IdUtils
from src.core.common.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Repository基类，包含通用功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化基类
        
        Args:
            config: 配置参数
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _log_operation(self, operation: str, success: bool, details: str = "") -> None:
        """记录操作日志
        
        Args:
            operation: 操作名称
            success: 是否成功
            details: 详细信息
        """
        status = "成功" if success else "失败"
        message = f"{operation}{status}"
        if details:
            message += f": {details}"
        
        if success:
            self.logger.debug(message)
        else:
            self.logger.error(message)
    
    def _handle_exception(self, operation: str, exception: Exception) -> None:
        """处理异常
        
        Args:
            operation: 操作名称
            exception: 异常对象
        """
        error_msg = f"{operation}失败: {exception}"
        self.logger.error(error_msg)
        raise RepositoryError(error_msg) from exception


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


class MemoryBaseRepository(BaseRepository):
    """内存Repository基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存基类
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._indexes: Dict[str, Dict[str, List[str]]] = {}
        self.logger.info(f"{self.__class__.__name__}初始化完成")
    
    def _add_to_index(self, index_name: str, key: str, item_id: str) -> None:
        """添加到索引"""
        if index_name not in self._indexes:
            self._indexes[index_name] = {}
        if key not in self._indexes[index_name]:
            self._indexes[index_name][key] = []
        if item_id not in self._indexes[index_name][key]:
            self._indexes[index_name][key].append(item_id)
    
    def _remove_from_index(self, index_name: str, key: str, item_id: str) -> None:
        """从索引中移除"""
        if (index_name in self._indexes and 
            key in self._indexes[index_name] and 
            item_id in self._indexes[index_name][key]):
            self._indexes[index_name][key].remove(item_id)
            if not self._indexes[index_name][key]:
                del self._indexes[index_name][key]
            if not self._indexes[index_name]:
                del self._indexes[index_name]
    
    def _get_from_index(self, index_name: str, key: str) -> List[str]:
        """从索引获取"""
        return self._indexes.get(index_name, {}).get(key, [])
    
    def _save_item(self, item_id: str, data: Dict[str, Any]) -> None:
        """保存项目"""
        self._storage[item_id] = data.copy()
    
    def _load_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """加载项目"""
        item = self._storage.get(item_id)
        return item.copy() if item else None
    
    def _delete_item(self, item_id: str) -> bool:
        """删除项目"""
        if item_id in self._storage:
            del self._storage[item_id]
            return True
        return False


class FileBaseRepository(BaseRepository):
    """文件Repository基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件基类
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self.base_path = config.get("base_path", "data/files")
        FileUtils.ensure_directory(self.base_path)
        self.logger.info(f"{self.__class__.__name__}初始化完成: {self.base_path}")
    
    def _get_item_file(self, category: str, item_id: str) -> Any:
        """获取项目文件路径"""
        from pathlib import Path
        return Path(self.base_path) / category / f"{item_id}.json"
    
    def _save_item(self, category: str, item_id: str, data: Dict[str, Any]) -> None:
        """保存项目到文件"""
        file_path = self._get_item_file(category, item_id)
        FileUtils.save_json(file_path, data)
    
    def _load_item(self, category: str, item_id: str) -> Optional[Dict[str, Any]]:
        """从文件加载项目"""
        file_path = self._get_item_file(category, item_id)
        return FileUtils.load_json(file_path)
    
    def _delete_item(self, category: str, item_id: str) -> bool:
        """删除项目文件"""
        file_path = self._get_item_file(category, item_id)
        return FileUtils.delete_file(file_path)
    
    def _list_items(self, category: str) -> List[Dict[str, Any]]:
        """列出分类下的所有项目"""
        from pathlib import Path
        category_dir = Path(self.base_path) / category
        return FileUtils.load_all_json(category_dir)