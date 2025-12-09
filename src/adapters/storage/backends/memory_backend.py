"""内存存储后端

基于MemoryProvider的存储后端实现。
"""

from typing import Dict, Any, Optional, List, AsyncIterator
from src.services.logger.injection import get_logger

from .core.base_backend import BaseStorageBackend
from .providers.memory_provider import MemoryProvider


logger = get_logger(__name__)


class MemoryStorageBackend(BaseStorageBackend):
    """内存存储后端
    
    使用MemoryProvider提供实际的存储操作。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化内存存储后端
        
        Args:
            **config: 配置参数
        """
        # 初始化基础后端
        super().__init__(**config)
        
        # 创建内存提供者
        self._provider = MemoryProvider(**config)
        
        # 默认表名
        self._default_table = config.get("default_table", "default")
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        await self._provider.connect()
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        await self._provider.disconnect()
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现
        
        Returns:
            健康检查结果
        """
        try:
            # 检查内存提供者状态
            tables = await self._provider.list_tables()
            return {
                "status": "healthy",
                "storage_type": "memory",
                "tables_count": len(tables),
                "default_table": self._default_table
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def save(self, data: Dict[str, Any], table: Optional[str] = None) -> str:
        """保存数据并返回ID
        
        Args:
            data: 要保存的数据字典
            table: 表名，可选
            
        Returns:
            保存的数据ID
        """
        table_name = table or self._default_table
        return await self._provider.save(table_name, data)
    
    async def load(self, id: str, table: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据ID加载数据
        
        Args:
            id: 数据ID
            table: 表名，可选
            
        Returns:
            数据字典，如果不存在则返回None
        """
        table_name = table or self._default_table
        return await self._provider.load(table_name, id)
    
    async def update(self, id: str, updates: Dict[str, Any], table: Optional[str] = None) -> bool:
        """更新数据
        
        Args:
            id: 数据ID
            updates: 要更新的字段
            table: 表名，可选
            
        Returns:
            是否更新成功
        """
        table_name = table or self._default_table
        return await self._provider.update(table_name, id, updates)
    
    async def delete(self, id: str, table: Optional[str] = None) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            table: 表名，可选
            
        Returns:
            是否删除成功
        """
        table_name = table or self._default_table
        return await self._provider.delete(table_name, id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None, table: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出数据
        
        Args:
            filters: 过滤条件
            limit: 限制返回数量
            table: 表名，可选
            
        Returns:
            数据列表
        """
        table_name = table or self._default_table
        return await self._provider.list(table_name, filters, limit)
    
    async def query(self, query: str, params: Dict[str, Any], table: Optional[str] = None) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            query: 查询语句
            params: 查询参数
            table: 表名，可选
            
        Returns:
            查询结果列表
        """
        table_name = table or self._default_table
        return await self._provider.query(table_name, query, params)
    
    async def exists(self, id: str, table: Optional[str] = None) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            table: 表名，可选
            
        Returns:
            数据是否存在
        """
        table_name = table or self._default_table
        return await self._provider.exists(table_name, id)
    
    async def count(self, filters: Dict[str, Any], table: Optional[str] = None) -> int:
        """计数
        
        Args:
            filters: 过滤条件
            table: 表名，可选
            
        Returns:
            符合条件的数据数量
        """
        table_name = table or self._default_table
        return await self._provider.count(table_name, filters)
    
    async def transaction(self, operations: List[Dict[str, Any]], table: Optional[str] = None) -> bool:
        """执行事务
        
        Args:
            operations: 操作列表，每个操作包含type和data字段
            table: 表名，可选
            
        Returns:
            事务是否执行成功
        """
        # 内存提供者不直接支持事务，这里简化实现
        table_name = table or self._default_table
        
        try:
            for operation in operations:
                op_type = operation.get("type")
                op_data = operation.get("data")
                
                if op_type == "save":
                    await self._provider.save(table_name, op_data)
                elif op_type == "update":
                    await self._provider.update(table_name, op_data["id"], op_data["updates"])
                elif op_type == "delete":
                    await self._provider.delete(table_name, op_data["id"])
                else:
                    raise ValueError(f"Unsupported operation type: {op_type}")
            
            return True
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False
    
    async def batch_save(self, data_list: List[Dict[str, Any]], table: Optional[str] = None) -> List[str]:
        """批量保存
        
        Args:
            data_list: 数据列表
            table: 表名，可选
            
        Returns:
            保存的数据ID列表
        """
        table_name = table or self._default_table
        return await self._provider.batch_save(table_name, data_list)
    
    async def batch_delete(self, ids: List[str], table: Optional[str] = None) -> int:
        """批量删除
        
        Args:
            ids: 数据ID列表
            table: 表名，可选
            
        Returns:
            删除的数据数量
        """
        table_name = table or self._default_table
        return await self._provider.batch_delete(table_name, ids)
    
    def stream_list(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100,
        table: Optional[str] = None
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列出数据
        
        Args:
            filters: 过滤条件
            batch_size: 批次大小
            table: 表名，可选
            
        Yields:
            数据批次列表
        """
        table_name = table or self._default_table
        
        async def _stream_generator():
            offset = 0
            while True:
                # 获取一批数据
                batch = await self._provider.list(table_name, filters, batch_size)
                
                if not batch:
                    break
                
                yield batch
                offset += batch_size
                
                # 如果返回的数据少于批次大小，说明已经到达末尾
                if len(batch) < batch_size:
                    break
        
        return _stream_generator()
    
    # 表管理操作
    async def create_table(self, table: str, schema: Dict[str, Any]) -> None:
        """创建表
        
        Args:
            table: 表名
            schema: 表结构定义
        """
        await self._provider.create_table(table, schema)
    
    async def drop_table(self, table: str) -> None:
        """删除表
        
        Args:
            table: 表名
        """
        await self._provider.drop_table(table)
    
    async def table_exists(self, table: str) -> bool:
        """检查表是否存在
        
        Args:
            table: 表名
            
        Returns:
            是否存在
        """
        return await self._provider.table_exists(table)
    
    async def list_tables(self) -> List[str]:
        """列出所有表
        
        Returns:
            表名列表
        """
        return await self._provider.list_tables()
    
    # 内存特有操作
    async def clear_all(self) -> None:
        """清空所有数据"""
        tables = await self._provider.list_tables()
        for table in tables:
            await self._provider.drop_table(table)
        logger.info("All memory data cleared")
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况
        
        Returns:
            内存使用信息
        """
        # 这里可以添加更详细的内存统计
        tables = await self._provider.list_tables()
        total_records = 0
        
        for table in tables:
            count = await self._provider.count(table, {})
            total_records += count
        
        return {
            "tables_count": len(tables),
            "total_records": total_records,
            "tables": tables
        }