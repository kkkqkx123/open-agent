"""存储配置管理器

提供存储的配置加载、管理和验证功能，包含业务逻辑。
"""

from typing import Dict, Any, Optional, List

from src.interfaces.config import IConfigManager
from src.core.config.models.storage_config import StorageConfig, StorageConfigCollection, StorageType
from src.core.config.validation.impl.storage_validator import StorageConfigValidator
from src.core.config.managers.base_config_manager import BaseConfigManager
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class StorageConfigManager(BaseConfigManager):
    """存储配置管理器
    
    提供存储的配置加载、管理和验证功能。
    """
    
    def __init__(self, config_manager: IConfigManager, config_path: Optional[str] = None):
        """初始化存储配置管理器
        
        Args:
            config_manager: 统一配置管理器
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self._validator = StorageConfigValidator()
        super().__init__(config_manager, config_path)
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return "configs/storage.yaml"
    
    def _get_config_module(self) -> str:
        """获取配置模块名"""
        return "storage"
    
    def _create_config_data(self, config_dict: Dict[str, Any]) -> StorageConfigCollection:
        """创建配置数据对象"""
        return StorageConfigCollection.from_dict(config_dict)
    
    def _get_validator(self) -> StorageConfigValidator:
        """获取配置验证器"""
        return self._validator
    
    def _create_default_config(self) -> StorageConfigCollection:
        """创建默认配置"""
        collection = StorageConfigCollection()
        self._register_default_templates(collection)
        return collection
    
    def _register_default_templates(self, collection: Optional[StorageConfigCollection] = None) -> None:
        """注册默认配置模板"""
        if collection is None:
            collection = self.get_config_collection()
        
        # 内存存储默认配置
        memory_config = StorageConfig(
            name="memory_default",
            storage_type=StorageType.MEMORY,
            is_default=True
        )
        collection.add_config(memory_config)
        
        # SQLite存储默认配置
        sqlite_config = StorageConfig(
            name="sqlite_default",
            storage_type=StorageType.SQLITE
        )
        collection.add_config(sqlite_config)
        
        # 文件存储默认配置
        file_config = StorageConfig(
            name="file_default",
            storage_type=StorageType.FILE
        )
        collection.add_config(file_config)
    
    def get_config_collection(self) -> StorageConfigCollection:
        """获取存储配置集合
        
        Returns:
            存储配置集合实例
        """
        config_data = self.get_config_data()
        assert isinstance(config_data, StorageConfigCollection), "配置数据类型错误"
        return config_data
    
    def register_config(self, config: StorageConfig) -> bool:
        """注册存储配置
        
        Args:
            config: 存储配置
            
        Returns:
            是否注册成功
        """
        try:
            # 验证配置
            config_dict = config.to_dict()
            validation_result = self._validator.validate(config_dict)
            if not validation_result.is_valid:
                logger.error(f"配置验证失败: {validation_result.errors}")
                return False
            
            # 处理环境变量
            processed_config = self._process_env_variables(config)
            
            # 添加到配置集合
            self.get_config_collection().add_config(processed_config)
            
            logger.info(f"已注册存储配置: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"注册配置失败 {config.name}: {e}")
            return False
    
    def unregister_config(self, name: str) -> bool:
        """注销存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否注销成功
        """
        return self.get_config_collection().remove_config(name)
    
    def get_config(self, name: str) -> Optional[StorageConfig]:
        """获取存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            存储配置或None
        """
        return self.get_config_collection().get_config(name)
    
    def get_default_config(self) -> Optional[StorageConfig]:
        """获取默认存储配置
        
        Returns:
            默认存储配置或None
        """
        collection = self.get_config_collection()
        return collection.get_default_config()
    
    def list_configs(self, storage_type: Optional[StorageType] = None) -> List[StorageConfig]:
        """列出存储配置
        
        Args:
            storage_type: 存储类型过滤
            
        Returns:
            存储配置列表
        """
        return self.get_config_collection().list_configs(storage_type)
    
    def set_default_config(self, name: str) -> bool:
        """设置默认存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否设置成功
        """
        config = self.get_config(name)
        if config is None:
            logger.warning(f"配置 {name} 不存在")
            return False
        
        # 更新配置集合的默认配置
        collection = self.get_config_collection()
        collection.default_config = name
        logger.info(f"已设置默认配置: {name}")
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
                logger.error(f"模板配置 {template_name} 不存在")
                return False
            
            # 创建新配置
            new_config = StorageConfig(
                name=new_name,
                storage_type=template_config.storage_type,
                config=template_config.config.copy() if template_config.config else {}
            )
            
            # 应用覆盖配置
            if overrides:
                new_config.config.update(overrides)
            
            # 注册新配置
            return self.register_config(new_config)
            
        except Exception as e:
            logger.error(f"从模板创建配置失败 {template_name}: {e}")
            return False
    
    def export_configs(self, include_defaults: bool = False) -> Dict[str, Any]:
        """导出配置
        
        Args:
            include_defaults: 是否包含默认配置
            
        Returns:
            导出的配置字典
        """
        collection = self.get_config_collection()
        
        exported_configs = {}
        for name, config in collection.configs.items():
            # 跳过默认配置模板（如果不需要包含）
            if not include_defaults and name.endswith("_default"):
                continue
            
            exported_configs[name] = config.to_dict()
        
        return {
            "default_config": collection.default_config,
            "configs": exported_configs
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
                self._config_data = StorageConfigCollection()
            
            # 导入默认配置
            if "default_config" in configs_data:
                collection = self.get_config_collection()
                collection.default_config = configs_data["default_config"]
            
            # 导入配置
            if "configs" in configs_data:
                for name, config_data in configs_data["configs"].items():
                    config = StorageConfig.from_dict(config_data)
                    self.register_config(config)
            
            logger.info("配置导入成功")
            return True
            
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
            return False


# 全局配置管理器实例
_global_storage_config_manager: Optional[StorageConfigManager] = None


def get_global_storage_config_manager(config_manager: Optional[IConfigManager] = None) -> StorageConfigManager:
    """获取全局存储配置管理器实例
    
    Args:
        config_manager: 配置管理器，如果为None则使用默认管理器
        
    Returns:
        全局存储配置管理器实例
    """
    global _global_storage_config_manager
    
    if _global_storage_config_manager is None:
        # 如果未提供配置管理器，尝试获取默认管理器
        if config_manager is None:
            try:
                from src.services.container import get_global_container
                _container = get_global_container()
                config_manager = _container.get(IConfigManager)
            except Exception:
                raise RuntimeError("无法获取默认配置管理器")
        
        assert config_manager is not None, "配置管理器为None"
        _global_storage_config_manager = StorageConfigManager(config_manager)
    
    return _global_storage_config_manager


def set_global_storage_config_manager(manager: StorageConfigManager) -> None:
    """设置全局存储配置管理器实例
    
    Args:
        manager: 存储配置管理器实例
    """
    global _global_storage_config_manager
    _global_storage_config_manager = manager

