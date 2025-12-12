"""LLM配置管理器

用于管理LLM相关的配置，包括任务组、轮询池、降级策略等。
"""

from typing import Dict, Any, Optional
from src.interfaces.dependency_injection import get_logger
from src.interfaces.config import IConfigManager
from .base_config_manager import BaseConfigManager


logger = get_logger(__name__)


class LLMConfigManager(BaseConfigManager):
    """LLM配置管理器
    
    负责加载和管理LLM相关配置：
    - 任务组配置
    - 轮询池配置
    - 全局降级配置
    - 并发控制配置
    - 速率限制配置
    """
    
    def __init__(self, config_manager: IConfigManager, config_path: Optional[str] = None):
        """初始化LLM配置管理器
        
        Args:
            config_manager: 统一配置管理器
            config_path: 配置文件路径（可选）
        """
        # 缓存各个子配置
        self._task_groups_cache: Optional[Dict[str, Any]] = None
        self._polling_pools_cache: Optional[Dict[str, Any]] = None
        self._global_fallback_cache: Optional[Dict[str, Any]] = None
        self._concurrency_control_cache: Optional[Dict[str, Any]] = None
        self._rate_limiting_cache: Optional[Dict[str, Any]] = None
        
        super().__init__(config_manager, config_path)
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return "llm/config.yaml"
    
    def _get_config_module(self) -> str:
        """获取配置模块名"""
        return "llm"
    
    def _create_config_data(self, config_dict: Dict[str, Any]) -> Any:
        """创建配置数据对象"""
        # 返回原始字典，简化实现
        return type('ConfigData', (), {
            'to_dict': lambda self: config_dict,
            **config_dict
        })()
    
    def _get_validator(self) -> Any:
        """获取配置验证器"""
        from src.infrastructure.config.validation.base_validator import GenericConfigValidator
        return GenericConfigValidator(name="LLMConfigValidator")
    
    def _create_default_config(self) -> Any:
        """创建默认配置"""
        return type('DefaultConfig', (), {
            'to_dict': lambda self: {
                'task_groups': {},
                'polling_pools': {},
                'global_fallback': {},
                'concurrency_control': {},
                'rate_limiting': {}
            }
        })()
    
    def get_task_groups(self) -> Dict[str, Any]:
        """获取所有任务组配置
        
        Returns:
            任务组配置字典
        """
        if self._task_groups_cache is None:
            config_data = self.get_config_data()
            self._task_groups_cache = getattr(config_data, 'task_groups', {})
            if callable(getattr(config_data, 'to_dict', None)):
                self._task_groups_cache = config_data.to_dict().get('task_groups', {})
        return self._task_groups_cache or {}
    
    def get_polling_pools(self) -> Dict[str, Any]:
        """获取所有轮询池配置
        
        Returns:
            轮询池配置字典
        """
        if self._polling_pools_cache is None:
            config_data = self.get_config_data()
            self._polling_pools_cache = getattr(config_data, 'polling_pools', {})
            if callable(getattr(config_data, 'to_dict', None)):
                self._polling_pools_cache = config_data.to_dict().get('polling_pools', {})
        return self._polling_pools_cache or {}
    
    def get_global_fallback(self) -> Dict[str, Any]:
        """获取全局降级配置
        
        Returns:
            全局降级配置字典
        """
        if self._global_fallback_cache is None:
            config_data = self.get_config_data()
            self._global_fallback_cache = getattr(config_data, 'global_fallback', {})
            if callable(getattr(config_data, 'to_dict', None)):
                self._global_fallback_cache = config_data.to_dict().get('global_fallback', {})
        return self._global_fallback_cache or {}
    
    def get_concurrency_control(self) -> Dict[str, Any]:
        """获取并发控制配置
        
        Returns:
            并发控制配置字典
        """
        if self._concurrency_control_cache is None:
            config_data = self.get_config_data()
            self._concurrency_control_cache = getattr(config_data, 'concurrency_control', {})
            if callable(getattr(config_data, 'to_dict', None)):
                self._concurrency_control_cache = config_data.to_dict().get('concurrency_control', {})
        return self._concurrency_control_cache or {}
    
    def get_rate_limiting(self) -> Dict[str, Any]:
        """获取速率限制配置
        
        Returns:
            速率限制配置字典
        """
        if self._rate_limiting_cache is None:
            config_data = self.get_config_data()
            self._rate_limiting_cache = getattr(config_data, 'rate_limiting', {})
            if callable(getattr(config_data, 'to_dict', None)):
                self._rate_limiting_cache = config_data.to_dict().get('rate_limiting', {})
        return self._rate_limiting_cache or {}
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态信息
        
        Returns:
            配置状态信息字典
        """
        return {
            "loaded": self._config_data is not None,
            "config_path": self.config_path,
            "task_groups_count": len(self.get_task_groups()),
            "polling_pools_count": len(self.get_polling_pools()),
            "has_global_fallback": len(self.get_global_fallback()) > 0,
            "has_concurrency_control": len(self.get_concurrency_control()) > 0,
            "has_rate_limiting": len(self.get_rate_limiting()) > 0
        }
    
    def reload_config(self) -> None:
        """重新加载配置"""
        super().reload_config()
        # 清除缓存
        self._task_groups_cache = None
        self._polling_pools_cache = None
        self._global_fallback_cache = None
        self._concurrency_control_cache = None
        self._rate_limiting_cache = None
