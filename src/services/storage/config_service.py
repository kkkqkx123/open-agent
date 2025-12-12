"""存储配置服务

提供存储的配置服务，包含业务逻辑，基于统一配置系统和基础设施层组件。
"""

import os
from typing import Dict, Any, Optional, List

from src.interfaces.dependency_injection import get_logger
from src.interfaces.config import IConfigManager
from src.infrastructure.config.models.storage import StorageConfigData, StorageConfigCollectionData, StorageType
from src.core.config.validation.impl.storage_validator import StorageConfigValidator


logger = get_logger(__name__)


class StorageConfigService:
    """存储配置服务
    
    提供存储的配置加载、管理和验证功能，包含业务逻辑。
    """
    
    def __init__(self, config_manager: IConfigManager, config_path: Optional[str] = None):
        """初始化存储配置服务
        
        Args:
            config_manager: 统一配置管理器
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_manager = config_manager
        self.config_path = config_path or "configs/storage.yaml"
        self._config_collection: Optional[StorageConfigCollectionData] = None
        self._validator = StorageConfigValidator()
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            # 检查配置文件是否存在
            if not self._config_file_exists():
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config_collection = StorageConfigCollectionData()
                self._register_default_templates()
                return
            
            # 使用统一配置管理器加载配置
            config_dict = self.config_manager.load_config(self.config_path, "storage")
            
            # 创建存储配置集合数据
            self._config_collection = StorageConfigCollectionData(config_dict)
            
            # 验证配置
            validation_result = self._validator.validate(config_dict)
            if not validation_result.is_valid:
                logger.error(f"配置验证失败: {validation_result.errors}")
                # 使用默认配置
                self._config_collection = StorageConfigCollectionData()
                self._register_default_templates()
                return
            
            logger.info(f"已加载存储配置: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self._config_collection = StorageConfigCollectionData()
            self._register_default_templates()
    
    def _config_file_exists(self) -> bool:
        """检查配置文件是否存在"""
        try:
            # 使用统一配置管理器的加载器检查文件存在性
            return self.config_manager.loader.exists(self.config_path)
        except Exception:
            # 如果统一配置管理器不支持文件存在检查，使用备用方法
            from pathlib import Path
            return Path(self.config_path).exists()
    
    def _register_default_templates(self) -> None:
        """注册默认配置模板"""
        # 内存存储默认配置
        memory_config = StorageConfigData.create_memory_config("memory_default")
        self._config_collection.add_config(memory_config)
        
        # SQLite存储默认配置
        sqlite_config = StorageConfigData.create_sqlite_config("sqlite_default")
        self._config_collection.add_config(sqlite_config)
        
        # 文件存储默认配置
        file_config = StorageConfigData.create_file_config("file_default")
        self._config_collection.add_config(file_config)
    
    def get_config_collection(self) -> StorageConfigCollectionData:
        """获取存储配置集合
        
        Returns:
            存储配置集合实例
        """
        if self._config_collection is None:
            self._load_config()
        return self._config_collection
    
    def register_config(self, config: StorageConfigData) -> bool:
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
            
            logger.info(f"已注册存储配置: {config.get_name()}")
            return True
            
        except Exception as e:
            logger.error(f"注册配置失败 {config.get_name()}: {e}")
            return False
    
    def unregister_config(self, name: str) -> bool:
        """注销存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否注销成功
        """
        return self.get_config_collection().remove_config(name)
    
    def get_config(self, name: str) -> Optional[StorageConfigData]:
        """获取存储配置
        
        Args:
            name: 配置名称
            
        Returns:
            存储配置或None
        """
        config_dict = self.get_config_collection().get_config(name)
        if config_dict is None:
            return None
        return StorageConfigData(config_dict)
    
    def get_default_config(self) -> Optional[StorageConfigData]:
        """获取默认存储配置
        
        Returns:
            默认存储配置或None
        """
        config_dict = self.get_config_collection().get_default_config()
        if config_dict is None:
            return None
        return StorageConfigData(config_dict)
    
    def list_configs(self, storage_type: Optional[StorageType] = None) -> List[StorageConfigData]:
        """列出存储配置
        
        Args:
            storage_type: 存储类型过滤
            
        Returns:
            存储配置列表
        """
        config_dicts = self.get_config_collection().list_configs(
            storage_type.value if storage_type else None
        )
        return [StorageConfigData(config_dict) for config_dict in config_dicts]
    
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
        self.get_config_collection().set_default_config_name(name)
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
            storage_type = template_config.get_storage_type()
            if storage_type == StorageType.MEMORY.value:
                new_config = StorageConfigData.create_memory_config(new_name)
            elif storage_type == StorageType.SQLITE.value:
                new_config = StorageConfigData.create_sqlite_config(new_name)
            elif storage_type == StorageType.FILE.value:
                new_config = StorageConfigData.create_file_config(new_name)
            else:
                logger.error(f"不支持的存储类型: {storage_type}")
                return False
            
            # 应用覆盖配置
            if overrides:
                config_data = new_config.to_dict()
                config_data['config'].update(overrides)
                new_config = StorageConfigData(config_data)
            
            # 注册新配置
            return self.register_config(new_config)
            
        except Exception as e:
            logger.error(f"从模板创建配置失败 {template_name}: {e}")
            return False
    
    def _process_env_variables(self, config: StorageConfigData) -> StorageConfigData:
        """处理环境变量注入
        
        Args:
            config: 存储配置
            
        Returns:
            处理后的存储配置
        """
        # 创建配置副本
        config_dict = config.to_dict()
        config_data = config_dict.get('config', {}).copy()
        
        # 处理配置中的环境变量
        for key, value in config_data.items():
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
                config_data[key] = self._convert_env_value(env_value)
        
        config_dict['config'] = config_data
        return StorageConfigData(config_dict)
    
    def _convert_env_value(self, value: str) -> Any:
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
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._load_config()
        logger.info("存储配置已重新加载")
    
    def save_config(self, path: Optional[str] = None) -> None:
        """保存配置到文件
        
        Args:
            path: 保存路径，如果为None则使用当前配置路径
        """
        save_path = path or self.config_path
        try:
            # 确保目录存在
            from pathlib import Path
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            import yaml
            config_dict = self.get_config_collection().to_dict()
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"存储配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            验证是否通过
        """
        try:
            config_dict = self.get_config_collection().to_dict()
            validation_result = self._validator.validate(config_dict)
            return validation_result.is_valid
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def export_configs(self, include_defaults: bool = False) -> Dict[str, Any]:
        """导出配置
        
        Args:
            include_defaults: 是否包含默认配置
            
        Returns:
            导出的配置字典
        """
        collection = self.get_config_collection()
        configs = collection.get_configs()
        
        exported_configs = {}
        for name, config_dict in configs.items():
            # 跳过默认配置模板（如果不需要包含）
            if not include_defaults and name.endswith("_default"):
                continue
            
            exported_configs[name] = config_dict
        
        return {
            "default_config": collection.get_default_config_name(),
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
                self._config_collection = StorageConfigCollectionData()
            
            # 导入默认配置
            if "default_config" in configs_data:
                self.get_config_collection().set_default_config_name(configs_data["default_config"])
            
            # 导入配置
            if "configs" in configs_data:
                for name, config_data in configs_data["configs"].items():
                    config = StorageConfigData(config_data)
                    self.register_config(config)
            
            logger.info("配置导入成功")
            return True
            
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
            return False


# 全局配置服务实例
_global_storage_config_service: Optional[StorageConfigService] = None


def get_global_storage_config_service(config_manager: Optional[IConfigManager] = None) -> StorageConfigService:
    """获取全局存储配置服务实例
    
    Args:
        config_manager: 配置管理器，如果为None则使用默认管理器
        
    Returns:
        全局存储配置服务实例
    """
    global _global_storage_config_service
    
    if _global_storage_config_service is None:
        # 如果未提供配置管理器，尝试获取默认管理器
        if config_manager is None:
            try:
                from src.core.config.config_manager import get_default_manager
                config_manager = get_default_manager()
            except ImportError:
                raise RuntimeError("无法获取默认配置管理器")
        
        _global_storage_config_service = StorageConfigService(config_manager)
    
    return _global_storage_config_service


def set_global_storage_config_service(service: StorageConfigService) -> None:
    """设置全局存储配置服务实例
    
    Args:
        service: 存储配置服务实例
    """
    global _global_storage_config_service
    _global_storage_config_service = service