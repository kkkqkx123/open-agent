"""状态管理配置设置

提供状态管理的配置加载和管理功能。
"""

import os
from src.services.logger import get_logger
from typing import Any, Dict, Optional, List
from pathlib import Path

from ...config.config_manager import get_default_manager, ConfigManager


logger = get_logger(__name__)


class StateManagementConfig:
    """状态管理配置类
    
    负责加载和管理状态管理的配置。
    """
    
    def __init__(self, config_path: Optional[str] = None, config_manager: Optional[ConfigManager] = None):
        """初始化配置管理器
         
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            config_manager: 配置管理器，如果为None则使用默认管理器
        """
        self.config_path = config_path or "configs/state_management.yaml"
        self._config: Dict[str, Any] = {}
        self.config_manager = config_manager or get_default_manager()
         
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_manager.loader.exists(self.config_path):
                self._config = self.config_manager.load_config_for_module(
                    self.config_path,
                    "state"
                )
                logger.info(f"已加载状态管理配置: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'core': {
                'default_ttl': 3600,
                'max_states': 10000,
                'cleanup_interval': 300
            },
            'serializer': {
                'format': 'json',
                'compression': True,
                'compression_threshold': 1024
            },
            'cache': {
                'enabled': True,
                'max_size': 1000,
                'ttl': 300,
                'eviction_policy': 'lru',
                'enable_serialization': False,
                'serialization_format': 'json'
            },
            'storage': {
                'default_type': 'memory',
                'memory': {
                    'max_size': 10000
                },
                'sqlite': {
                    'database_path': 'data/states.db',
                    'connection_pool_size': 10,
                    'compression': True,
                    'compression_threshold': 1024
                },
                'file': {
                    'base_path': 'data/states',
                    'format': 'json',
                    'compression': False,
                    'create_subdirs': True
                }
            },
            'validation': {
                'enabled': True,
                'strict_mode': False,
                'custom_validators': []
            },
            'lifecycle': {
                'auto_cleanup': True,
                'cleanup_interval': 300,
                'event_handlers': []
            },
            'specialized': {
                'workflow': {
                    'max_iterations': 100,
                    'message_history_limit': 1000,
                    'auto_save': True
                },
                'tools': {
                    'context_isolation': True,
                    'auto_expiration': True,
                    'default_ttl': 1800
                },
                'sessions': {
                    'auto_cleanup': True,
                    'max_inactive_duration': 3600
                },
                'threads': {
                    'auto_cleanup': True,
                    'max_inactive_duration': 7200
                },
                'checkpoints': {
                    'auto_cleanup': True,
                    'max_checkpoints_per_thread': 50,
                    'cleanup_interval': 600
                }
            },
            'monitoring': {
                'enabled': True,
                'statistics_interval': 60,
                'performance_tracking': True,
                'memory_tracking': True
            },
            'error_handling': {
                'retry_attempts': 3,
                'retry_delay': 1.0,
                'fallback_to_memory': True,
                'log_errors': True
            },
            'development': {
                'debug_mode': False,
                'verbose_logging': False,
                'enable_profiling': False,
                'mock_storage': False
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置
        
        Returns:
            配置字典
        """
        return self._config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_core_config(self) -> Dict[str, Any]:
        """获取核心配置
        
        Returns:
            核心配置字典
        """
        return self.get('core', {})
    
    def get_serializer_config(self) -> Dict[str, Any]:
        """获取序列化配置
        
        Returns:
            序列化配置字典
        """
        return self.get('serializer', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置
        
        Returns:
            缓存配置字典
        """
        return self.get('cache', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置
        
        Returns:
            存储配置字典
        """
        return self.get('storage', {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """获取验证配置
        
        Returns:
            验证配置字典
        """
        return self.get('validation', {})
    
    def get_lifecycle_config(self) -> Dict[str, Any]:
        """获取生命周期配置
        
        Returns:
            生命周期配置字典
        """
        return self.get('lifecycle', {})
    
    def get_specialized_config(self) -> Dict[str, Any]:
        """获取特化配置
        
        Returns:
            特化配置字典
        """
        return self.get('specialized', {})
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置
        
        Returns:
            工作流配置字典
        """
        return self.get('specialized.workflow', {})
    
    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置
        
        Returns:
            工具配置字典
        """
        return self.get('specialized.tools', {})
    
    def get_sessions_config(self) -> Dict[str, Any]:
        """获取会话配置
        
        Returns:
            会话配置字典
        """
        return self.get('specialized.sessions', {})
    
    def get_threads_config(self) -> Dict[str, Any]:
        """获取线程配置
        
        Returns:
            线程配置字典
        """
        return self.get('specialized.threads', {})
    
    def get_checkpoints_config(self) -> Dict[str, Any]:
        """获取检查点配置
        
        Returns:
            检查点配置字典
        """
        return self.get('specialized.checkpoints', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置
        
        Returns:
            监控配置字典
        """
        return self.get('monitoring', {})
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """获取错误处理配置
        
        Returns:
            错误处理配置字典
        """
        return self.get('error_handling', {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """获取开发配置
        
        Returns:
            开发配置字典
        """
        return self.get('development', {})
    
    def is_debug_mode(self) -> bool:
        """检查是否为调试模式
        
        Returns:
            是否为调试模式
        """
        return self.get('development.debug_mode', False)
    
    def is_verbose_logging(self) -> bool:
        """检查是否启用详细日志
        
        Returns:
            是否启用详细日志
        """
        return self.get('development.verbose_logging', False)
    
    def is_monitoring_enabled(self) -> bool:
        """检查是否启用监控
        
        Returns:
            是否启用监控
        """
        return self.get('monitoring.enabled', True)
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._load_config()
        logger.info("配置已重新加载")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            updates: 更新的配置字典
        """
        self._deep_update(self._config, updates)
        logger.info("配置已更新")
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """深度更新字典
        
        Args:
            target: 目标字典
            source: 源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def save_config(self, path: Optional[str] = None) -> None:
        """保存配置到文件
        
        Args:
            path: 保存路径，如果为None则使用当前配置路径
        """
        save_path = path or self.config_path
        try:
            # 确保目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            import yaml
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def validate_config(self) -> List[str]:
        """验证配置
        
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证必需的配置项
        required_sections = ['core', 'serializer', 'cache', 'storage']
        for section in required_sections:
            if section not in self._config:
                errors.append(f"缺少必需的配置节: {section}")
        
        # 验证序列化配置
        serializer_config = self.get_serializer_config()
        if serializer_config.get('format') not in ['json', 'pickle', 'msgpack']:
            errors.append("不支持的序列化格式")
        
        # 验证缓存配置
        cache_config = self.get_cache_config()
        if cache_config.get('eviction_policy') not in ['lru', 'lfu', 'fifo']:
            errors.append("不支持的缓存驱逐策略")
        
        # 验证存储配置
        storage_config = self.get_storage_config()
        if storage_config.get('default_type') not in ['memory', 'sqlite', 'file']:
            errors.append("不支持的存储类型")
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要字典
        """
        return {
            'config_path': self.config_path,
            'core': self.get_core_config(),
            'serializer': {
                'format': self.get('serializer.format'),
                'compression': self.get('serializer.compression')
            },
            'cache': {
                'enabled': self.get('cache.enabled'),
                'max_size': self.get('cache.max_size'),
                'ttl': self.get('cache.ttl')
            },
            'storage': {
                'default_type': self.get('storage.default_type')
            },
            'monitoring': {
                'enabled': self.get('monitoring.enabled')
            },
            'development': {
                'debug_mode': self.get('development.debug_mode')
            }
        }


# 全局配置实例
_global_config: Optional[StateManagementConfig] = None


def get_global_config() -> StateManagementConfig:
    """获取全局配置实例
    
    Returns:
        全局配置实例
    """
    global _global_config
    if _global_config is None:
        _global_config = StateManagementConfig()
    return _global_config


def set_global_config(config: StateManagementConfig) -> None:
    """设置全局配置实例
    
    Args:
        config: 配置实例
    """
    global _global_config
    _global_config = config