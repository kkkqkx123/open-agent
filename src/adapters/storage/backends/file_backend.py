"""文件存储后端

基于FileProvider的存储后端实现。
"""

from typing import Dict, Any, Optional, List, AsyncIterator
from src.services.logger.injection import get_logger

from .core.base_backend import BaseStorageBackend
from .providers.file_provider import FileProvider


logger = get_logger(__name__)


class FileStorageBackend(BaseStorageBackend):
    """文件存储后端
    
    使用FileProvider提供实际的存储操作。
    """
    
    def __init__(self, base_path: str = "./storage", **config: Any) -> None:
        """初始化文件存储后端
        
        Args:
            base_path: 基础存储路径
            **config: 其他配置参数
        """
        # 初始化基础后端
        super().__init__(base_path=base_path, **config)
        
        # 创建文件提供者
        self._provider = FileProvider(base_path=base_path, **config)
        
        # 默认表名
        self._default_table = config.get("default_table", "default")
    
    def _get_required_config_keys(self) -> list:
        """获取必需的配置键
        
        Returns:
            必需配置键列表
        """
        return ["base_path"]
    
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
            # 检查文件系统访问权限
            tables = await self._provider.list_tables()
            return {
                "status": "healthy",
                "storage_type": "file",
                "base_path": self._config.get("base_path"),
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
        # 文件提供者不直接支持事务，这里简化实现
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
    
    # 文件特有操作
    async def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息
        
        Returns:
            存储信息
        """
        import os
        
        base_path = self._config.get("base_path")
        tables = await self._provider.list_tables()
        
        # 计算总大小
        total_size = 0
        total_files = 0
        
        for table in tables:
            table_path = os.path.join(base_path, table)
            if os.path.exists(table_path):
                for root, dirs, files in os.walk(table_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            total_size += os.path.getsize(file_path)
                            total_files += 1
        
        return {
            "base_path": base_path,
            "tables_count": len(tables),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "tables": tables
        }
    
    async def export_table(self, table: str, output_path: str) -> None:
        """导出表数据
        
        Args:
            table: 表名
            output_path: 输出路径
        """
        import json
        import os
        
        # 获取所有数据
        all_data = await self._provider.list(table, {}, None)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "table": table,
                "exported_at": str(os.path.getmtime(output_path)),
                "count": len(all_data),
                "data": all_data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Table '{table}' exported to '{output_path}'")
    
    async def import_table(self, table: str, input_path: str) -> int:
        """导入表数据
        
        Args:
            table: 表名
            input_path: 输入路径
            
        Returns:
            导入的记录数
        """
        import json
        
        # 读取文件
        with open(input_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # 创建表
        if "schema" in import_data:
            await self._provider.create_table(table, import_data["schema"])
        
        # 导入数据
        data_list = import_data.get("data", [])
        if data_list:
            await self._provider.batch_save(table, data_list)
        
        logger.info(f"Imported {len(data_list)} records to table '{table}'")
        return len(data_list)