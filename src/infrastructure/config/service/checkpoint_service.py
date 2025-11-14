"""Checkpoint配置服务"""

import os
from typing import Optional
from ..config_system import IConfigSystem
from ..models.checkpoint_config import CheckpointConfig


class CheckpointConfigService:
    """Checkpoint配置服务
    
    提供checkpoint配置的获取和管理功能。
    """
    
    def __init__(self, config_system: Optional[IConfigSystem] = None):
        """初始化配置服务
        
        Args:
            config_system: 配置系统实例，如果为None则使用默认配置
        """
        self._config_system = config_system
        self._default_config = CheckpointConfig(
            enabled=True,
            storage_type="sqlite",
            auto_save=True,
            save_interval=5,
            max_checkpoints=100,
            retention_days=30,
            db_path=None,
            compression=False
        )
    
    def get_config(self) -> CheckpointConfig:
        """获取checkpoint配置
        
        Returns:
            CheckpointConfig: checkpoint配置对象
        """
        if self._config_system:
            try:
                global_config = self._config_system.load_global_config()
                return global_config.checkpoint
            except Exception:
                # 如果加载配置失败，返回默认配置
                return self._default_config
        else:
            return self._default_config
    
    def get_db_path(self) -> str:
        """获取数据库路径
        
        Returns:
            str: 数据库路径
        """
        config = self.get_config()
        return config.get_db_path()
    
    def is_enabled(self) -> bool:
        """检查是否启用checkpoint功能
        
        Returns:
            bool: 是否启用
        """
        return self.get_config().enabled
    
    def get_storage_type(self) -> str:
        """获取存储类型
        
        Returns:
            str: 存储类型
        """
        return self.get_config().storage_type
    
    def is_test_environment(self) -> bool:
        """检查是否为测试环境
        
        Returns:
            bool: 是否为测试环境
        """
        return "test" in os.environ.get("PYTEST_CURRENT_TEST", "")