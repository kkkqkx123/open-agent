"""通用配置提供者

提供通用的配置获取和管理功能，可作为其他提供者的基类。
"""

from typing import Dict, Any, Optional, Type
import logging

from .base_provider import BaseConfigProvider
from ..impl.base_impl import IConfigImpl

logger = logging.getLogger(__name__)


class CommonConfigProvider(BaseConfigProvider):
    """通用配置提供者
    
    提供通用的配置获取和管理功能。
    """
    
    def __init__(self, 
                 module_type: str,
                 config_impl: IConfigImpl,
                 model_class: Optional[Type] = None,
                 **kwargs):
        """初始化通用配置提供者
        
        Args:
            module_type: 模块类型
            config_impl: 配置实现
            model_class: 配置模型类
            **kwargs: 其他参数
        """
        super().__init__(module_type, config_impl, **kwargs)
        self.model_class = model_class
        
        logger.debug(f"初始化{module_type}模块通用配置提供者")
    
    def get_config_model(self, config_name: str) -> Any:
        """获取配置模型
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置模型实例
        """
        # 获取配置数据
        config_data = self.get_config(config_name)
        
        # 转换为模型
        return self._create_config_model(config_data)
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        Args:
            config_data: 配置数据
            
        Returns:
            配置模型实例
        """
        if self.model_class:
            try:
                # 如果模型类有from_dict方法，使用它
                if hasattr(self.model_class, 'from_dict'):
                    return self.model_class.from_dict(config_data)
                # 否则尝试直接构造
                else:
                    return self.model_class(**config_data)
            except Exception as e:
                logger.warning(f"创建配置模型失败: {e}")
                return config_data
        
        # 没有模型类，返回原始数据
        return config_data
    
    def get_config_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            config_name: 配置名称
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.get_config(config_name)
        return self._get_nested_value(config, key, default)
    
    def set_config_value(self, config_name: str, key: str, value: Any) -> None:
        """设置配置值（仅在内存中，不持久化）
        
        Args:
            config_name: 配置名称
            key: 配置键
            value: 配置值
        """
        if config_name in self._config_cache:
            self._set_nested_value(self._config_cache[config_name], key, value)
            logger.debug(f"设置{self.module_type}模块配置值: {config_name}.{key} = {value}")
        else:
            logger.warning(f"配置{config_name}未加载到缓存，无法设置值")
    
    def has_config_key(self, config_name: str, key: str) -> bool:
        """检查配置键是否存在
        
        Args:
            config_name: 配置名称
            key: 配置键
            
        Returns:
            是否存在
        """
        config = self.get_config(config_name)
        return self._has_nested_key(config, key)
    
    def get_config_section(self, config_name: str, section: str) -> Dict[str, Any]:
        """获取配置段
        
        Args:
            config_name: 配置名称
            section: 段名称
            
        Returns:
            配置段
        """
        config = self.get_config(config_name)
        section_data = self._get_nested_value(config, section, {})
        
        if not isinstance(section_data, dict):
            logger.warning(f"配置段{section}不是字典类型")
            return {}
        
        return section_data
    
    def merge_configs(self, config_names: list[str]) -> Dict[str, Any]:
        """合并多个配置
        
        Args:
            config_names: 配置名称列表
            
        Returns:
            合并后的配置
        """
        merged = {}
        
        for config_name in config_names:
            config = self.get_config(config_name)
            merged = self._deep_merge(merged, config)
        
        return merged
    
    def validate_config_structure(self, config_name: str, required_keys: list[str]) -> bool:
        """验证配置结构
        
        Args:
            config_name: 配置名称
            required_keys: 必需的键列表
            
        Returns:
            是否有效
        """
        config = self.get_config(config_name)
        
        for key in required_keys:
            if not self._has_nested_key(config, key):
                logger.error(f"配置{config_name}缺少必需的键: {key}")
                return False
        
        return True
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """获取嵌套值
        
        Args:
            data: 数据字典
            key: 键（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            值
        """
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """设置嵌套值
        
        Args:
            data: 数据字典
            key: 键（支持点号分隔的嵌套键）
            value: 值
        """
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _has_nested_key(self, data: Dict[str, Any], key: str) -> bool:
        """检查是否存在嵌套键
        
        Args:
            data: 数据字典
            key: 键（支持点号分隔的嵌套键）
            
        Returns:
            是否存在
        """
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False
        
        return True
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典
        
        Args:
            dict1: 字典1
            dict2: 字典2
            
        Returns:
            合并后的字典
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _preload_common_configs(self) -> None:
        """预加载常用配置"""
        # 子类可以重写此方法以预加载常用配置
        pass
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            统计信息
        """
        stats = self._get_cache_stats()
        stats.update({
            "module_type": self.module_type,
            "model_class": self.model_class.__name__ if self.model_class else None,
            "available_configs": self.list_available_configs()
        })
        return stats