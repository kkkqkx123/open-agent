"""存储适配器接口定义

定义状态存储的统一接口，支持多种存储后端。
此文件保持向后兼容性，实际接口定义已移至 src/core/state/interfaces.py
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# 从 Core 层导入接口以保持向后兼容性
from src.core.state.interfaces import IStateStorageAdapter

# 重新导出以便向后兼容
__all__ = ['IStateStorageAdapter', 'IStorageAdapterFactory', 'IStorageMigration']


class IStorageAdapterFactory(ABC):
    """存储适配器工厂接口
    
    定义存储适配器的创建接口。
    """
    
    @abstractmethod
    def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建存储适配器
        
        Args:
            storage_type: 存储类型（memory, sqlite, file等）
            config: 配置参数
            
        Returns:
            存储适配器实例
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的存储类型
        
        Returns:
            支持的存储类型列表
        """
        pass
    
    @abstractmethod
    def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """验证配置参数
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        pass


class IStorageMigration(ABC):
    """存储迁移接口
    
    定义存储数据的迁移功能。
    """
    
    @abstractmethod
    def migrate_from(self, source_adapter: IStateStorageAdapter, 
                    target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
        """从源存储迁移到目标存储
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            迁移结果统计
        """
        pass
    
    @abstractmethod
    def validate_migration(self, source_adapter: IStateStorageAdapter,
                          target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
        """验证迁移结果
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            验证结果
        """
        pass