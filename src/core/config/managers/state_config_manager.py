"""状态配置管理器

提供状态管理的配置加载、管理和验证功能。
"""

from typing import Dict, Any, Optional

from src.interfaces.config import IConfigManager
from src.infrastructure.config.models.state import StateConfigData
from src.core.config.validation.impl.state_validator import StateConfigValidator
from src.core.config.managers.base_config_manager import BaseConfigManager
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class StateConfigManager(BaseConfigManager):
    """状态配置管理器
    
    提供状态管理的配置加载、管理和验证功能。
    """
    
    def __init__(self, config_manager: IConfigManager, config_path: Optional[str] = None):
        """初始化状态配置管理器
        
        Args:
            config_manager: 统一配置管理器
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self._validator = StateConfigValidator()
        super().__init__(config_manager, config_path)
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return "configs/state_management.yaml"
    
    def _get_config_module(self) -> str:
        """获取配置模块名"""
        return "state"
    
    def _create_config_data(self, config_dict: Dict[str, Any]) -> StateConfigData:
        """创建配置数据对象"""
        return StateConfigData(config_dict)
    
    def _get_validator(self) -> StateConfigValidator:
        """获取配置验证器"""
        return self._validator
    
    def _create_default_config(self) -> StateConfigData:
        """创建默认配置"""
        return StateConfigData()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        config_data = self.get_config_data()
        return config_data.get(key, default)
    
    def get_core_config(self) -> Dict[str, Any]:
        """获取核心配置
        
        Returns:
            核心配置字典
        """
        return self.get_config_data().get_core_config()
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置
        
        Returns:
            存储配置字典
        """
        return self.get_config_data().get_storage_config()
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置
        
        Returns:
            缓存配置字典
        """
        return self.get_config_data().get_cache_config()
    
    def get_serializer_config(self) -> Dict[str, Any]:
        """获取序列化配置
        
        Returns:
            序列化配置字典
        """
        return self.get_config_data().get_serializer_config()
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置
        
        Returns:
            工作流配置字典
        """
        return self.get_config_data().get_workflow_config()
    
    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置
        
        Returns:
            工具配置字典
        """
        return self.get_config_data().get_tools_config()
    
    def get_sessions_config(self) -> Dict[str, Any]:
        """获取会话配置
        
        Returns:
            会话配置字典
        """
        return self.get_config_data().get_sessions_config()
    
    def get_threads_config(self) -> Dict[str, Any]:
        """获取线程配置
        
        Returns:
            线程配置字典
        """
        return self.get_config_data().get_threads_config()
    
    def get_checkpoints_config(self) -> Dict[str, Any]:
        """获取检查点配置
        
        Returns:
            检查点配置字典
        """
        return self.get_config_data().get_checkpoints_config()
    
    def is_debug_mode(self) -> bool:
        """检查是否为调试模式
        
        Returns:
            是否为调试模式
        """
        return self.get_config_value('development.debug_mode', False)
    
    def is_verbose_logging(self) -> bool:
        """检查是否启用详细日志
        
        Returns:
            是否启用详细日志
        """
        return self.get_config_value('development.verbose_logging', False)
    
    def is_monitoring_enabled(self) -> bool:
        """检查是否启用监控
        
        Returns:
            是否启用监控
        """
        return self.get_config_value('monitoring.enabled', True)
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            updates: 更新的配置字典
        """
        config_data = self.get_config_data()
        current_config = config_data.to_dict()
        
        # 深度更新配置
        self._deep_update(current_config, updates)
        
        # 验证更新后的配置
        validation_result = self._validator.validate(current_config)
        if not validation_result.is_valid:
            logger.error(f"配置更新验证失败: {validation_result.errors}")
            raise ValueError(f"配置更新验证失败: {validation_result.errors}")
        
        # 更新配置数据
        self._config_data = StateConfigData(current_config)
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
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要字典
        """
        config_data = self.get_config_data()
        return {
            'config_path': self.config_path,
            'core': config_data.get_core_config(),
            'serializer': {
                'format': config_data.get('serializer.format'),
                'compression': config_data.get('serializer.compression')
            },
            'cache': {
                'enabled': config_data.get('cache.enabled'),
                'max_size': config_data.get('cache.max_size'),
                'ttl': config_data.get('cache.ttl')
            },
            'storage': {
                'default_type': config_data.get('storage.default_type')
            },
            'monitoring': {
                'enabled': config_data.get('monitoring.enabled')
            },
            'development': {
                'debug_mode': config_data.get('development.debug_mode')
            }
        }


# 全局配置管理器实例
_global_state_config_manager: Optional[StateConfigManager] = None


def get_global_state_config_manager(config_manager: Optional[IConfigManager] = None) -> StateConfigManager:
    """获取全局状态配置管理器实例
    
    Args:
        config_manager: 配置管理器，如果为None则使用默认管理器
        
    Returns:
        全局状态配置管理器实例
    """
    global _global_state_config_manager
    
    if _global_state_config_manager is None:
        # 如果未提供配置管理器，尝试获取默认管理器
        if config_manager is None:
            try:
                from src.services.container import get_global_container
                _container = get_global_container()
                config_manager = _container.get(IConfigManager)
            except Exception:
                raise RuntimeError("无法获取默认配置管理器")
        
        assert config_manager is not None, "配置管理器为None"
        _global_state_config_manager = StateConfigManager(config_manager)
    
    return _global_state_config_manager


def set_global_state_config_manager(manager: StateConfigManager) -> None:
    """设置全局状态配置管理器实例
    
    Args:
        manager: 状态配置管理器实例
    """
    global _global_state_config_manager
    _global_state_config_manager = manager
