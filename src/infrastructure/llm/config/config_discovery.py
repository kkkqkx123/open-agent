"""配置发现器

自动发现和管理LLM客户端配置文件，支持多环境和配置继承。
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from src.services.logger import get_logger


@dataclass
class ConfigInfo:
    """配置信息"""
    path: Path
    provider: str
    models: List[str]
    inherits_from: Optional[str] = None


class ConfigDiscovery:
    """配置发现器
    
    负责自动发现、加载和管理LLM客户端配置文件。
    支持配置继承、环境变量注入和多环境配置。
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """初始化配置发现器
        
        Args:
            config_dir: 配置目录路径，默认为 "configs/llms"
        """
        if config_dir is None:
            config_dir = Path("configs/llms")
        elif isinstance(config_dir, str):
            config_dir = Path(config_dir)
            
        self.config_dir = config_dir
        self.logger = get_logger(__name__)
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._config_info_cache: Dict[str, ConfigInfo] = {}
        
        # 环境变量引用模式
        self.env_var_pattern = re.compile(r"^\$\{([^}:]+)(?::([^}]*))?\}$")
        
        self.logger.info(f"初始化配置发现器，配置目录: {self.config_dir}")
    
    def discover_configs(self, provider: Optional[str] = None) -> List[ConfigInfo]:
        """发现配置文件
        
        Args:
            provider: 提供商名称，如果为None则发现所有提供商的配置
            
        Returns:
            List[ConfigInfo]: 配置信息列表
        """
        configs: List[ConfigInfo] = []
        
        if not self.config_dir.exists():
            self.logger.warning(f"配置目录不存在: {self.config_dir}")
            return configs
        
        # 遍历配置目录
        for config_file in self.config_dir.rglob("*.yaml"):
            try:
                config_info = self._parse_config_file(config_file, provider)
                if config_info:
                    configs.append(config_info)
            except Exception as e:
                self.logger.error(f"解析配置文件失败 {config_file}: {e}")
                continue
        
        
        self.logger.debug(f"发现 {len(configs)} 个配置文件")
        return configs
    
    def load_provider_config(self, provider: str, model: str) -> Dict[str, Any]:
        """加载指定提供商和模型的配置
        
        Args:
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        cache_key = f"{provider}:{model}"
        
        # 检查缓存
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # 发现配置文件
        configs = self.discover_configs(provider)
        
        # 查找匹配的配置
        for config_info in configs:
            if self._matches_model(config_info, model):
                config = self._load_config_file(config_info.path)
                resolved_config = self._resolve_config(config)
                
                # 缓存结果
                self._config_cache[cache_key] = resolved_config
                self._config_info_cache[cache_key] = config_info
                
                self.logger.debug(f"加载配置: {config_info.path} for {provider}:{model}")
                return resolved_config
        
        # 返回默认配置
        default_config = self._get_default_config(provider)
        self._config_cache[cache_key] = default_config
        
        self.logger.warning(f"未找到匹配的配置，使用默认配置: {provider}:{model}")
        return default_config
    
    def get_all_models(self, provider: str) -> List[str]:
        """获取指定提供商的所有模型
        
        Args:
            provider: 提供商名称
            
        Returns:
            List[str]: 模型名称列表
        """
        configs = self.discover_configs(provider)
        models = []
        
        for config_info in configs:
            models.extend(config_info.models)
        
        # 去重并排序
        return sorted(list(set(models)))
    
    def reload_configs(self) -> None:
        """重新加载所有配置
        
        清除缓存并重新发现配置文件。
        """
        self._config_cache.clear()
        self._config_info_cache.clear()
        self.logger.info("配置缓存已清除")
    
    def _parse_config_file(self, config_file: Path, provider_filter: Optional[str] = None) -> Optional[ConfigInfo]:
        """解析配置文件
        
        Args:
            config_file: 配置文件路径
            provider_filter: 提供商过滤器
            
        Returns:
            Optional[ConfigInfo]: 配置信息或None
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return None
            
            # 提取提供商信息
            provider = self._extract_provider_from_path(config_file)
            if provider_filter and provider != provider_filter:
                return None
            
            # 提取模型信息
            models = self._extract_models_from_config(config)
            
            # 提取其他信息
            inherits_from = config.get("inherits_from")
            
            return ConfigInfo(
                path=config_file,
                provider=provider,
                models=models,
                inherits_from=inherits_from
            )
            
        except Exception as e:
            self.logger.error(f"解析配置文件失败 {config_file}: {e}")
            return None
    
    def _extract_provider_from_path(self, config_file: Path) -> str:
        """从文件路径提取提供商名称
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            str: 提供商名称
        """
        # 尝试从路径中提取提供商名称
        parts = config_file.relative_to(self.config_dir).parts
        
        # 如果路径包含provider目录
        if len(parts) >= 2 and parts[0] == "provider":
            return parts[1]
        
        # 从文件名提取
        filename = config_file.stem
        if "_" in filename:
            return filename.split("_")[0]
        
        return filename
    
    def _extract_models_from_config(self, config: Dict[str, Any]) -> List[str]:
        """从配置中提取模型列表
        
        Args:
            config: 配置数据
            
        Returns:
            List[str]: 模型名称列表
        """
        models = []
        
        # 直接的models字段
        if "models" in config:
            if isinstance(config["models"], list):
                models.extend(config["models"])
            elif isinstance(config["models"], str):
                models.append(config["models"])
        
        # model_pattern字段
        if "model_pattern" in config:
            # 这里可以添加正则匹配逻辑，暂时返回空列表
            pass
        
        # 单个model字段
        if "model" in config:
            models.append(config["model"])
        
        return models
    
    def _matches_model(self, config_info: ConfigInfo, model: str) -> bool:
        """检查配置是否匹配指定模型
        
        Args:
            config_info: 配置信息
            model: 模型名称
            
        Returns:
            bool: 是否匹配
        """
        # 直接匹配
        if model in config_info.models:
            return True
        
        # 如果没有指定模型，则认为是通用配置
        if not config_info.models:
            return True
        
        return False
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"加载配置文件失败 {config_path}: {e}")
            return {}
    
    def _resolve_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置，处理环境变量和继承
        
        Args:
            config: 原始配置
            
        Returns:
            Dict[str, Any]: 解析后的配置
        """
        resolved = config.copy()
        
        # 处理环境变量
        resolved = self._resolve_env_vars(resolved)
        
        # 处理继承
        if "inherits_from" in resolved:
            base_config = self._load_base_config(resolved["inherits_from"])
            resolved = self._merge_configs(base_config, resolved)
        
        return resolved
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """递归解析环境变量
        
        Args:
            obj: 要解析的对象
            
        Returns:
            Any: 解析后的对象
        """
        if isinstance(obj, str):
            return self._resolve_env_var(obj)
        elif isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        else:
            return obj
    
    def _resolve_env_var(self, value: str) -> str:
        """解析单个环境变量
        
        Args:
            value: 环境变量引用字符串
            
        Returns:
            str: 解析后的值
        """
        match = self.env_var_pattern.match(value.strip())
        if not match:
            return value
        
        env_var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""
        
        return os.getenv(env_var_name, default_value)
    
    def _load_base_config(self, inherits_from: str) -> Dict[str, Any]:
        """加载基础配置
        
        Args:
            inherits_from: 继承的配置名称
            
        Returns:
            Dict[str, Any]: 基础配置
        """
        base_config_path = self.config_dir / f"{inherits_from}.yaml"
        
        if not base_config_path.exists():
            self.logger.warning(f"基础配置文件不存在: {base_config_path}")
            return {}
        
        return self._load_config_file(base_config_path)
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        merged = base.copy()
        
        for key, value in override.items():
            if key == "inherits_from":
                continue  # 跳过继承字段
            
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _get_default_config(self, provider: str) -> Dict[str, Any]:
        """获取默认配置
        
        Args:
            provider: 提供商名称
            
        Returns:
            Dict[str, Any]: 默认配置
        """
        defaults = {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "timeout": 30,
                "max_retries": 3,
                "api_version": "v1",
                "pool_connections": 10
            },
            "gemini": {
                "base_url": "https://generativelanguage.googleapis.com/v1",
                "timeout": 30,
                "max_retries": 3,
                "pool_connections": 10
            },
            "anthropic": {
                "base_url": "https://api.anthropic.com",
                "timeout": 30,
                "max_retries": 3,
                "pool_connections": 10
            }
        }
        
        return defaults.get(provider, {})