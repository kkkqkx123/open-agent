"""Checkpoint工厂实现

提供checkpoint存储和管理器的创建功能。
"""

import logging
from pathlib import Path
from typing import Optional

from ...domain.checkpoint.config import CheckpointConfig
from ...domain.checkpoint.interfaces import ICheckpointStore, ICheckpointSerializer
from ...domain.checkpoint.serializer import DefaultCheckpointSerializer, JSONCheckpointSerializer
from ...application.checkpoint.manager import CheckpointManager
from .sqlite_store import SQLiteCheckpointStore
from .memory_store import MemoryCheckpointStore

logger = logging.getLogger(__name__)


class CheckpointStoreFactory:
    """Checkpoint存储工厂
    
    根据配置创建不同类型的checkpoint存储。
    """
    
    @staticmethod
    def create_store(config: CheckpointConfig, 
                    serializer: Optional[ICheckpointSerializer] = None) -> ICheckpointStore:
        """创建checkpoint存储
        
        Args:
            config: checkpoint配置
            serializer: 可选的序列化器
            
        Returns:
            ICheckpointStore: checkpoint存储实例
            
        Raises:
            ValueError: 不支持的存储类型
        """
        if config.storage_type == "sqlite":
            if not config.db_path:
                raise ValueError("SQLite存储需要指定数据库路径")
            
            db_path = Path(config.db_path)
            return SQLiteCheckpointStore(db_path, serializer)
        
        elif config.storage_type == "memory":
            return MemoryCheckpointStore(serializer)
        
        else:
            raise ValueError(f"不支持的存储类型: {config.storage_type}")


class CheckpointSerializerFactory:
    """Checkpoint序列化器工厂
    
    根据配置创建不同类型的序列化器。
    """
    
    @staticmethod
    def create_serializer(config: CheckpointConfig) -> ICheckpointSerializer:
        """创建checkpoint序列化器
        
        Args:
            config: checkpoint配置
            
        Returns:
            ICheckpointSerializer: 序列化器实例
        """
        if config.compression:
            # 如果启用压缩，使用JSON序列化器
            return JSONCheckpointSerializer()
        else:
            # 默认使用基本序列化器
            return DefaultCheckpointSerializer()


class CheckpointManagerFactory:
    """Checkpoint管理器工厂
    
    创建完整的checkpoint管理器。
    """
    
    @staticmethod
    def create_manager(config: CheckpointConfig) -> CheckpointManager:
        """创建checkpoint管理器
        
        Args:
            config: checkpoint配置
            
        Returns:
            CheckpointManager: checkpoint管理器实例
        """
        # 创建序列化器
        serializer = CheckpointSerializerFactory.create_serializer(config)
        
        # 创建存储
        store = CheckpointStoreFactory.create_store(config, serializer)
        
        # 创建管理器
        return CheckpointManager(store, config)


class CheckpointFactory:
    """Checkpoint统一工厂
    
    提供创建checkpoint相关组件的统一接口。
    """
    
    @staticmethod
    def create_from_config(config_dict: dict) -> CheckpointManager:
        """从配置字典创建checkpoint管理器
        
        Args:
            config_dict: 配置字典
            
        Returns:
            CheckpointManager: checkpoint管理器实例
        """
        # 创建配置对象
        config = CheckpointConfig.from_dict(config_dict)
        
        # 验证配置
        errors = config.validate()
        if errors:
            raise ValueError(f"配置验证失败: {'; '.join(errors)}")
        
        # 创建管理器
        return CheckpointManagerFactory.create_manager(config)
    
    @staticmethod
    def create_sqlite_manager(db_path: str, **kwargs) -> CheckpointManager:
        """创建SQLite checkpoint管理器
        
        Args:
            db_path: 数据库文件路径
            **kwargs: 其他配置参数
            
        Returns:
            CheckpointManager: checkpoint管理器实例
        """
        config_dict = {
            "storage_type": "sqlite",
            "db_path": db_path,
            **kwargs
        }
        return CheckpointFactory.create_from_config(config_dict)
    
    @staticmethod
    def create_memory_manager(**kwargs) -> CheckpointManager:
        """创建内存checkpoint管理器
        
        Args:
            **kwargs: 配置参数
            
        Returns:
            CheckpointManager: checkpoint管理器实例
        """
        config_dict = {
            "storage_type": "memory",
            **kwargs
        }
        return CheckpointFactory.create_from_config(config_dict)
    
    @staticmethod
    def create_test_manager() -> CheckpointManager:
        """创建测试用的checkpoint管理器
        
        Returns:
            CheckpointManager: 测试用的checkpoint管理器实例
        """
        return CheckpointFactory.create_memory_manager(
            auto_save=False,
            max_checkpoints=10
        )
    
    @staticmethod
    def create_production_manager(db_path: str, **kwargs) -> CheckpointManager:
        """创建生产环境的checkpoint管理器
        
        Args:
            db_path: 数据库文件路径
            **kwargs: 其他配置参数
            
        Returns:
            CheckpointManager: 生产环境的checkpoint管理器实例
        """
        config_dict = {
            "storage_type": "sqlite",
            "db_path": db_path,
            "auto_save": True,
            "save_interval": 3,
            "max_checkpoints": 1000,
            "retention_days": 90,
            "compression": True,
            **kwargs
        }
        return CheckpointFactory.create_from_config(config_dict)