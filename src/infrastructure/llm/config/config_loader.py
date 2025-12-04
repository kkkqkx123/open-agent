"""
配置加载器

提供LLM配置文件的加载和解析功能。
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.services.logger import get_logger
from .config_discovery import ConfigDiscovery, get_config_discovery

logger = get_logger(__name__)


@dataclass
class LoadOptions:
    """配置加载选项"""
    
    resolve_env_vars: bool = True  # 是否解析环境变量
    resolve_inheritance: bool = True  # 是否解析继承关系
    validate_schema: bool = True  # 是否验证配置模式
    cache_enabled: bool = True  # 是否启用缓存


class ConfigLoader:
    """配置加载器
    
    负责加载和解析LLM配置文件，支持环境变量解析和配置继承。
    """
    
    def __init__(self, discovery: Optional[ConfigDiscovery] = None):
        """
        初始化配置加载器
        
        Args:
            discovery: 配置发现器实例
        """
        self.discovery = discovery or get_config_discovery()
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("配置加载器初始化完成")
    
    def load_config(
        self,
        config_type: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        options: Optional[LoadOptions] = None
    ) -> Optional[Dict[str, Any]]:
        """
        加载配置
        
        Args:
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            options: 加载选项
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        options = options or LoadOptions()
        
        # 生成缓存键
        cache_key = self._generate_cache_key(config_type, provider, model, options)
        
        # 检查缓存
        if options.cache_enabled and cache_key in self._config_cache:
            logger.debug(f"从缓存加载配置: {cache_key}")
            return self._config_cache[cache_key].copy()
        
        # 获取配置文件位置
        location = self.discovery.get_config_file(config_type, provider, model)
        if not location:
            logger.warning(f"未找到配置文件: {config_type}/{provider}/{model}")
            return None
        
        # 加载原始配置
        config_data = self.discovery.load_config(location.path)
        if not config_data:
            return None
        
        # 处理配置
        processed_config = self._process_config(config_data, options)
        
        # 缓存配置
        if options.cache_enabled:
            self._config_cache[cache_key] = processed_config.copy()
        
        logger.debug(f"加载配置成功: {location.path.name}")
        return processed_config
    
    def load_provider_config(self, provider: str, options: Optional[LoadOptions] = None) -> Optional[Dict[str, Any]]:
        """
        加载提供商配置
        
        Args:
            provider: 提供商名称
            options: 加载选项
            
        Returns:
            Optional[Dict[str, Any]]: 提供商配置数据
        """
        return self.load_config("provider", provider=provider, options=options)
    
    def load_model_config(self, provider: str, model: str, options: Optional[LoadOptions] = None) -> Optional[Dict[str, Any]]:
        """
        加载模型配置
        
        Args:
            provider: 提供商名称
            model: 模型名称
            options: 加载选项
            
        Returns:
            Optional[Dict[str, Any]]: 模型配置数据
        """
        return self.load_config("model", provider=provider, model=model, options=options)
    
    def load_global_config(self, options: Optional[LoadOptions] = None) -> Optional[Dict[str, Any]]:
        """
        加载全局配置
        
        Args:
            options: 加载选项
            
        Returns:
            Optional[Dict[str, Any]]: 全局配置数据
        """
        return self.load_config("global", options=options)
    
    def _process_config(self, config_data: Dict[str, Any], options: LoadOptions) -> Dict[str, Any]:
        """
        处理配置数据
        
        Args:
            config_data: 原始配置数据
            options: 处理选项
            
        Returns:
            Dict[str, Any]: 处理后的配置数据
        """
        processed_config = config_data.copy()
        
        # 解析环境变量
        if options.resolve_env_vars:
            processed_config = self._resolve_environment_variables(processed_config)
        
        # 解析继承关系
        if options.resolve_inheritance:
            processed_config = self._resolve_inheritance(processed_config)
        
        # 验证配置模式
        if options.validate_schema:
            self._validate_config_schema(processed_config)
        
        return processed_config
    
    def _resolve_environment_variables(self, config_data: Any) -> Any:
        """
        解析环境变量
        
        Args:
            config_data: 配置数据
            
        Returns:
            Any: 解析后的配置数据
        """
        if isinstance(config_data, dict):
            resolved_config = {}
            for key, value in config_data.items():
                resolved_config[key] = self._resolve_environment_variables(value)
            return resolved_config
        elif isinstance(config_data, list):
            return [self._resolve_environment_variables(item) for item in config_data]
        elif isinstance(config_data, str):
            return self._substitute_env_vars(config_data)
        else:
            return config_data
    
    def _substitute_env_vars(self, text: str) -> str:
        """
        替换字符串中的环境变量
        
        Args:
            text: 包含环境变量的字符串
            
        Returns:
            str: 替换后的字符串
        """
        # 匹配 ${VAR:default} 格式
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_expr = match.group(1)
            
            # 分离变量名和默认值
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
            else:
                var_name, default_value = var_expr, ''
            
            # 获取环境变量值
            env_value = os.getenv(var_name.strip())
            
            return env_value if env_value is not None else default_value
        
        return re.sub(pattern, replace_var, text)
    
    def _resolve_inheritance(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析配置继承关系
        
        Args:
            config_data: 配置数据
            
        Returns:
            Dict[str, Any]: 解析继承后的配置数据
        """
        if "inherits_from" not in config_data:
            return config_data
        
        inherits_from = config_data["inherits_from"]
        if not isinstance(inherits_from, str):
            logger.warning("inherits_from 必须是字符串")
            return config_data
        
        # 移除继承字段，避免循环
        config_data = config_data.copy()
        del config_data["inherits_from"]
        
        # 加载父配置
        parent_config = self._load_parent_config(inherits_from)
        if not parent_config:
            logger.warning(f"无法加载父配置: {inherits_from}")
            return config_data
        
        # 合并配置（子配置覆盖父配置）
        merged_config = self._merge_configs(parent_config, config_data)
        
        return merged_config
    
    def _load_parent_config(self, inherits_from: str) -> Optional[Dict[str, Any]]:
        """
        加载父配置
        
        Args:
            inherits_from: 继承路径
            
        Returns:
            Optional[Dict[str, Any]]: 父配置数据
        """
        # 解析继承路径格式: "provider:config_name" 或 "config_name"
        if ':' in inherits_from:
            provider, config_name = inherits_from.split(':', 1)
            return self.load_provider_config(provider)
        else:
            # 加载全局配置
            return self.load_global_config()
    
    def _merge_configs(self, parent_config: Dict[str, Any], child_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并配置
        
        Args:
            parent_config: 父配置
            child_config: 子配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        merged_config = parent_config.copy()
        
        for key, value in child_config.items():
            if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                # 递归合并字典
                merged_config[key] = self._merge_configs(merged_config[key], value)
            else:
                # 子配置覆盖父配置
                merged_config[key] = value
        
        return merged_config
    
    def _validate_config_schema(self, config_data: Dict[str, Any]) -> None:
        """
        验证配置模式
        
        Args:
            config_data: 配置数据
        """
        # 基础验证
        if not isinstance(config_data, dict):
            raise ValueError("配置必须是字典类型")
        
        # 可以在这里添加更多的验证逻辑
        # 例如验证必需字段、数据类型等
    
    def _generate_cache_key(
        self,
        config_type: str,
        provider: Optional[str],
        model: Optional[str],
        options: LoadOptions
    ) -> str:
        """
        生成缓存键
        
        Args:
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            options: 加载选项
            
        Returns:
            str: 缓存键
        """
        key_parts = [
            config_type,
            provider or "",
            model or "",
            str(options.resolve_env_vars),
            str(options.resolve_inheritance),
            str(options.validate_schema)
        ]
        
        return "|".join(key_parts)
    
    def clear_cache(self) -> None:
        """清空配置缓存"""
        self._config_cache.clear()
        logger.info("配置加载器缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return {
            "cached_configs": len(self._config_cache),
            "cache_keys": list(self._config_cache.keys())
        }
    
    def load_config_with_fallback(
        self,
        config_type: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        fallback_configs: Optional[List[str]] = None,
        options: Optional[LoadOptions] = None
    ) -> Optional[Dict[str, Any]]:
        """
        加载配置，支持回退配置
        
        Args:
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            fallback_configs: 回退配置列表
            options: 加载选项
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        # 尝试加载主配置
        config = self.load_config(config_type, provider, model, options)
        if config:
            return config
        
        # 尝试加载回退配置
        if fallback_configs:
            for fallback_path in fallback_configs:
                logger.debug(f"尝试加载回退配置: {fallback_path}")
                
                # 解析回退路径
                if ':' in fallback_path:
                    fb_provider, fb_config = fallback_path.split(':', 1)
                    fb_config = self.load_config(fb_config, provider=fb_provider, options=options)
                else:
                    fb_config = self.load_config(fallback_path, options=options)
                
                if fb_config:
                    logger.info(f"使用回退配置: {fallback_path}")
                    return fb_config
        
        logger.warning(f"所有配置加载失败: {config_type}/{provider}/{model}")
        return None


# 全局配置加载器实例
_global_loader: Optional[ConfigLoader] = None


def get_config_loader(discovery: Optional[ConfigDiscovery] = None) -> ConfigLoader:
    """
    获取全局配置加载器实例
    
    Args:
        discovery: 配置发现器实例
        
    Returns:
        ConfigLoader: 配置加载器实例
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = ConfigLoader(discovery)
    return _global_loader