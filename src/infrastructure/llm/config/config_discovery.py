"""配置发现器

自动发现和管理LLM客户端配置文件，支持多环境和配置继承。
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass

from src.services.logger.injection import get_logger
from src.infrastructure.common.utils.dict_merger import DictMerger


@dataclass
class ConfigLocation:
    """配置位置信息"""
    path: Path
    provider: Optional[str] = None
    model: Optional[str] = None


@dataclass
class ConfigInfo:
    """配置信息"""
    path: Path
    provider: str
    models: List[str]
    inherits_from: Optional[str] = None


@dataclass
class ProviderInfo:
    """Provider信息"""
    name: str
    config_files: List[str]
    common_config_path: str
    enabled: bool = True


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
        self._discovered_configs: List[ConfigInfo] = []
        self._providers_cache: Optional[Dict[str, ProviderInfo]] = None
        
        # 环境变量引用模式
        self.env_var_pattern = re.compile(r"^\$\{([^}:]+)(?::([^}]*))?\}$")
        
        # 支持的配置文件类型
        self.supported_extensions = {'.yaml', '.yml', '.json'}
        
        # 配置合并器
        self.config_merger = DictMerger()
        
        self.logger.info(f"初始化配置发现器，配置目录: {self.config_dir}")
    
    def discover_configs(self, provider: Optional[str] = None, force_refresh: bool = False) -> List[ConfigInfo]:
        """发现配置文件
        
        Args:
            provider: 提供商名称，如果为None则发现所有提供商的配置
            force_refresh: 是否强制刷新缓存
            
        Returns:
            List[ConfigInfo]: 配置信息列表
        """
        # 检查缓存
        if not force_refresh and self._discovered_configs and not provider:
            return self._discovered_configs
        
        configs: List[ConfigInfo] = []
        
        if not self.config_dir.exists():
            self.logger.warning(f"配置目录不存在: {self.config_dir}")
            return configs
        
        # 遍历配置目录
        for config_file in self.config_dir.rglob("*"):
            if config_file.suffix.lower() in self.supported_extensions:
                try:
                    config_info = self._parse_config_file(config_file, provider)
                    if config_info:
                        configs.append(config_info)
                except Exception as e:
                    self.logger.error(f"解析配置文件失败 {config_file}: {e}")
                    continue
        
        # 缓存结果
        if not provider:
            self._discovered_configs = configs
        
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
    
    def get_config_file(self, config_type: str, provider: Optional[str] = None, model: Optional[str] = None) -> Optional[ConfigLocation]:
        """获取配置文件位置
        
        Args:
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            Optional[ConfigLocation]: 配置位置信息
        """
        # 根据配置类型构造路径
        if config_type == "global":
            config_path = self.config_dir / "global.yaml"
        elif config_type == "provider" and provider:
            config_path = self.config_dir / "provider" / f"{provider}.yaml"
        elif config_type == "model" and provider and model:
            config_path = self.config_dir / "provider" / provider / f"{model}.yaml"
        else:
            return None
        
        if config_path.exists():
            return ConfigLocation(path=config_path, provider=provider, model=model)
        
        return None
    
    def load_config(self, config_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        return self._load_config_file(config_path)
    
    def get_config_hierarchy(self) -> Dict[str, List[ConfigInfo]]:
        """获取配置层次结构
        
        Returns:
            Dict[str, List[ConfigInfo]]: 按类型分组的配置信息
        """
        configs = self.discover_configs()
        hierarchy = {
            "global": [],
            "provider": [],
            "model": [],
            "tools": [],
            "other": []
        }
        
        for config in configs:
            path_parts = config.path.relative_to(self.config_dir).parts
            
            if len(path_parts) == 1 and path_parts[0].startswith("global"):
                hierarchy["global"].append(config)
            elif len(path_parts) == 2 and path_parts[0] == "provider":
                hierarchy["provider"].append(config)
            elif len(path_parts) == 3 and path_parts[0] == "provider":
                hierarchy["model"].append(config)
            elif "tools" in path_parts:
                hierarchy["tools"].append(config)
            else:
                hierarchy["other"].append(config)
        
        return hierarchy
    
    def validate_config_structure(self) -> Dict[str, List[str]]:
        """验证配置文件结构
        
        Returns:
            Dict[str, List[str]]: 验证结果，包含错误和警告信息
        """
        result = {
            "errors": [],
            "warnings": []
        }
        
        if not self.config_dir.exists():
            result["errors"].append(f"配置目录不存在: {self.config_dir}")
            return result
        
        # 检查必需的配置文件
        required_configs = [
            self.config_dir / "global.yaml",
            self.config_dir / "_group.yaml"
        ]
        
        for required_config in required_configs:
            if not required_config.exists():
                result["warnings"].append(f"推荐配置文件不存在: {required_config}")
        
        # 检查提供商配置目录
        provider_dir = self.config_dir / "provider"
        if provider_dir.exists():
            providers = [d.name for d in provider_dir.iterdir() if d.is_dir()]
            if not providers:
                result["warnings"].append("提供商配置目录存在但为空")
        else:
            result["warnings"].append("提供商配置目录不存在")
        
        return result
    
    # Provider 管理方法（从 Core 层迁移过来）
    def discover_providers(self, force_refresh: bool = False) -> Dict[str, ProviderInfo]:
        """发现所有可用的Provider
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            Dict[str, ProviderInfo]: Provider名称到Provider信息的映射
        """
        if self._providers_cache is not None and not force_refresh:
            return self._providers_cache
        
        providers: Dict[str, ProviderInfo] = {}
        provider_dir = self.config_dir / "provider"
        
        if not provider_dir.exists():
            self.logger.warning(f"Provider配置目录不存在: {provider_dir}")
            return providers
        
        # 扫描provider目录下的子目录
        for provider_path in provider_dir.iterdir():
            if not provider_path.is_dir():
                continue
                
            provider_name = provider_path.name
            provider_info = self._scan_provider_directory(provider_name, provider_path)
            
            if provider_info:
                providers[provider_name] = provider_info
                self.logger.debug(f"发现Provider: {provider_name}, 配置文件: {len(provider_info.config_files)}")
        
        self._providers_cache = providers
        self.logger.info(f"发现 {len(providers)} 个Provider配置")
        
        return providers
    
    def _scan_provider_directory(self, provider_name: str, provider_path: Path) -> Optional[ProviderInfo]:
        """扫描单个Provider目录
        
        Args:
            provider_name: Provider名称
            provider_path: Provider目录路径
            
        Returns:
            ProviderInfo: Provider信息，如果扫描失败返回None
        """
        try:
            config_files = []
            common_config_path = None
            
            # 查找common配置文件
            for ext in self.supported_extensions:
                common_file = provider_path / f"common{ext}"
                if common_file.exists():
                    common_config_path = str(common_file.relative_to(self.config_dir))
                    break
            
            if not common_config_path:
                self.logger.warning(f"Provider {provider_name} 缺少common配置文件")
                return None
            
            # 查找模型特定配置文件
            for config_file in provider_path.iterdir():
                if config_file.is_file() and config_file.suffix in self.supported_extensions:
                    # 跳过common配置文件，因为它已经单独处理
                    if config_file.stem == "common":
                        continue
                    
                    relative_path = str(config_file.relative_to(self.config_dir))
                    config_files.append(relative_path)
            
            if not config_files:
                self.logger.warning(f"Provider {provider_name} 没有找到模型配置文件")
                return None
            
            return ProviderInfo(
                name=provider_name,
                config_files=config_files,
                common_config_path=common_config_path,
                enabled=True
            )
            
        except Exception as e:
            self.logger.error(f"扫描Provider目录失败 {provider_name}: {e}")
            return None
    
    def get_provider_config(self, provider_name: str, model_name: str) -> Optional[Dict[str, Any]]:
        """获取特定Provider和模型的配置
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 配置数据，如果加载失败返回None
        """
        providers = self.discover_providers()
        
        if provider_name not in providers:
            self.logger.warning(f"未找到Provider: {provider_name}")
            return None
        
        provider_info = providers[provider_name]
        
        # 查找模型配置文件
        model_config_path = None
        for config_file in provider_info.config_files:
            config_file_name = Path(config_file).stem
            if config_file_name == model_name:
                model_config_path = config_file
                break
        
        if not model_config_path:
            self.logger.warning(f"Provider {provider_name} 中未找到模型 {model_name} 的配置")
            return None
        
        try:
            # 加载配置文件
            model_config = self._load_config_file(Path(model_config_path))
            common_config = self._load_config_file(Path(provider_info.common_config_path))
            
            # 使用DictMerger合并配置（模型配置覆盖common配置）
            merged_config = self.config_merger.deep_merge(common_config, model_config)
            
            # 添加Provider元信息
            merged_config["_provider_meta"] = {
                "provider_name": provider_name,
                "model_name": model_name,
                "common_config_path": provider_info.common_config_path,
                "model_config_path": model_config_path
            }
            
            self.logger.debug(f"成功加载Provider配置: {provider_name}/{model_name}")
            return merged_config
            
        except Exception as e:
            self.logger.error(f"加载Provider配置失败 {provider_name}/{model_name}: {e}")
            return None
    
    def list_provider_models(self, provider_name: str) -> List[str]:
        """列出指定Provider的所有模型
        
        Args:
            provider_name: Provider名称
            
        Returns:
            List[str]: 模型名称列表
        """
        providers = self.discover_providers()
        
        if provider_name not in providers:
            return []
        
        provider_info = providers[provider_name]
        models = []
        
        for config_file in provider_info.config_files:
            model_name = Path(config_file).stem
            models.append(model_name)
        
        return models
    
    def get_provider_info(self, provider_name: str) -> Optional[ProviderInfo]:
        """获取Provider信息
        
        Args:
            provider_name: Provider名称
            
        Returns:
            ProviderInfo: Provider信息，如果不存在返回None
        """
        providers = self.discover_providers()
        return providers.get(provider_name)
    
    def is_provider_available(self, provider_name: str) -> bool:
        """检查Provider是否可用
        
        Args:
            provider_name: Provider名称
            
        Returns:
            bool: 是否可用
        """
        provider_info = self.get_provider_info(provider_name)
        return provider_info is not None and provider_info.enabled
    
    def enable_provider(self, provider_name: str) -> bool:
        """启用Provider
        
        Args:
            provider_name: Provider名称
            
        Returns:
            bool: 是否成功启用
        """
        if self._providers_cache is None:
            self.discover_providers()
        
        if self._providers_cache and provider_name in self._providers_cache:
            self._providers_cache[provider_name].enabled = True
            self.logger.info(f"已启用Provider: {provider_name}")
            return True
        
        return False
    
    def disable_provider(self, provider_name: str) -> bool:
        """禁用Provider
        
        Args:
            provider_name: Provider名称
            
        Returns:
            bool: 是否成功禁用
        """
        if self._providers_cache is None:
            self.discover_providers()
        
        if self._providers_cache and provider_name in self._providers_cache:
            self._providers_cache[provider_name].enabled = False
            self.logger.info(f"已禁用Provider: {provider_name}")
            return True
        
        return False
    
    def refresh_providers_cache(self) -> None:
        """刷新Provider缓存"""
        self._providers_cache = None
        self.logger.debug("Provider配置缓存已清除")


# 全局配置发现器实例
_global_discovery: Optional[ConfigDiscovery] = None


def get_config_discovery(config_dir: Optional[Union[str, Path]] = None) -> ConfigDiscovery:
    """获取全局配置发现器实例
    
    Args:
        config_dir: 配置目录路径
        
    Returns:
        ConfigDiscovery: 配置发现器实例
    """
    global _global_discovery
    if _global_discovery is None:
        _global_discovery = ConfigDiscovery(config_dir)
    return _global_discovery