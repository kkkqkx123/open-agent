"""配置提供者基类

定义配置提供者的基础实现类，提供配置获取、缓存和模型转换的通用框架。
"""

from typing import Dict, Any, Optional, Type
from pathlib import Path
import logging
from datetime import datetime, timedelta

from src.interfaces.config.provider import IConfigProvider
from ..impl.base_impl import IConfigImpl

logger = logging.getLogger(__name__)


class BaseConfigProvider(IConfigProvider):
    """配置提供者基类
    
    提供配置获取、缓存和模型转换的通用功能。
    """
    
    def __init__(self,
                 module_type: str,
                 config_impl: IConfigImpl,
                 cache_enabled: bool = True,
                 cache_ttl: int = 300,
                 model_class: Optional[Type] = None,
                 **kwargs: Any):
        """初始化配置提供者
        
        Args:
            module_type: 模块类型
            config_impl: 配置实现
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存生存时间（秒）
            model_class: 配置模型类
            **kwargs: 其他参数
        """
        self.module_type = module_type
        self.config_impl = config_impl
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.model_class = model_class
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # 配置模型缓存
        self._model_cache: Dict[str, Any] = {}
        self._model_cache_timestamps: Dict[str, datetime] = {}
        
        logger.debug(f"初始化{module_type}模块配置提供者")
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """获取配置数据
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置数据
        """
        # 检查缓存
        if self.cache_enabled and self._is_cache_valid(config_name, self._config_cache, self._cache_timestamps):
            logger.debug(f"从缓存获取{self.module_type}模块配置: {config_name}")
            return self._config_cache[config_name].copy()
        
        # 加载配置
        config_path = self._resolve_config_path(config_name)
        config_data = self.config_impl.load_config(config_path)
        
        # 更新缓存
        if self.cache_enabled:
            self._config_cache[config_name] = config_data.copy()
            self._cache_timestamps[config_name] = datetime.now()
        
        logger.debug(f"加载{self.module_type}模块配置: {config_name}")
        return config_data
    
    def get_config_model(self, config_name: str) -> Any:
        """获取配置模型
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置模型实例
        """
        # 检查模型缓存
        if self.cache_enabled and self._is_cache_valid(config_name, self._model_cache, self._model_cache_timestamps):
            logger.debug(f"从缓存获取{self.module_type}模块配置模型: {config_name}")
            return self._model_cache[config_name]
        
        # 获取配置数据
        config_data = self.get_config(config_name)
        
        # 转换为模型
        model = self._create_config_model(config_data)
        
        # 更新模型缓存
        if self.cache_enabled:
            self._model_cache[config_name] = model
            self._model_cache_timestamps[config_name] = datetime.now()
        
        logger.debug(f"创建{self.module_type}模块配置模型: {config_name}")
        return model
    
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
        merged: Dict[str, Any] = {}
        
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
    
    def reload_config(self, config_name: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            重新加载的配置数据
        """
        logger.info(f"重新加载{self.module_type}模块配置: {config_name}")
        
        # 清除缓存
        self._clear_cache_for_config(config_name)
        
        # 重新加载
        return self.get_config(config_name)
    
    def reload_all_configs(self) -> None:
        """重新加载所有配置"""
        logger.info(f"重新加载{self.module_type}模块所有配置")
        
        # 清除所有缓存
        self._clear_all_caches()
        
        # 预加载常用配置（子类可重写）
        self._preload_common_configs()
    
    def list_available_configs(self) -> list[str]:
        """列出可用配置
        
        Returns:
            可用配置列表
        """
        try:
            # 获取模块配置目录
            config_dir = Path("configs") / self.module_type
            
            if not config_dir.exists():
                return []
            
            # 扫描配置文件
            configs = []
            for file_path in config_dir.glob("*.yaml"):
                configs.append(file_path.stem)
            
            for file_path in config_dir.glob("*.yml"):
                configs.append(file_path.stem)
            
            return sorted(configs)
            
        except Exception as e:
            logger.error(f"列出{self.module_type}模块配置失败: {e}")
            return []
    
    def validate_config(self, config_name: str) -> bool:
        """验证配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            是否有效
        """
        try:
            self.get_config(config_name)
            return True
        except Exception as e:
            logger.error(f"配置验证失败 {config_name}: {e}")
            return False
    
    def get_config_info(self, config_name: str) -> Dict[str, Any]:
        """获取配置信息
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置信息
        """
        info = {
            "module_type": self.module_type,
            "config_name": config_name,
            "config_path": self._resolve_config_path(config_name),
            "cache_enabled": self.cache_enabled,
            "is_cached": self._is_config_cached(config_name),
            "is_valid": self.validate_config(config_name)
        }
        
        # 添加缓存时间戳
        if config_name in self._cache_timestamps:
            info["cached_at"] = self._cache_timestamps[config_name].isoformat()
        
        return info
    
    def clear_cache(self, config_name: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_name: 配置名称，如果为None则清除所有缓存
        """
        if config_name:
            self._clear_cache_for_config(config_name)
            logger.debug(f"清除{self.module_type}模块配置缓存: {config_name}")
        else:
            self._clear_all_caches()
            logger.debug(f"清除{self.module_type}模块所有配置缓存")
    
    def set_cache_ttl(self, ttl: int) -> None:
        """设置缓存生存时间
        
        Args:
            ttl: 缓存生存时间（秒）
        """
        self.cache_ttl = ttl
        logger.debug(f"设置{self.module_type}模块配置缓存TTL: {ttl}秒")
    
    def enable_cache(self, enabled: bool) -> None:
        """启用或禁用缓存
        
        Args:
            enabled: 是否启用缓存
        """
        self.cache_enabled = enabled
        if not enabled:
            self._clear_all_caches()
        logger.debug(f"{self.module_type}模块配置缓存: {'启用' if enabled else '禁用'}")
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        子类可以重写此方法以实现模块特定的模型创建逻辑。
        
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
    
    def _resolve_config_path(self, config_name: str) -> str:
        """解析配置文件路径
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置文件路径
        """
        # 构建模块特定的配置路径
        config_path = f"{self.module_type}/{config_name}"
        
        # 如果没有扩展名，添加.yaml
        if not config_name.endswith(('.yaml', '.yml')):
            config_path += ".yaml"
        
        return config_path
    
    def _is_cache_valid(self, 
                       config_name: str, 
                       cache: Dict[str, Any], 
                       timestamps: Dict[str, datetime]) -> bool:
        """检查缓存是否有效
        
        Args:
            config_name: 配置名称
            cache: 缓存字典
            timestamps: 时间戳字典
            
        Returns:
            是否有效
        """
        if config_name not in cache or config_name not in timestamps:
            return False
        
        # 检查是否过期
        cache_time = timestamps[config_name]
        expiry_time = cache_time + timedelta(seconds=self.cache_ttl)
        
        return datetime.now() < expiry_time
    
    def _is_config_cached(self, config_name: str) -> bool:
        """检查配置是否已缓存
        
        Args:
            config_name: 配置名称
            
        Returns:
            是否已缓存
        """
        return (config_name in self._config_cache and 
                config_name in self._cache_timestamps)
    
    def _clear_cache_for_config(self, config_name: str) -> None:
        """清除特定配置的缓存
        
        Args:
            config_name: 配置名称
        """
        self._config_cache.pop(config_name, None)
        self._cache_timestamps.pop(config_name, None)
        self._model_cache.pop(config_name, None)
        self._model_cache_timestamps.pop(config_name, None)
    
    def _clear_all_caches(self) -> None:
        """清除所有缓存"""
        self._config_cache.clear()
        self._cache_timestamps.clear()
        self._model_cache.clear()
        self._model_cache_timestamps.clear()
    
    def _preload_common_configs(self) -> None:
        """预加载常用配置
        
        子类可以重写此方法以预加载常用配置。
        """
        pass
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return {
            "config_cache_size": len(self._config_cache),
            "model_cache_size": len(self._model_cache),
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cached_configs": list(self._config_cache.keys())
        }
    
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