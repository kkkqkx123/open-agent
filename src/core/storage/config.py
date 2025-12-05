"""存储配置管理服务

提供统一的存储配置管理，支持配置验证、默认值管理和环境变量注入。
"""

import os
from src.services.logger.injection import get_logger
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

from src.core.storage import StorageError, StorageConfigurationError


logger = get_logger(__name__)


class StorageType(Enum):
    """存储类型枚举"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"


@dataclass
class StorageConfig:
    """存储配置数据类"""
    name: str
    storage_type: StorageType
    enabled: bool = True
    is_default: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class MemoryStorageConfig:
    """内存存储配置"""
    max_size: Optional[int] = None
    max_memory_mb: Optional[int] = None
    enable_ttl: bool = False
    default_ttl_seconds: int = 3600
    cleanup_interval_seconds: int = 300
    enable_compression: bool = False
    compression_threshold: int = 1024
    enable_metrics: bool = True
    enable_persistence: bool = False
    persistence_path: Optional[str] = None
    persistence_interval_seconds: int = 600


@dataclass
class SQLiteStorageConfig:
    """SQLite存储配置"""
    db_path: str = "storage.db"
    timeout: float = 30.0
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    connection_pool_size: int = 5
    enable_auto_vacuum: bool = False
    cache_size: int = 2000
    temp_store: str = "memory"
    synchronous_mode: str = "NORMAL"
    journal_mode: str = "WAL"
    enable_backup: bool = False
    backup_interval_hours: int = 24
    backup_path: str = "backups"
    max_backup_files: int = 7


@dataclass
class FileStorageConfig:
    """文件存储配置"""
    base_path: str = "file_storage"
    enable_compression: bool = False
    compression_threshold: int = 1024
    enable_ttl: bool = False
    default_ttl_seconds: int = 3600
    cleanup_interval_seconds: int = 300
    enable_backup: bool = False
    backup_interval_hours: int = 24
    backup_path: str = "file_storage_backups"
    max_backup_files: int = 7
    directory_structure: str = "flat"
    file_extension: str = "json"
    enable_metadata: bool = True
    max_directory_size: Optional[int] = None
    max_files_per_directory: int = 1000


class StorageConfigManager:
    """存储配置管理服务
    
    提供统一的存储配置管理，支持配置验证、默认值管理和环境变量注入。
    """
    
    def __init__(self):
        """初始化存储配置管理服务"""
        self._configs: Dict[str, StorageConfig] = {}
        self._default_config: Optional[str] = None
        
        # 注册默认配置模板
        self._register_default_templates()
        
        logger.info("StorageConfigManager initialized")
    
    def _register_default_templates(self) -> None:
        """注册默认配置模板"""
        # 内存存储默认配置
        self.register_config(
            StorageConfig(
                name="memory_default",
                storage_type=StorageType.MEMORY,
                description="Default memory storage configuration",
                config=MemoryStorageConfig().__dict__
            )
        )
        
        # SQLite存储默认配置
        self.register_config(
            StorageConfig(
                name="sqlite_default",
                storage_type=StorageType.SQLITE,
                description="Default SQLite storage configuration",
                config=SQLiteStorageConfig().__dict__
            )
        )
        
        # 文件存储默认配置
        self.register_config(
            StorageConfig(
                name="file_default",
                storage_type=StorageType.FILE,
                description="Default file storage configuration",
                config=FileStorageConfig().__dict__
            )
        )
    
    def register_config(self, config: StorageConfig) -> bool:
        """注册存储配置
        
        Args:
            config: 存储配置
            
        Returns:
            是否注册成功
        """
        try:
            # 验证配置
            self._validate_config(config)
            
            # 处理环境变量注入
            processed_config = self._process_env_variables(config)
            
            # 注册配置
            self._configs[config.name] = processed_config
            
            # 设置默认配置
            if processed_config.is_default or self._default_config is None:
                self._default_config = config.name
            
            logger.info(f"Registered storage config: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register config {config.name}: {e}")
            return False
    
    def unregister_config(self, name: str) -> bool:
        """注销存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否注销成功
        """
        try:
            if name not in self._configs:
                logger.warning(f"Config {name} not found")
                return False
            
            # 移除配置
            del self._configs[name]
            
            # 如果是默认配置，重新选择默认配置
            if self._default_config == name:
                self._default_config = next(iter(self._configs.keys()), None)
            
            logger.info(f"Unregistered storage config: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister config {name}: {e}")
            return False
    
    def get_config(self, name: str) -> Optional[StorageConfig]:
        """获取存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            存储配置或None
        """
        return self._configs.get(name)
    
    def get_default_config(self) -> Optional[StorageConfig]:
        """获取默认存储配置
        
        Returns:
            默认存储配置或None
        """
        if self._default_config is None:
            return None
        return self._configs.get(self._default_config)
    
    def list_configs(self, storage_type: Optional[StorageType] = None) -> List[StorageConfig]:
        """列出存储配置
        
        Args:
            storage_type: 存储类型过滤
            
        Returns:
            存储配置列表
        """
        configs = list(self._configs.values())
        
        if storage_type is not None:
            configs = [config for config in configs if config.storage_type == storage_type]
        
        return configs
    
    def set_default_config(self, name: str) -> bool:
        """设置默认存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否设置成功
        """
        if name not in self._configs:
            logger.warning(f"Config {name} not found")
            return False
        
        self._default_config = name
        logger.info(f"Set default config: {name}")
        return True
    
    def create_config_from_template(
        self, 
        template_name: str, 
        new_name: str, 
        overrides: Optional[Dict[str, Any]] = None
    ) -> bool:
        """从模板创建配置
        
        Args:
            template_name: 模板名称
            new_name: 新配置名称
            overrides: 覆盖配置
            
        Returns:
            是否创建成功
        """
        try:
            # 获取模板配置
            template_config = self.get_config(template_name)
            if template_config is None:
                logger.error(f"Template config {template_name} not found")
                return False
            
            # 创建新配置
            new_config = StorageConfig(
                name=new_name,
                storage_type=template_config.storage_type,
                enabled=template_config.enabled,
                is_default=False,
                config=template_config.config.copy(),
                description=f"Created from template: {template_name}",
                tags=template_config.tags.copy()
            )
            
            # 应用覆盖配置
            if overrides:
                new_config.config.update(overrides)
            
            # 注册新配置
            return self.register_config(new_config)
            
        except Exception as e:
            logger.error(f"Failed to create config from template {template_name}: {e}")
            return False
    
    def _validate_config(self, config: StorageConfig) -> None:
        """验证存储配置
        
        Args:
            config: 存储配置
            
        Raises:
            StorageConfigurationError: 配置验证失败
        """
        # 验证基本字段
        if not config.name:
            raise StorageConfigurationError("Config name is required")
        
        if not isinstance(config.storage_type, StorageType):
            raise StorageConfigurationError(f"Invalid storage type: {config.storage_type}")
        
        # 根据存储类型验证特定配置
        if config.storage_type == StorageType.MEMORY:
            self._validate_memory_config(config.config)
        elif config.storage_type == StorageType.SQLITE:
            self._validate_sqlite_config(config.config)
        elif config.storage_type == StorageType.FILE:
            self._validate_file_config(config.config)
    
    def _validate_memory_config(self, config: Dict[str, Any]) -> None:
        """验证内存存储配置
        
        Args:
            config: 配置字典
            
        Raises:
            StorageConfigurationError: 配置验证失败
        """
        # 验证数值范围
        if "max_size" in config and config["max_size"] is not None:
            if not isinstance(config["max_size"], int) or config["max_size"] <= 0:
                raise StorageConfigurationError("max_size must be a positive integer")
        
        if "max_memory_mb" in config and config["max_memory_mb"] is not None:
            if not isinstance(config["max_memory_mb"], int) or config["max_memory_mb"] <= 0:
                raise StorageConfigurationError("max_memory_mb must be a positive integer")
        
        if "default_ttl_seconds" in config:
            if not isinstance(config["default_ttl_seconds"], int) or config["default_ttl_seconds"] <= 0:
                raise StorageConfigurationError("default_ttl_seconds must be a positive integer")
        
        if "cleanup_interval_seconds" in config:
            if not isinstance(config["cleanup_interval_seconds"], int) or config["cleanup_interval_seconds"] <= 0:
                raise StorageConfigurationError("cleanup_interval_seconds must be a positive integer")
        
        if "compression_threshold" in config:
            if not isinstance(config["compression_threshold"], int) or config["compression_threshold"] <= 0:
                raise StorageConfigurationError("compression_threshold must be a positive integer")
    
    def _validate_sqlite_config(self, config: Dict[str, Any]) -> None:
        """验证SQLite存储配置
        
        Args:
            config: 配置字典
            
        Raises:
            StorageConfigurationError: 配置验证失败
        """
        # 验证必需字段
        if "db_path" not in config or not config["db_path"]:
            raise StorageConfigurationError("db_path is required for SQLite storage")
        
        # 验证数值范围
        if "timeout" in config:
            if not isinstance(config["timeout"], (int, float)) or config["timeout"] <= 0:
                raise StorageConfigurationError("timeout must be a positive number")
        
        if "connection_pool_size" in config:
            if not isinstance(config["connection_pool_size"], int) or config["connection_pool_size"] <= 0:
                raise StorageConfigurationError("connection_pool_size must be a positive integer")
        
        if "cache_size" in config:
            if not isinstance(config["cache_size"], int) or config["cache_size"] <= 0:
                raise StorageConfigurationError("cache_size must be a positive integer")
        
        # 验证枚举值
        if "temp_store" in config:
            valid_values = ["memory", "file", "default"]
            if config["temp_store"] not in valid_values:
                raise StorageConfigurationError(f"temp_store must be one of {valid_values}")
        
        if "synchronous_mode" in config:
            valid_values = ["OFF", "NORMAL", "FULL", "EXTRA"]
            if config["synchronous_mode"] not in valid_values:
                raise StorageConfigurationError(f"synchronous_mode must be one of {valid_values}")
        
        if "journal_mode" in config:
            valid_values = ["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"]
            if config["journal_mode"] not in valid_values:
                raise StorageConfigurationError(f"journal_mode must be one of {valid_values}")
    
    def _validate_file_config(self, config: Dict[str, Any]) -> None:
        """验证文件存储配置
        
        Args:
            config: 配置字典
            
        Raises:
            StorageConfigurationError: 配置验证失败
        """
        # 验证必需字段
        if "base_path" not in config or not config["base_path"]:
            raise StorageConfigurationError("base_path is required for file storage")
        
        # 验证数值范围
        if "default_ttl_seconds" in config:
            if not isinstance(config["default_ttl_seconds"], int) or config["default_ttl_seconds"] <= 0:
                raise StorageConfigurationError("default_ttl_seconds must be a positive integer")
        
        if "cleanup_interval_seconds" in config:
            if not isinstance(config["cleanup_interval_seconds"], int) or config["cleanup_interval_seconds"] <= 0:
                raise StorageConfigurationError("cleanup_interval_seconds must be a positive integer")
        
        if "compression_threshold" in config:
            if not isinstance(config["compression_threshold"], int) or config["compression_threshold"] <= 0:
                raise StorageConfigurationError("compression_threshold must be a positive integer")
        
        if "max_files_per_directory" in config:
            if not isinstance(config["max_files_per_directory"], int) or config["max_files_per_directory"] <= 0:
                raise StorageConfigurationError("max_files_per_directory must be a positive integer")
        
        # 验证枚举值
        if "directory_structure" in config:
            valid_values = ["flat", "by_type", "by_date", "by_agent"]
            if config["directory_structure"] not in valid_values:
                raise StorageConfigurationError(f"directory_structure must be one of {valid_values}")
    
    def _process_env_variables(self, config: StorageConfig) -> StorageConfig:
        """处理环境变量注入
        
        Args:
            config: 存储配置
            
        Returns:
            处理后的存储配置
        """
        # 创建配置副本
        processed_config = StorageConfig(
            name=config.name,
            storage_type=config.storage_type,
            enabled=config.enabled,
            is_default=config.is_default,
            config=config.config.copy(),
            description=config.description,
            tags=config.tags.copy()
        )
        
        # 处理配置中的环境变量
        for key, value in processed_config.config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 解析环境变量格式: ${ENV_VAR:DEFAULT}
                env_expr = value[2:-1]  # 移除 ${ 和 }
                
                if ":" in env_expr:
                    env_var, default_value = env_expr.split(":", 1)
                else:
                    env_var, default_value = env_expr, ""
                
                # 获取环境变量值
                env_value = os.getenv(env_var, default_value)
                
                # 尝试转换类型
                processed_config.config[key] = self._convert_env_value(env_value)
        
        return processed_config
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """转换环境变量值类型
        
        Args:
            value: 环境变量值
            
        Returns:
            转换后的值
        """
        # 布尔值
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False
        
        # 整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 字符串
        return value
    
    def export_configs(self, include_defaults: bool = False) -> Dict[str, Any]:
        """导出配置
        
        Args:
            include_defaults: 是否包含默认配置
            
        Returns:
            导出的配置字典
        """
        configs = {}
        
        for name, config in self._configs.items():
            # 跳过默认配置模板（如果不需要包含）
            if not include_defaults and name.endswith("_default"):
                continue
            
            configs[name] = {
                "storage_type": config.storage_type.value,
                "enabled": config.enabled,
                "is_default": config.is_default,
                "config": config.config,
                "description": config.description,
                "tags": config.tags
            }
        
        return {
            "default_config": self._default_config,
            "configs": configs
        }
    
    def import_configs(self, configs_data: Dict[str, Any], merge: bool = True) -> bool:
        """导入配置
        
        Args:
            configs_data: 配置数据
            merge: 是否合并现有配置
            
        Returns:
            是否导入成功
        """
        try:
            if not merge:
                # 清空现有配置
                self._configs.clear()
                self._default_config = None
            
            # 导入默认配置
            if "default_config" in configs_data:
                self._default_config = configs_data["default_config"]
            
            # 导入配置
            if "configs" in configs_data:
                for name, config_data in configs_data["configs"].items():
                    config = StorageConfig(
                        name=name,
                        storage_type=StorageType(config_data["storage_type"]),
                        enabled=config_data.get("enabled", True),
                        is_default=config_data.get("is_default", False),
                        config=config_data.get("config", {}),
                        description=config_data.get("description"),
                        tags=config_data.get("tags", [])
                    )
                    
                    self.register_config(config)
            
            logger.info("Configs imported successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configs: {e}")
            return False