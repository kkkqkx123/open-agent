"""存储配置验证器

提供核心层的存储配置验证功能，包含业务逻辑验证。
"""

import os
from typing import Dict, Any

from src.infrastructure.config.validation.base_validator import BaseConfigValidator
from src.interfaces.common_domain import IValidationResult
from src.infrastructure.config.models.storage import StorageType


class StorageConfigValidator(BaseConfigValidator):
    """存储配置验证器
    
    提供存储配置的验证功能，基于基础设施层的基础验证器，包含业务逻辑验证。
    """
    
    def __init__(self, **kwargs):
        """初始化存储配置验证器"""
        super().__init__("StorageConfigValidator", **kwargs)
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        return module_type == "storage"
    
    def _validate_custom(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """自定义验证逻辑
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 验证配置集合结构
        if 'default_config' in config:
            self._validate_default_config(config, result)
        
        if 'configs' in config:
            self._validate_configs_collection(config['configs'], result)
        
        # 如果是单个配置，验证单个配置
        if 'name' in config and 'storage_type' in config:
            self._validate_single_config(config, result)
    
    def _validate_default_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证默认配置
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        default_config = config.get('default_config')
        if default_config is not None and not isinstance(default_config, str):
            result.add_error("默认配置名称必须是字符串类型")
        
        # 检查默认配置是否存在于配置集合中
        if default_config and 'configs' in config:
            configs = config['configs']
            if not isinstance(configs, dict) or default_config not in configs:
                result.add_error(f"默认配置 '{default_config}' 不存在于配置集合中")
    
    def _validate_configs_collection(self, configs: Dict[str, Any], result: IValidationResult) -> None:
        """验证配置集合
        
        Args:
            configs: 配置集合字典
            result: 验证结果
        """
        if not isinstance(configs, dict):
            result.add_error("配置集合必须是字典类型")
            return
        
        for name, config_data in configs.items():
            if not isinstance(config_data, dict):
                result.add_error(f"配置 '{name}' 必须是字典类型")
                continue
            
            # 验证单个配置
            self._validate_single_config(config_data, result, context_name=name)
    
    def _validate_single_config(self, config: Dict[str, Any], result: IValidationResult, context_name: str = "") -> None:
        """验证单个配置
        
        Args:
            config: 配置字典
            result: 验证结果
            context_name: 上下文名称（用于错误消息）
        """
        context = f"配置 '{context_name}'" if context_name else "配置"
        
        # 验证必需字段
        required_fields = ['name', 'storage_type', 'enabled', 'is_default', 'config']
        self._validate_required_fields(config, required_fields, result)
        
        if not result.is_valid:
            return
        
        # 验证字段类型
        type_rules = {
            'name': str,
            'storage_type': str,
            'enabled': bool,
            'is_default': bool,
            'config': dict,
            'description': str,
            'tags': list
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证存储类型
        if 'storage_type' in config:
            storage_type = config['storage_type']
            if storage_type not in [t.value for t in StorageType]:
                result.add_error(f"{context}: 存储类型 '{storage_type}' 无效，必须是以下之一: {[t.value for t in StorageType]}")
        
        # 验证配置名称
        if 'name' in config:
            name = config['name']
            if not name.strip():
                result.add_error(f"{context}: 配置名称不能为空")
        
        # 验证具体配置数据
        if 'config' in config and 'storage_type' in config:
            self._validate_storage_specific_config(config['config'], config['storage_type'], result, context)
    
    def _validate_storage_specific_config(self, config: Dict[str, Any], storage_type: str, result: IValidationResult, context: str) -> None:
        """验证特定存储类型的配置
        
        Args:
            config: 配置数据字典
            storage_type: 存储类型
            result: 验证结果
            context: 上下文名称
        """
        if storage_type == StorageType.MEMORY.value:
            self._validate_memory_config(config, result, context)
        elif storage_type == StorageType.SQLITE.value:
            self._validate_sqlite_config(config, result, context)
        elif storage_type == StorageType.FILE.value:
            self._validate_file_config(config, result, context)
    
    def _validate_memory_config(self, config: Dict[str, Any], result: IValidationResult, context: str) -> None:
        """验证内存存储配置
        
        Args:
            config: 配置数据字典
            result: 验证结果
            context: 上下文名称
        """
        # 验证字段类型
        type_rules = {
            'max_size': (int, type(None)),
            'max_memory_mb': (int, type(None)),
            'enable_ttl': bool,
            'default_ttl_seconds': int,
            'cleanup_interval_seconds': int,
            'enable_compression': bool,
            'compression_threshold': int,
            'enable_metrics': bool,
            'enable_persistence': bool,
            'persistence_path': (str, type(None)),
            'persistence_interval_seconds': int
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证字段值
        value_rules = {
            'default_ttl_seconds': {'range': (1, 86400 * 7)},  # 1秒到7天
            'cleanup_interval_seconds': {'range': (1, 3600)},  # 1秒到1小时
            'compression_threshold': {'range': (1, 1024 * 1024)},  # 1字节到1MB
            'persistence_interval_seconds': {'range': (60, 86400)}  # 1分钟到24小时
        }
        self._validate_field_values(config, value_rules, result)
        
        # 验证可选字段
        if 'max_size' in config and config['max_size'] is not None:
            if config['max_size'] <= 0:
                result.add_error(f"{context}: max_size 必须为正整数")
        
        if 'max_memory_mb' in config and config['max_memory_mb'] is not None:
            if config['max_memory_mb'] <= 0:
                result.add_error(f"{context}: max_memory_mb 必须为正整数")
        
        # 验证持久化路径
        if 'persistence_path' in config and config['persistence_path']:
            self._validate_file_path(config['persistence_path'], result)
    
    def _validate_sqlite_config(self, config: Dict[str, Any], result: IValidationResult, context: str) -> None:
        """验证SQLite存储配置
        
        Args:
            config: 配置数据字典
            result: 验证结果
            context: 上下文名称
        """
        # 验证必需字段
        required_fields = ['db_path']
        self._validate_required_fields(config, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            'db_path': str,
            'timeout': (int, float),
            'enable_wal_mode': bool,
            'enable_foreign_keys': bool,
            'connection_pool_size': int,
            'enable_auto_vacuum': bool,
            'cache_size': int,
            'temp_store': str,
            'synchronous_mode': str,
            'journal_mode': str,
            'enable_backup': bool,
            'backup_interval_hours': int,
            'backup_path': str,
            'max_backup_files': int
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证字段值
        value_rules = {
            'timeout': {'range': (1.0, 300.0)},  # 1秒到5分钟
            'connection_pool_size': {'range': (1, 100)},
            'cache_size': {'range': (100, 100000)},
            'temp_store': {'enum': ['memory', 'file', 'default']},
            'synchronous_mode': {'enum': ['OFF', 'NORMAL', 'FULL', 'EXTRA']},
            'journal_mode': {'enum': ['DELETE', 'TRUNCATE', 'PERSIST', 'MEMORY', 'WAL', 'OFF']},
            'backup_interval_hours': {'range': (1, 168)},  # 1小时到7天
            'max_backup_files': {'range': (1, 100)}
        }
        self._validate_field_values(config, value_rules, result)
        
        # 验证文件路径
        if 'db_path' in config:
            self._validate_file_path(config['db_path'], result)
        
        if 'backup_path' in config:
            self._validate_file_path(config['backup_path'], result)
    
    def _validate_file_config(self, config: Dict[str, Any], result: IValidationResult, context: str) -> None:
        """验证文件存储配置
        
        Args:
            config: 配置数据字典
            result: 验证结果
            context: 上下文名称
        """
        # 验证必需字段
        required_fields = ['base_path']
        self._validate_required_fields(config, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            'base_path': str,
            'enable_compression': bool,
            'compression_threshold': int,
            'enable_ttl': bool,
            'default_ttl_seconds': int,
            'cleanup_interval_seconds': int,
            'enable_backup': bool,
            'backup_interval_hours': int,
            'backup_path': str,
            'max_backup_files': int,
            'directory_structure': str,
            'file_extension': str,
            'enable_metadata': bool,
            'max_directory_size': (int, type(None)),
            'max_files_per_directory': int
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证字段值
        value_rules = {
            'default_ttl_seconds': {'range': (1, 86400 * 7)},  # 1秒到7天
            'cleanup_interval_seconds': {'range': (1, 3600)},  # 1秒到1小时
            'compression_threshold': {'range': (1, 1024 * 1024)},  # 1字节到1MB
            'backup_interval_hours': {'range': (1, 168)},  # 1小时到7天
            'max_backup_files': {'range': (1, 100)},
            'directory_structure': {'enum': ['flat', 'by_type', 'by_date', 'by_agent']},
            'file_extension': {'enum': ['json', 'yaml', 'pickle', 'msgpack']},
            'max_files_per_directory': {'range': (1, 100000)}
        }
        self._validate_field_values(config, value_rules, result)
        
        # 验证文件路径
        if 'base_path' in config:
            self._validate_file_path(config['base_path'], result)
        
        if 'backup_path' in config:
            self._validate_file_path(config['backup_path'], result)
        
        # 验证可选字段
        if 'max_directory_size' in config and config['max_directory_size'] is not None:
            if config['max_directory_size'] <= 0:
                result.add_error(f"{context}: max_directory_size 必须为正整数")
    
    def _apply_production_rules(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """应用生产环境规则
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        super()._apply_production_rules(config, result)
        
        # 生产环境特定规则
        if 'configs' in config:
            configs = config['configs']
            for name, config_data in configs.items():
                if isinstance(config_data, dict):
                    # 生产环境建议启用备份
                    if config_data.get('storage_type') == StorageType.SQLITE.value:
                        storage_config = config_data.get('config', {})
                        if not storage_config.get('enable_backup', False):
                            result.add_warning(f"生产环境建议为SQLite配置 '{name}' 启用备份")
                    
                    # 生产环境建议启用压缩
                    if config_data.get('storage_type') == StorageType.FILE.value:
                        storage_config = config_data.get('config', {})
                        if not storage_config.get('enable_compression', False):
                            result.add_warning(f"生产环境建议为文件配置 '{name}' 启用压缩")
    
    def _apply_development_rules(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """应用开发环境规则
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        super()._apply_development_rules(config, result)
        
        # 开发环境特定规则
        if 'configs' in config:
            configs = config['configs']
            for name, config_data in configs.items():
                if isinstance(config_data, dict):
                    # 开发环境可以使用内存存储
                    if config_data.get('storage_type') == StorageType.MEMORY.value:
                        result.add_info(f"开发环境使用内存存储配置 '{name}' 是合适的")


def create_storage_config_validator(**kwargs) -> StorageConfigValidator:
    """创建存储配置验证器实例
    
    Args:
        **kwargs: 其他参数
        
    Returns:
        存储配置验证器实例
    """
    return StorageConfigValidator(**kwargs)


__all__ = [
    "StorageConfigValidator",
    "create_storage_config_validator"
]