"""
检查点存储工厂

提供检查点存储的创建和管理功能。
"""

from typing import Dict, Any

from src.interfaces.dependency_injection import get_logger
from src.core.checkpoint.interfaces import ICheckpointRepository
from .config import CheckpointStorageConfig
from .memory import MemoryCheckpointBackend


logger = get_logger(__name__)


class CheckpointStorageFactory:
    """检查点存储工厂"""
    
    @staticmethod
    def create_repository(config: CheckpointStorageConfig) -> ICheckpointRepository:
        """创建检查点仓储
        
        Args:
            config: 存储配置
            
        Returns:
            检查点仓储实例
        """
        try:
            if config.storage_type == "memory":
                logger.info(f"Creating memory checkpoint repository")
                return MemoryCheckpointBackend(**config.to_dict())
            elif config.storage_type == "sqlite":
                # TODO: 实现SQLite存储后端
                raise NotImplementedError(f"SQLite storage not yet implemented")
            elif config.storage_type == "file":
                # TODO: 实现文件存储后端
                raise NotImplementedError(f"File storage not yet implemented")
            else:
                raise ValueError(f"Unsupported storage type: {config.storage_type}")
                
        except Exception as e:
            logger.error(f"Failed to create repository: {e}")
            raise
    
    @staticmethod
    def create_from_config_dict(config_dict: Dict[str, Any]) -> ICheckpointRepository:
        """从配置字典创建仓储
        
        Args:
            config_dict: 配置字典
            
        Returns:
            检查点仓储实例
        """
        config = CheckpointStorageConfig.from_dict(config_dict)
        return CheckpointStorageFactory.create_repository(config)