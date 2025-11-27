"""存储迁移接口定义

定义存储数据迁移的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from .adapter import IStateStorageAdapter


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


class IAsyncStorageMigration(ABC):
     """异步存储迁移接口
     
     定义存储数据的异步迁移功能。
     """
     
     @abstractmethod
     async def migrate_from(self, source_adapter: IStateStorageAdapter, 
                           target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
         """异步从源存储迁移到目标存储
         
         Args:
             source_adapter: 源存储适配器
             target_adapter: 目标存储适配器
             
         Returns:
             迁移结果统计
         """
         pass
     
     @abstractmethod
     async def validate_migration(self, source_adapter: IStateStorageAdapter,
                                 target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
         """异步验证迁移结果
         
         Args:
             source_adapter: 源存储适配器
             target_adapter: 目标存储适配器
             
         Returns:
             验证结果
         """
         pass