"""后端接口定义

定义存储后端和存储提供者的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IStorageBackend(ABC):
    """存储后端接口
    
    定义后端基础能力，专注于基础设施组件管理。
    """
    
    # === 基础连接管理 ===
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到存储后端"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        pass
    
    # === 健康检查 ===
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        pass
    
    # === 配置管理 ===
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            配置字典
        """
        pass
    
    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config: 新配置
        """
        pass
    
    # === 统计信息 ===
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    # === 错误处理 ===
    
    @abstractmethod
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计
        
        Returns:
            错误统计信息
        """
        pass
    
    @abstractmethod
    def clear_error_stats(self) -> None:
        """清除错误统计"""
        pass


class IStorageProvider(ABC):
    """存储提供者接口
    
    定义存储技术抽象，专注于底层存储操作。
    """
    
    # === 基础CRUD操作 ===
    
    @abstractmethod
    async def save(self, table: str, data: Dict[str, Any]) -> str:
        """保存数据到指定表
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            数据ID
        """
        pass
    
    @abstractmethod
    async def load(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """从指定表加载数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            数据字典，不存在返回None
        """
        pass
    
    @abstractmethod
    async def update(self, table: str, id: str, updates: Dict[str, Any]) -> bool:
        """更新指定表中的数据
        
        Args:
            table: 表名
            id: 数据ID
            updates: 更新内容
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete(self, table: str, id: str) -> bool:
        """从指定表删除数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, table: str, id: str) -> bool:
        """检查指定表中数据是否存在
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            是否存在
        """
        pass
    
    # === 查询操作 ===
    
    @abstractmethod
    async def list(self, table: str, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出指定表中的数据
        
        Args:
            table: 表名
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            数据列表
        """
        pass
    
    @abstractmethod
    async def query(self, table: str, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """在指定表中执行查询
        
        Args:
            table: 表名
            query: 查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        pass
    
    @abstractmethod
    async def count(self, table: str, filters: Dict[str, Any]) -> int:
        """统计指定表中符合条件的数据数量
        
        Args:
            table: 表名
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
        """
        pass
    
    # === 高级操作 ===
    
    @abstractmethod
    async def batch_save(self, table: str, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存数据到指定表
        
        Args:
            table: 表名
            data_list: 数据列表
            
        Returns:
            数据ID列表
        """
        pass
    
    @abstractmethod
    async def batch_delete(self, table: str, ids: List[str]) -> int:
        """从指定表批量删除数据
        
        Args:
            table: 表名
            ids: 数据ID列表
            
        Returns:
            删除的数量
        """
        pass
    
    # === 表管理 ===
    
    @abstractmethod
    async def create_table(self, table: str, schema: Dict[str, Any]) -> None:
        """创建表
        
        Args:
            table: 表名
            schema: 表结构定义
        """
        pass
    
    @abstractmethod
    async def drop_table(self, table: str) -> None:
        """删除表
        
        Args:
            table: 表名
        """
        pass
    
    @abstractmethod
    async def table_exists(self, table: str) -> bool:
        """检查表是否存在
        
        Args:
            table: 表名
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def list_tables(self) -> List[str]:
        """列出所有表
        
        Returns:
            表名列表
        """
        pass
    
    # === 事务支持 ===
    
    @abstractmethod
    async def begin_transaction(self) -> str:
        """开始事务
        
        Returns:
            事务ID
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self, transaction_id: str) -> None:
        """提交事务
        
        Args:
            transaction_id: 事务ID
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self, transaction_id: str) -> None:
        """回滚事务
        
        Args:
            transaction_id: 事务ID
        """
        pass
    
    # === 连接管理 ===
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到存储"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        pass
    
    # === 健康检查 ===
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        pass