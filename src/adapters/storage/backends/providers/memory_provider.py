"""内存存储提供者

提供内存中的底层存储操作实现。
"""

import time
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from .base_provider import BaseStorageProvider
from ..core.exceptions import ProviderError


logger = get_logger(__name__)


class MemoryProvider(BaseStorageProvider):
    """内存存储提供者
    
    专注于内存中的底层存储操作。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化内存提供者
        
        Args:
            **config: 其他配置参数
        """
        # 内存存储结构: {table: {id: data}}
        self._storage: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # 表结构信息
        self._table_schemas: Dict[str, Dict[str, Any]] = {}
        
        # 最大内存使用量 (字节)
        self._max_memory_usage = config.get("max_memory_usage", 100 * 1024 * 1024)  # 100MB
        
        # 当前内存使用量
        self._current_memory_usage = 0
        
        super().__init__(**config)
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # 内存存储不需要显式连接
        logger.debug("Memory provider ready")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        # 清空内存数据
        self._storage.clear()
        self._table_schemas.clear()
        self._current_memory_usage = 0
        logger.debug("Memory provider disconnected")
    
    def _estimate_data_size(self, data: Dict[str, Any]) -> int:
        """估算数据大小
        
        Args:
            data: 数据字典
            
        Returns:
            数据大小（字节）
        """
        try:
            import pickle
            return len(pickle.dumps(data))
        except Exception:
            # 粗略估算
            return len(str(data)) * 2  # 假设每个字符2字节
    
    def _check_memory_limit(self, additional_size: int = 0) -> None:
        """检查内存限制
        
        Args:
            additional_size: 额外大小
            
        Raises:
            ProviderError: 超出内存限制时抛出
        """
        if self._current_memory_usage + additional_size > self._max_memory_usage:
            raise ProviderError(
                f"Memory limit exceeded: {self._current_memory_usage + additional_size} > {self._max_memory_usage}",
                provider_type="memory"
            )
    
    async def save(self, table: str, data: Dict[str, Any]) -> str:
        """保存数据到指定表
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            数据ID
        """
        try:
            # 确保表存在
            if table not in self._storage:
                self._storage[table] = {}
            
            # 确保有ID字段
            if "id" not in data:
                data["id"] = str(time.time()) + str(id(data))
            
            record_id = data["id"]
            
            # 估算新数据大小
            new_size = self._estimate_data_size(data)
            
            # 检查内存限制
            old_size = 0
            if record_id in self._storage[table]:
                old_size = self._estimate_data_size(self._storage[table][record_id])
            
            self._check_memory_limit(new_size - old_size)
            
            # 更新内存使用量
            self._current_memory_usage += (new_size - old_size)
            
            # 保存数据
            self._storage[table][record_id] = data.copy()
            
            self._record_operation("save", True)
            logger.debug(f"Data saved to {table}: {record_id}")
            return record_id
            
        except Exception as e:
            self._record_operation("save", False)
            raise ProviderError(f"Failed to save data to {table}: {e}", provider_type="memory")
    
    async def load(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """从指定表加载数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            数据字典，不存在返回None
        """
        try:
            if table not in self._storage or id not in self._storage[table]:
                return None
            
            data = self._storage[table][id].copy()
            
            self._record_operation("load", True)
            logger.debug(f"Data loaded from {table}: {id}")
            return data
            
        except Exception as e:
            self._record_operation("load", False)
            raise ProviderError(f"Failed to load data from {table}: {e}", provider_type="memory")
    
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
            if not updates:
                return True
            
            if table not in self._storage or id not in self._storage[table]:
                return False
            
            # 获取现有数据
            existing_data = self._storage[table][id]
            
            # 估算更新前后的数据大小差异
            old_size = self._estimate_data_size(existing_data)
            
            # 创建更新后的数据副本
            updated_data = existing_data.copy()
            updated_data.update(updates)
            updated_data["updated_at"] = time.time()
            
            # 估算新数据大小
            new_size = self._estimate_data_size(updated_data)
            
            # 检查内存限制
            self._check_memory_limit(new_size - old_size)
            
            # 更新内存使用量
            self._current_memory_usage += (new_size - old_size)
            
            # 保存更新后的数据
            self._storage[table][id] = updated_data
            
            self._record_operation("update", True)
            logger.debug(f"Data updated in {table}: {id}")
            return True
            
        except Exception as e:
            self._record_operation("update", False)
            raise ProviderError(f"Failed to update data in {table}: {e}", provider_type="memory")
    
    async def delete(self, table: str, id: str) -> bool:
        """从指定表删除数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        try:
            if table not in self._storage or id not in self._storage[table]:
                return False
            
            # 估算数据大小
            data_size = self._estimate_data_size(self._storage[table][id])
            
            # 删除数据
            del self._storage[table][id]
            
            # 更新内存使用量
            self._current_memory_usage -= data_size
            
            # 如果表为空，删除表
            if not self._storage[table]:
                del self._storage[table]
                if table in self._table_schemas:
                    del self._table_schemas[table]
            
            self._record_operation("delete", True)
            logger.debug(f"Data deleted from {table}: {id}")
            return True
            
        except Exception as e:
            self._record_operation("delete", False)
            raise ProviderError(f"Failed to delete data from {table}: {e}", provider_type="memory")
    
    async def exists(self, table: str, id: str) -> bool:
        """检查指定表中数据是否存在
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否存在
        """
        try:
            exists = table in self._storage and id in self._storage[table]
            
            self._record_operation("exists", True)
            return exists
            
        except Exception as e:
            self._record_operation("exists", False)
            raise ProviderError(f"Failed to check existence in {table}: {e}", provider_type="memory")
    
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
            if table not in self._storage:
                return []
            
            results = []
            count = 0
            
            for id, data in self._storage[table].items():
                if limit and count >= limit:
                    break
                
                # 应用过滤器
                if self._matches_filters(data, filters):
                    results.append(data.copy())
                    count += 1
            
            self._record_operation("list", True)
            logger.debug(f"Listed {len(results)} records from {table}")
            return results
            
        except Exception as e:
            self._record_operation("list", False)
            raise ProviderError(f"Failed to list data from {table}: {e}", provider_type="memory")
    
    async def query(self, table: str, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """在指定表中执行查询
        
        Args:
            table: 表名
            query: 查询语句（这里模拟简单的键值查询）
            params: 查询参数
            
        Returns:
            查询结果
        """
        try:
            # 模拟查询：将查询字符串转换为过滤器
            filters = {}
            
            # 简单的键值查询
            if query and "=" in query:
                parts = query.split("=")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().strip("'\"")
                    filters[key] = value
            
            # 添加参数中的过滤条件
            filters.update(params)
            
            return await self.list(table, filters)
            
        except Exception as e:
            self._record_operation("query", False)
            raise ProviderError(f"Failed to query {table}: {e}", provider_type="memory")
    
    async def count(self, table: str, filters: Dict[str, Any]) -> int:
        """统计指定表中符合条件的数据数量
        
        Args:
            table: 表名
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
        """
        try:
            if table not in self._storage:
                return 0
            
            count = 0
            
            for id, data in self._storage[table].items():
                if self._matches_filters(data, filters):
                    count += 1
            
            self._record_operation("count", True)
            logger.debug(f"Counted {count} records in {table}")
            return count
            
        except Exception as e:
            self._record_operation("count", False)
            raise ProviderError(f"Failed to count data in {table}: {e}", provider_type="memory")
    
    async def batch_save(self, table: str, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存数据到指定表
        
        Args:
            table: 表名
            data_list: 数据列表
            
        Returns:
            数据ID列表
        """
        try:
            result_ids = []
            
            for data in data_list:
                # 确保有ID字段
                if "id" not in data:
                    data["id"] = str(time.time()) + str(id(data))
                
                result_id = await self.save(table, data)
                result_ids.append(result_id)
            
            self._record_operation("batch_save", True)
            logger.debug(f"Batch saved {len(result_ids)} records to {table}")
            return result_ids
            
        except Exception as e:
            self._record_operation("batch_save", False)
            raise ProviderError(f"Failed to batch save data to {table}: {e}", provider_type="memory")
    
    async def batch_delete(self, table: str, ids: List[str]) -> int:
        """从指定表批量删除数据
        
        Args:
            table: 表名
            ids: 数据ID列表
            
        Returns:
            删除的数量
        """
        try:
            count = 0
            
            for id in ids:
                if await self.delete(table, id):
                    count += 1
            
            self._record_operation("batch_delete", True)
            logger.debug(f"Batch deleted {count} records from {table}")
            return count
            
        except Exception as e:
            self._record_operation("batch_delete", False)
            raise ProviderError(f"Failed to batch delete data from {table}: {e}", provider_type="memory")
    
    async def create_table(self, table: str, schema: Dict[str, Any]) -> None:
        """创建表
        
        Args:
            table: 表名
            schema: 表结构定义
        """
        try:
            # 确保表存在
            if table not in self._storage:
                self._storage[table] = {}
            
            # 保存表结构信息
            self._table_schemas[table] = schema.copy()
            
            logger.debug(f"Table created: {table}")
            
        except Exception as e:
            raise ProviderError(f"Failed to create table {table}: {e}", provider_type="memory")
    
    async def drop_table(self, table: str) -> None:
        """删除表
        
        Args:
            table: 表名
        """
        try:
            if table in self._storage:
                # 估算表的大小
                table_size = sum(
                    self._estimate_data_size(data)
                    for data in self._storage[table].values()
                )
                
                # 删除表
                del self._storage[table]
                
                # 更新内存使用量
                self._current_memory_usage -= table_size
                
                # 删除表结构信息
                if table in self._table_schemas:
                    del self._table_schemas[table]
            
            logger.debug(f"Table dropped: {table}")
            
        except Exception as e:
            raise ProviderError(f"Failed to drop table {table}: {e}", provider_type="memory")
    
    async def table_exists(self, table: str) -> bool:
        """检查表是否存在
        
        Args:
            table: 表名
            
        Returns:
            是否存在
        """
        try:
            exists = table in self._storage
            return exists
            
        except Exception as e:
            raise ProviderError(f"Failed to check table existence {table}: {e}", provider_type="memory")
    
    async def list_tables(self) -> List[str]:
        """列出所有表
        
        Returns:
            表名列表
        """
        try:
            tables = list(self._storage.keys())
            return tables
            
        except Exception as e:
            raise ProviderError(f"Failed to list tables: {e}", provider_type="memory")
    
    def _matches_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配过滤器
        """
        if not filters:
            return True
        
        for key, expected_value in filters.items():
            if key not in data:
                return False
            
            actual_value = data[key]
            
            # 处理操作符
            if isinstance(expected_value, dict) and "op" in expected_value:
                op = expected_value["op"]
                val = expected_value["value"]
                
                if op == "like":
                    if val not in str(actual_value):
                        return False
                elif op == ">":
                    if not (actual_value > val):
                        return False
                elif op == "<":
                    if not (actual_value < val):
                        return False
                elif op == ">=":
                    if not (actual_value >= val):
                        return False
                elif op == "<=":
                    if not (actual_value <= val):
                        return False
                else:  # 默认等于
                    if actual_value != val:
                        return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True