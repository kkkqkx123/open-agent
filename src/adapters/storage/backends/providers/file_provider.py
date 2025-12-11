"""文件存储提供者

提供文件系统的底层存储操作实现。
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from .base_provider import BaseStorageProvider
from ..core.exceptions import ProviderError


logger = get_logger(__name__)


class FileProvider(BaseStorageProvider):
    """文件存储提供者
    
    专注于文件系统的底层存储操作。
    """
    
    def __init__(self, base_path: str = "./storage", **config: Any) -> None:
        """初始化文件提供者
        
        Args:
            base_path: 基础存储路径
            **config: 其他配置参数
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 文件扩展名
        self.file_extension = config.get("file_extension", ".json")
        
        # 文件锁定机制
        self._file_locks = {}
        
        super().__init__(base_path=base_path, **config)
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # 文件系统不需要显式连接
        logger.debug(f"File provider ready for directory: {self.base_path}")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        # 清理文件锁
        self._file_locks.clear()
        logger.debug("File provider disconnected")
    
    def _get_table_path(self, table: str) -> Path:
        """获取表的存储路径
        
        Args:
            table: 表名
            
        Returns:
            表的存储路径
        """
        return self.base_path / table
    
    def _get_file_path(self, table: str, id: str) -> Path:
        """获取文件路径
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            文件路径
        """
        table_path = self._get_table_path(table)
        table_path.mkdir(parents=True, exist_ok=True)
        return table_path / f"{id}{self.file_extension}"
    
    def _get_file_lock(self, file_path: Path) -> asyncio.Lock:
        """获取文件锁
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件锁
        """
        key = str(file_path)
        if key not in self._file_locks:
            self._file_locks[key] = asyncio.Lock()
        return self._file_locks[key]
    
    async def save(self, table: str, data: Dict[str, Any]) -> str:
        """保存数据到指定表
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            数据ID
        """
        try:
            # 确保有ID字段
            if "id" not in data:
                data["id"] = str(time.time()) + str(id(data))
            
            file_path = self._get_file_path(table, data["id"])
            lock = self._get_file_lock(file_path)
            
            async with lock:
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._record_operation("save", True)
            logger.debug(f"Data saved to {table}: {data['id']}")
            return data["id"]
            
        except Exception as e:
            self._record_operation("save", False)
            raise ProviderError(f"Failed to save data to {table}: {e}", provider_type="file")
    
    async def load(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """从指定表加载数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            数据字典，不存在返回None
        """
        try:
            file_path = self._get_file_path(table, id)
            
            if not file_path.exists():
                return None
            
            lock = self._get_file_lock(file_path)
            
            async with lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            self._record_operation("load", True)
            logger.debug(f"Data loaded from {table}: {id}")
            return data
            
        except Exception as e:
            self._record_operation("load", False)
            raise ProviderError(f"Failed to load data from {table}: {e}", provider_type="file")
    
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
            
            # 先加载现有数据
            existing_data = await self.load(table, id)
            if existing_data is None:
                return False
            
            # 合并更新
            existing_data.update(updates)
            existing_data["updated_at"] = time.time()
            
            # 保存更新后的数据
            await self.save(table, existing_data)
            
            self._record_operation("update", True)
            logger.debug(f"Data updated in {table}: {id}")
            return True
            
        except Exception as e:
            self._record_operation("update", False)
            raise ProviderError(f"Failed to update data in {table}: {e}", provider_type="file")
    
    async def delete(self, table: str, id: str) -> bool:
        """从指定表删除数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        try:
            file_path = self._get_file_path(table, id)
            
            if not file_path.exists():
                return False
            
            lock = self._get_file_lock(file_path)
            
            async with lock:
                file_path.unlink()
            
            self._record_operation("delete", True)
            logger.debug(f"Data deleted from {table}: {id}")
            return True
            
        except Exception as e:
            self._record_operation("delete", False)
            raise ProviderError(f"Failed to delete data from {table}: {e}", provider_type="file")
    
    async def exists(self, table: str, id: str) -> bool:
        """检查指定表中数据是否存在
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否存在
        """
        try:
            file_path = self._get_file_path(table, id)
            exists = file_path.exists()
            
            self._record_operation("exists", True)
            return exists
            
        except Exception as e:
            self._record_operation("exists", False)
            raise ProviderError(f"Failed to check existence in {table}: {e}", provider_type="file")
    
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
            table_path = self._get_table_path(table)
            
            if not table_path.exists():
                return []
            
            results = []
            count = 0
            
            # 遍历文件
            for file_path in table_path.glob(f"*{self.file_extension}"):
                if limit and count >= limit:
                    break
                
                try:
                    # 获取文件锁
                    lock = self._get_file_lock(file_path)
                    
                    async with lock:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    
                    # 应用过滤器
                    if self._matches_filters(data, filters):
                        results.append(data)
                        count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to load file {file_path}: {e}")
                    continue
            
            self._record_operation("list", True)
            logger.debug(f"Listed {len(results)} records from {table}")
            return results
            
        except Exception as e:
            self._record_operation("list", False)
            raise ProviderError(f"Failed to list data from {table}: {e}", provider_type="file")
    
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
            raise ProviderError(f"Failed to query {table}: {e}", provider_type="file")
    
    async def count(self, table: str, filters: Dict[str, Any]) -> int:
        """统计指定表中符合条件的数据数量
        
        Args:
            table: 表名
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
        """
        try:
            results = await self.list(table, filters)
            count = len(results)
            
            self._record_operation("count", True)
            logger.debug(f"Counted {count} records in {table}")
            return count
            
        except Exception as e:
            self._record_operation("count", False)
            raise ProviderError(f"Failed to count data in {table}: {e}", provider_type="file")
    
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
            raise ProviderError(f"Failed to batch save data to {table}: {e}", provider_type="file")
    
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
            raise ProviderError(f"Failed to batch delete data from {table}: {e}", provider_type="file")
    
    async def create_table(self, table: str, schema: Dict[str, Any]) -> None:
        """创建表
        
        Args:
            table: 表名
            schema: 表结构定义
        """
        try:
            table_path = self._get_table_path(table)
            table_path.mkdir(parents=True, exist_ok=True)
            
            # 创建元数据文件
            metadata_file = table_path / "_metadata.json"
            metadata = {
                "table": table,
                "schema": schema,
                "created_at": time.time()
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Table created: {table}")
            
        except Exception as e:
            raise ProviderError(f"Failed to create table {table}: {e}", provider_type="file")
    
    async def drop_table(self, table: str) -> None:
        """删除表
        
        Args:
            table: 表名
        """
        try:
            table_path = self._get_table_path(table)
            
            if table_path.exists():
                import shutil
                shutil.rmtree(table_path)
            
            logger.debug(f"Table dropped: {table}")
            
        except Exception as e:
            raise ProviderError(f"Failed to drop table {table}: {e}", provider_type="file")
    
    async def table_exists(self, table: str) -> bool:
        """检查表是否存在
        
        Args:
            table: 表名
            
        Returns:
            是否存在
        """
        try:
            table_path = self._get_table_path(table)
            exists = table_path.exists()
            return exists
            
        except Exception as e:
            raise ProviderError(f"Failed to check table existence {table}: {e}", provider_type="file")
    
    async def list_tables(self) -> List[str]:
        """列出所有表
        
        Returns:
            表名列表
        """
        try:
            tables = []
            
            for item in self.base_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    tables.append(item.name)
            
            return tables
            
        except Exception as e:
            raise ProviderError(f"Failed to list tables: {e}", provider_type="file")
    
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