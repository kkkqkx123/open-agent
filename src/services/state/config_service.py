"""状态配置服务

提供状态管理的配置服务，包含业务逻辑，基于统一配置系统和基础设施层组件。
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from src.interfaces.dependency_injection import get_logger
from src.interfaces.config import IConfigManager
from src.infrastructure.config.models.state import StateConfigData
from src.core.config.validation.impl.state_validator import StateConfigValidator


logger = get_logger(__name__)


class StateConfigService:
    """状态配置服务
    
    提供状态管理的配置加载、管理和验证功能，包含业务逻辑。
    """
    
    def __init__(self, config_manager: IConfigManager, config_path: Optional[str] = None):
        """初始化状态配置服务
        
        Args:
            config_manager: 统一配置管理器
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_manager = config_manager
        self.config_path = config_path or "configs/state_management.yaml"
        self._config_data: Optional[StateConfigData] = None
        self._validator = StateConfigValidator()
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            # 检查配置文件是否存在
            if not self._config_file_exists():
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config_data = StateConfigData()
                return
            
            # 使用统一配置管理器加载配置
            config_dict = self.config_manager.load_config(self.config_path, "state")
            
            # 创建状态配置数据
            self._config_data = StateConfigData(config_dict)
            
            # 验证配置
            validation_result = self._validator.validate(config_dict)
            if not validation_result.is_valid:
                logger.error(f"配置验证失败: {validation_result.errors}")
                # 使用默认配置
                self._config_data = StateConfigData()
                return
            
            logger.info(f"已加载状态管理配置: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self._config_data = StateConfigData()
    
    def _config_file_exists(self) -> bool:
        """检查配置文件是否存在"""
        try:
            # 使用统一配置管理器的加载器检查文件存在性
            return self.config_manager.loader.exists(self.config_path)
        except Exception:
            # 如果统一配置管理器不支持文件存在检查，使用备用方法
            return Path(self.config_path).exists()
    
    def get_config_data(self) -> StateConfigData:
        """获取状态配置数据
        
        Returns:
            状态配置数据实例
        """
        if self._config_data is None:
            self._load_config()
        return self._config_data
    
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
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._load_config()
        logger.info("状态配置已重新加载")
    
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
            config_dict = self.get_config_data().to_dict()
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"状态配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            验证是否通过
        """
        try:
            config_dict = self.get_config_data().to_dict()
            validation_result = self._validator.validate(config_dict)
            return validation_result.is_valid
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
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


# 全局配置服务实例
_global_state_config_service: Optional[StateConfigService] = None


def get_global_state_config_service(config_manager: Optional[IConfigManager] = None) -> StateConfigService:
    """获取全局状态配置服务实例
    
    Args:
        config_manager: 配置管理器，如果为None则使用默认管理器
        
    Returns:
        全局状态配置服务实例
    """
    global _global_state_config_service
    
    if _global_state_config_service is None:
        # 如果未提供配置管理器，尝试获取默认管理器
        if config_manager is None:
            try:
                from src.core.config.config_manager import get_default_manager
                config_manager = get_default_manager()
            except ImportError:
                raise RuntimeError("无法获取默认配置管理器")
        
        _global_state_config_service = StateConfigService(config_manager)
    
    return _global_state_config_service


def set_global_state_config_service(service: StateConfigService) -> None:
    """设置全局状态配置服务实例
    
    Args:
        service: 状态配置服务实例
    """
    global _global_state_config_service
    _global_state_config_service = service