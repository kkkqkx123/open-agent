"""存储配置管理服务

提供存储适配器的配置管理，不包含业务逻辑。
"""

import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from src.core.storage import StorageError, StorageConfigurationError


logger = logging.getLogger(__name__)


class StorageType(Enum):
    """存储类型枚举"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"


class StorageConfigManager:
    """存储配置管理服务
    
    专注于存储适配器的配置管理，不包含业务逻辑。
    """
    
    def __init__(self):
        """初始化存储配置管理服务"""
        self._adapter_configs: Dict[str, Dict[str, Any]] = {}
        self._default_adapter: Optional[str] = None
        
        logger.info("StorageConfigManager initialized")
    
    def register_adapter_config(
        self, 
        name: str, 
        storage_type: Union[str, StorageType], 
        config: Dict[str, Any],
        set_as_default: bool = False
    ) -> bool:
        """注册存储适配器配置
        
        Args:
            name: 适配器名称
            storage_type: 存储类型
            config: 配置参数
            set_as_default: 是否设为默认适配器
            
        Returns:
            是否注册成功
        """
        try:
            # 验证配置
            self._validate_adapter_config(name, storage_type, config)
            
            # 注册配置
            self._adapter_configs[name] = {
                "storage_type": storage_type.value if isinstance(storage_type, StorageType) else storage_type,
                "config": config.copy()
            }
            
            # 设置默认适配器
            if set_as_default or self._default_adapter is None:
                self._default_adapter = name
            
            logger.info(f"Registered storage adapter config: {name} ({storage_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register adapter config {name}: {e}")
            return False
    
    def unregister_adapter_config(self, name: str) -> bool:
        """注销存储适配器配置
        
        Args:
            name: 适配器名称
            
        Returns:
            是否注销成功
        """
        try:
            if name not in self._adapter_configs:
                logger.warning(f"Adapter config {name} not found")
                return False
            
            # 移除配置
            del self._adapter_configs[name]
            
            # 如果是默认适配器，重新选择默认适配器
            if self._default_adapter == name:
                self._default_adapter = next(iter(self._adapter_configs.keys()), None)
            
            logger.info(f"Unregistered storage adapter config: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister adapter config {name}: {e}")
            return False
    
    def get_adapter_config(self, name: str) -> Optional[Dict[str, Any]]:
        """获取存储适配器配置
        
        Args:
            name: 适配器名称
            
        Returns:
            适配器配置或None
        """
        return self._adapter_configs.get(name)
    
    def get_default_adapter_config(self) -> Optional[Dict[str, Any]]:
        """获取默认存储适配器配置
        
        Returns:
            默认适配器配置或None
        """
        if self._default_adapter is None:
            return None
        return self._adapter_configs.get(self._default_adapter)
    
    def list_adapter_configs(self) -> List[Dict[str, Any]]:
        """列出所有已注册的适配器配置
        
        Returns:
            适配器配置信息列表
        """
        configs = []
        
        for name, config_info in self._adapter_configs.items():
            configs.append({
                "name": name,
                "storage_type": config_info["storage_type"],
                "is_default": name == self._default_adapter,
                "config": config_info["config"]
            })
        
        return configs
    
    def set_default_adapter(self, name: str) -> bool:
        """设置默认适配器
        
        Args:
            name: 适配器名称
            
        Returns:
            是否设置成功
        """
        if name not in self._adapter_configs:
            logger.warning(f"Adapter config {name} not found")
            return False
        
        self._default_adapter = name
        logger.info(f"Set default adapter: {name}")
        return True
    
    def get_default_adapter_name(self) -> Optional[str]:
        """获取默认适配器名称
        
        Returns:
            默认适配器名称或None
        """
        return self._default_adapter
    
    def update_adapter_config(
        self, 
        name: str, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """更新适配器配置
        
        Args:
            name: 适配器名称
            config_updates: 配置更新
            
        Returns:
            是否更新成功
        """
        try:
            if name not in self._adapter_configs:
                logger.warning(f"Adapter config {name} not found")
                return False
            
            # 更新配置
            self._adapter_configs[name]["config"].update(config_updates)
            
            logger.info(f"Updated adapter config: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update adapter config {name}: {e}")
            return False
    
    def validate_adapter_config(self, name: str) -> List[str]:
        """验证适配器配置
        
        Args:
            name: 适配器名称
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        try:
            config_info = self._adapter_configs.get(name)
            if config_info is None:
                errors.append(f"Adapter config {name} not found")
                return errors
            
            storage_type = config_info["storage_type"]
            config = config_info["config"]
            
            # 验证存储类型
            try:
                StorageType(storage_type)
            except ValueError:
                errors.append(f"Invalid storage type: {storage_type}")
            
            # 根据存储类型验证配置
            if storage_type == StorageType.MEMORY.value:
                errors.extend(self._validate_memory_config(config))
            elif storage_type == StorageType.SQLITE.value:
                errors.extend(self._validate_sqlite_config(config))
            elif storage_type == StorageType.FILE.value:
                errors.extend(self._validate_file_config(config))
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    def export_configs(self) -> Dict[str, Any]:
        """导出配置
        
        Returns:
            导出的配置字典
        """
        return {
            "default_adapter": self._default_adapter,
            "adapter_configs": {
                name: config_info.copy() 
                for name, config_info in self._adapter_configs.items()
            }
        }
    
    def import_configs(self, configs_data: Dict[str, Any]) -> bool:
        """导入配置
        
        Args:
            configs_data: 配置数据
            
        Returns:
            是否导入成功
        """
        try:
            # 清空现有配置
            self._adapter_configs.clear()
            self._default_adapter = None
            
            # 导入默认适配器
            if "default_adapter" in configs_data:
                self._default_adapter = configs_data["default_adapter"]
            
            # 导入适配器配置
            if "adapter_configs" in configs_data:
                for name, config_info in configs_data["adapter_configs"].items():
                    self._adapter_configs[name] = config_info.copy()
            
            logger.info("Configs imported successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configs: {e}")
            return False
    
    def clear_configs(self) -> None:
        """清空所有配置"""
        self._adapter_configs.clear()
        self._default_adapter = None
        logger.info("Cleared all adapter configs")
    
    # 私有方法
    def _validate_adapter_config(
        self, 
        name: str, 
        storage_type: Union[str, StorageType], 
        config: Dict[str, Any]
    ) -> None:
        """验证适配器配置
        
        Args:
            name: 适配器名称
            storage_type: 存储类型
            config: 配置参数
            
        Raises:
            ConfigurationError: 配置验证失败
        """
        if not name:
            raise StorageConfigurationError("Adapter name is required")
        
        if isinstance(storage_type, str):
            try:
                storage_type = StorageType(storage_type)
            except ValueError:
                raise StorageConfigurationError(f"Invalid storage type: {storage_type}")
        
        # 根据存储类型验证特定配置
        if storage_type == StorageType.MEMORY:
            self._validate_memory_config(config)
        elif storage_type == StorageType.SQLITE:
            self._validate_sqlite_config(config)
        elif storage_type == StorageType.FILE:
            self._validate_file_config(config)
    
    def _validate_memory_config(self, config: Dict[str, Any]) -> List[str]:
        """验证内存存储配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证数值范围
        if "max_size" in config and config["max_size"] is not None:
            if not isinstance(config["max_size"], int) or config["max_size"] <= 0:
                errors.append("max_size must be a positive integer")
        
        if "max_memory_mb" in config and config["max_memory_mb"] is not None:
            if not isinstance(config["max_memory_mb"], int) or config["max_memory_mb"] <= 0:
                errors.append("max_memory_mb must be a positive integer")
        
        if "default_ttl_seconds" in config:
            if not isinstance(config["default_ttl_seconds"], int) or config["default_ttl_seconds"] <= 0:
                errors.append("default_ttl_seconds must be a positive integer")
        
        return errors
    
    def _validate_sqlite_config(self, config: Dict[str, Any]) -> List[str]:
        """验证SQLite存储配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证必需字段
        if "db_path" not in config or not config["db_path"]:
            errors.append("db_path is required for SQLite storage")
        
        # 验证数值范围
        if "timeout" in config:
            if not isinstance(config["timeout"], (int, float)) or config["timeout"] <= 0:
                errors.append("timeout must be a positive number")
        
        if "connection_pool_size" in config:
            if not isinstance(config["connection_pool_size"], int) or config["connection_pool_size"] <= 0:
                errors.append("connection_pool_size must be a positive integer")
        
        return errors
    
    def _validate_file_config(self, config: Dict[str, Any]) -> List[str]:
        """验证文件存储配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证必需字段
        if "base_path" not in config or not config["base_path"]:
            errors.append("base_path is required for file storage")
        
        # 验证数值范围
        if "default_ttl_seconds" in config:
            if not isinstance(config["default_ttl_seconds"], int) or config["default_ttl_seconds"] <= 0:
                errors.append("default_ttl_seconds must be a positive integer")
        
        return errors