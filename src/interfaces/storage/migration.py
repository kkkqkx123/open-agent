"""
存储迁移接口定义

定义存储系统的迁移功能接口，包括数据迁移、版本管理和模式升级。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .base import IStorage


class IStorageMigration(ABC):
    """存储迁移接口
    
    定义存储数据的迁移功能，支持不同存储类型之间的数据迁移。
    """
    
    @abstractmethod
    async def migrate_from(
        self, 
        source_storage: 'IStorage', 
        target_storage: 'IStorage',
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从源存储迁移到目标存储
        
        Args:
            source_storage: 源存储实例
            target_storage: 目标存储实例
            config: 迁移配置
            
        Returns:
            迁移结果统计
        """
        pass
    
    @abstractmethod
    async def validate_migration(
        self, 
        source_storage: 'IStorage',
        target_storage: 'IStorage'
    ) -> Dict[str, Any]:
        """验证迁移结果
        
        Args:
            source_storage: 源存储实例
            target_storage: 目标存储实例
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    async def rollback_migration(
        self, 
        migration_id: str,
        target_storage: 'IStorage'
    ) -> bool:
        """回滚迁移
        
        Args:
            migration_id: 迁移ID
            target_storage: 目标存储实例
            
        Returns:
            是否回滚成功
        """
        pass


class ISchemaMigration(ABC):
    """模式迁移接口
    
    定义存储模式的版本管理和升级功能。
    """
    
    @abstractmethod
    async def create_migration(
        self, 
        name: str, 
        description: str,
        up_script: str,
        down_script: Optional[str] = None
    ) -> str:
        """创建迁移
        
        Args:
            name: 迁移名称
            description: 迁移描述
            up_script: 升级脚本
            down_script: 回滚脚本
            
        Returns:
            迁移ID
        """
        pass
    
    @abstractmethod
    async def apply_migration(self, migration_id: str) -> bool:
        """应用迁移
        
        Args:
            migration_id: 迁移ID
            
        Returns:
            是否应用成功
        """
        pass
    
    @abstractmethod
    async def rollback_migration(self, migration_id: str) -> bool:
        """回滚迁移
        
        Args:
            migration_id: 迁移ID
            
        Returns:
            是否回滚成功
        """
        pass
    
    @abstractmethod
    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史
        
        Returns:
            迁移历史列表
        """
        pass
    
    @abstractmethod
    async def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """获取待执行的迁移
        
        Returns:
            待执行迁移列表
        """
        pass
    
    @abstractmethod
    async def get_current_version(self) -> str:
        """获取当前版本
        
        Returns:
            当前版本号
        """
        pass


class IDataTransformer(ABC):
    """数据转换器接口
    
    定义数据在迁移过程中的转换逻辑。
    """
    
    @abstractmethod
    async def transform_data(
        self, 
        source_data: Dict[str, Any],
        target_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换数据格式
        
        Args:
            source_data: 源数据
            target_schema: 目标模式
            
        Returns:
            转换后的数据
        """
        pass
    
    @abstractmethod
    async def validate_transformed_data(
        self, 
        data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> bool:
        """验证转换后的数据
        
        Args:
            data: 转换后的数据
            schema: 数据模式
            
        Returns:
            是否验证通过
        """
        pass
    
    @abstractmethod
    async def get_transformation_rules(self) -> Dict[str, Any]:
        """获取转换规则
        
        Returns:
            转换规则配置
        """
        pass


class IMigrationPlanner(ABC):
    """迁移计划器接口
    
    定义复杂迁移的规划和执行策略。
    """
    
    @abstractmethod
    async def plan_migration(
        self, 
        source_config: Dict[str, Any],
        target_config: Dict[str, Any],
        data_size_estimate: Optional[int] = None
    ) -> Dict[str, Any]:
        """规划迁移策略
        
        Args:
            source_config: 源配置
            target_config: 目标配置
            data_size_estimate: 数据大小估算
            
        Returns:
            迁移计划
        """
        pass
    
    @abstractmethod
    async def estimate_migration_time(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """估算迁移时间
        
        Args:
            plan: 迁移计划
            
        Returns:
            时间估算结果
        """
        pass
    
    @abstractmethod
    async def validate_migration_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """验证迁移计划
        
        Args:
            plan: 迁移计划
            
        Returns:
            验证结果
        """
        pass