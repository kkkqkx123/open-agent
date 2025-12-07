"""存储配置管理器实现

提供统一的存储配置管理功能。
"""

import os
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from src.services.logger.injection import get_logger
from src.interfaces.storage.adapter import IStorageConfigManager


logger = get_logger(__name__)


class StorageConfigManager(IStorageConfigManager):
    """存储配置管理器实现
    
    统一管理存储后端和仓库的配置，支持环境变量注入和配置继承。
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径（可选）
        """
        self.logger = get_logger(self.__class__.__name__)
        self._configs: Dict[str, Any] = {}
        self._config_path = config_path or self._get_default_config_path()
        
        # 加载配置
        self._load_configs()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 尝试多个可能的配置文件位置
        possible_paths = [
            "configs/storage.yaml",
            "configs/storage.yml",
            "src/configs/storage.yaml",
            "src/configs/storage.yml",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 如果都不存在，返回默认路径
        return "configs/storage.yaml"
    
    def _load_configs(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._configs = yaml.safe_load(f) or {}
                self.logger.info(f"已加载存储配置文件: {self._config_path}")
            else:
                self.logger.warning(f"配置文件不存在: {self._config_path}，使用默认配置")
                self._configs = self._get_default_configs()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self._configs = self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "backends": {
                "sqlite": {
                    "db_path": "storage.db",
                    "connection_pool_size": 5,
                    "timeout": 30.0,
                    "enable_wal_mode": True,
                    "enable_foreign_keys": True,
                    "enable_auto_vacuum": False,
                    "cache_size": 2000,
                    "temp_store": "memory",
                    "synchronous_mode": "NORMAL",
                    "journal_mode": "WAL",
                    "backup_path": "backups",
                    "enable_compression": False,
                    "compression_threshold": 1024,
                    "enable_ttl": False,
                    "default_ttl_seconds": 3600,
                    "cleanup_interval_seconds": 300,
                    "enable_backup": False,
                    "backup_interval_hours": 24,
                    "max_backup_files": 7
                },
                "memory": {
                    "max_items": 10000,
                    "enable_compression": False,
                    "compression_threshold": 1024,
                    "enable_ttl": False,
                    "default_ttl_seconds": 3600,
                    "cleanup_interval_seconds": 300
                },
                "file": {
                    "base_path": "data/storage",
                    "enable_compression": False,
                    "compression_threshold": 1024,
                    "enable_ttl": False,
                    "default_ttl_seconds": 3600,
                    "cleanup_interval_seconds": 300,
                    "enable_backup": False,
                    "backup_interval_hours": 24,
                    "max_backup_files": 7
                }
            },
            "repositories": {
                "state": {
                    "backend_type": "sqlite",
                    "enable_cache": True,
                    "cache_size": 1000,
                    "cache_ttl": 300
                },
                "history": {
                    "backend_type": "sqlite",
                    "enable_cache": True,
                    "cache_size": 500,
                    "cache_ttl": 600
                },
                "snapshot": {
                    "backend_type": "file",
                    "enable_cache": True,
                    "cache_size": 100,
                    "cache_ttl": 1800
                },
                "checkpoint": {
                    "backend_type": "sqlite",
                    "enable_cache": True,
                    "cache_size": 200,
                    "cache_ttl": 900
                }
            }
        }
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """解析配置中的环境变量
        
        支持格式: ${VAR_NAME:DEFAULT_VALUE}
        
        Args:
            config: 配置值
            
        Returns:
            解析后的配置值
        """
        if isinstance(config, str):
            # 检查是否是环境变量格式
            import re
            pattern = r'\$\{([^:}]+):?([^}]*)\}'
            match = re.match(pattern, config)
            
            if match:
                var_name = match.group(1)
                default_value = match.group(2)
                return os.getenv(var_name, default_value)
            
            return config
        elif isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        else:
            return config
    
    def get_backend_config(self, backend_type: str) -> Dict[str, Any]:
        """获取后端配置
        
        Args:
            backend_type: 后端类型
            
        Returns:
            后端配置字典
        """
        try:
            # 获取后端配置
            backend_configs = self._configs.get("backends", {})
            config = backend_configs.get(backend_type, {})
            
            # 解析环境变量
            resolved_config = self._resolve_env_vars(config)
            
            # 确保返回字典
            if not isinstance(resolved_config, dict):
                self.logger.warning(f"后端 {backend_type} 的配置不是字典格式")
                return {}
            
            self.logger.debug(f"获取后端配置: {backend_type}")
            return resolved_config
            
        except Exception as e:
            self.logger.error(f"获取后端配置失败 {backend_type}: {e}")
            return {}
    
    def get_repository_config(self, repo_type: str) -> Dict[str, Any]:
        """获取仓库配置
        
        Args:
            repo_type: 仓库类型
            
        Returns:
            仓库配置字典
        """
        try:
            # 获取仓库配置
            repo_configs = self._configs.get("repositories", {})
            config = repo_configs.get(repo_type, {})
            
            # 解析环境变量
            resolved_config = self._resolve_env_vars(config)
            
            # 确保返回字典
            if not isinstance(resolved_config, dict):
                self.logger.warning(f"仓库 {repo_type} 的配置不是字典格式")
                return {}
            
            self.logger.debug(f"获取仓库配置: {repo_type}")
            return resolved_config
            
        except Exception as e:
            self.logger.error(f"获取仓库配置失败 {repo_type}: {e}")
            return {}
    
    def update_config(self, config_path: str, config_value: Any) -> None:
        """更新配置
        
        Args:
            config_path: 配置路径（如 "backends.sqlite.db_path"）
            config_value: 配置值
        """
        try:
            # 分割路径
            path_parts = config_path.split('.')
            
            # 导航到目标位置
            current = self._configs
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # 设置值
            current[path_parts[-1]] = config_value
            
            # 保存配置
            self._save_configs()
            
            self.logger.info(f"已更新配置: {config_path} = {config_value}")
            
        except Exception as e:
            self.logger.error(f"更新配置失败 {config_path}: {e}")
            raise
    
    def _save_configs(self) -> None:
        """保存配置到文件"""
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self._config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            # 保存配置
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._configs, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.debug(f"已保存配置文件: {self._config_path}")
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            raise
    
    def reload_configs(self) -> None:
        """重新加载配置"""
        self.logger.info("重新加载配置")
        self._load_configs()
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            完整配置字典
        """
        return self._configs.copy()
    
    def validate_config(self, config_type: str, config: Dict[str, Any]) -> bool:
        """验证配置
        
        Args:
            config_type: 配置类型（backend或repository）
            config: 配置字典
            
        Returns:
            是否有效
        """
        try:
            if config_type == "backend":
                # 验证后端配置
                required_fields = ["backend_type"]
                for field in required_fields:
                    if field not in config:
                        self.logger.error(f"后端配置缺少必需字段: {field}")
                        return False
                
                backend_type = config.get("backend_type")
                if backend_type not in ["sqlite", "memory", "file"]:
                    self.logger.error(f"不支持的后端类型: {backend_type}")
                    return False
                
            elif config_type == "repository":
                # 验证仓库配置
                required_fields = ["backend_type"]
                for field in required_fields:
                    if field not in config:
                        self.logger.error(f"仓库配置缺少必需字段: {field}")
                        return False
                
                backend_type = config.get("backend_type")
                if backend_type not in ["sqlite", "memory", "file"]:
                    self.logger.error(f"不支持的后端类型: {backend_type}")
                    return False
            
            else:
                self.logger.error(f"不支持的配置类型: {config_type}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证配置失败: {e}")
            return False


# 全局配置管理器实例
_global_config_manager: Optional[StorageConfigManager] = None


def get_global_config_manager() -> StorageConfigManager:
    """获取全局配置管理器实例
    
    Returns:
        配置管理器实例
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = StorageConfigManager()
    return _global_config_manager


def set_global_config_manager(config_manager: StorageConfigManager) -> None:
    """设置全局配置管理器实例
    
    Args:
        config_manager: 配置管理器实例
    """
    global _global_config_manager
    _global_config_manager = config_manager