"""LLM配置实现

提供LLM模块的配置加载、转换和管理功能。
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import yaml
from dataclasses import dataclass

from .base_impl import BaseConfigImpl
from .base_impl import IConfigSchema, ConfigProcessorChain

from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class ProviderInfo:
    """Provider信息"""
    name: str
    config_files: List[str]
    common_config_path: str
    enabled: bool = True
    models: Optional[List[str]] = None
    
    def __post_init__(self) -> None:
        if self.models is None:
            self.models = []


class LLMConfigImpl(BaseConfigImpl):
    """LLM配置实现类
    
    负责LLM模块的配置加载、转换和管理。
    支持多种LLM提供商的配置：OpenAI、Gemini、Anthropic、Mock等。
    """
    
    def __init__(self, 
                 config_loader: 'IConfigLoader',
                 processor_chain: ConfigProcessorChain,
                 schema: IConfigSchema):
        """初始化LLM配置实现
        
        Args:
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        super().__init__("llm", config_loader, processor_chain, schema)
        
        # Provider管理相关
        self._providers_cache: Optional[Dict[str, ProviderInfo]] = None
        self._supported_extensions = {'.yaml', '.yml', '.json'}
        
        # LLM特定的配置映射
        self._model_type_mapping = {
            "openai": "openai",
            "gpt": "openai",
            "chatgpt": "openai",
            "gemini": "gemini",
            "anthropic": "anthropic",
            "claude": "anthropic",
            "mock": "mock",
            "human_relay": "human_relay",
            "human-relay": "human_relay",
            "human-relay-s": "human_relay",
            "human-relay-m": "human_relay"
        }
        
        # 支持的模型类型
        self._supported_model_types = {
            "openai", "gemini", "anthropic", "mock", "human_relay"
        }
        
        logger.debug("LLM配置实现初始化完成")
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换LLM配置
        
        将原始配置转换为标准化的LLM配置格式。
        只保留模块特定的逻辑，通用处理由处理器链完成。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        logger.debug("开始转换LLM配置")
        
        # 1. 标准化模型类型（模块特定）
        config = self._normalize_model_type(config)
        
        # 2. 处理客户端配置（模块特定）
        config = self._process_client_configs(config)
        
        # 3. 处理模块配置（模块特定）
        config = self._process_module_config(config)
        
        # 注意：默认值设置、验证等通用处理已由处理器链完成
        
        logger.debug("LLM配置转换完成")
        return config
    
    def _normalize_model_type(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化模型类型
        
        Args:
            config: 配置数据
            
        Returns:
            标准化后的配置数据
        """
        # 处理客户端配置中的模型类型
        if "clients" in config:
            for client_name, client_config in config["clients"].items():
                if "model_type" in client_config:
                    model_type = client_config["model_type"].lower()
                    normalized_type = self._model_type_mapping.get(model_type, model_type)
                    client_config["model_type"] = normalized_type
                    
                    # 验证模型类型是否支持
                    if normalized_type not in self._supported_model_types:
                        logger.warning(f"不支持的模型类型: {normalized_type}")
        
        return config
    
    def _process_client_configs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理客户端配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "clients" not in config:
            config["clients"] = {}
        
        # 确保每个客户端配置都有必要的字段
        for client_name, client_config in config["clients"].items():
            # 设置默认值
            client_config.setdefault("timeout", 30)
            client_config.setdefault("max_retries", 3)
            client_config.setdefault("temperature", 0.7)
            client_config.setdefault("top_p", 1.0)
            client_config.setdefault("stream", False)
            client_config.setdefault("fallback_enabled", True)
            client_config.setdefault("fallback_models", [])
            client_config.setdefault("max_fallback_attempts", 3)
            
            # 处理连接池配置
            if "connection_pool_config" not in client_config:
                client_config["connection_pool_config"] = {
                    "max_connections": 10,
                    "max_keepalive": 10,
                    "connection_timeout": 30.0,
                    "read_timeout": 30.0,
                    "write_timeout": 30.0,
                    "connect_retries": 3,
                    "pool_timeout": 30.0
                }
            
            # 处理元数据配置
            if "metadata_config" not in client_config:
                client_config["metadata_config"] = {}
        
        return config
    
    def _process_module_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理模块配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "module" not in config:
            config["module"] = {}
        
        module_config = config["module"]
        
        # 设置默认值
        module_config.setdefault("default_model", "openai-gpt4")
        module_config.setdefault("default_timeout", 30)
        module_config.setdefault("default_max_retries", 3)
        module_config.setdefault("cache_enabled", True)
        module_config.setdefault("cache_ttl", 3600)
        module_config.setdefault("cache_max_size", 100)
        module_config.setdefault("hooks_enabled", True)
        module_config.setdefault("log_requests", True)
        module_config.setdefault("log_responses", True)
        module_config.setdefault("log_errors", True)
        module_config.setdefault("fallback_enabled", True)
        module_config.setdefault("global_fallback_models", [])
        module_config.setdefault("max_concurrent_requests", 10)
        module_config.setdefault("request_queue_size", 100)
        module_config.setdefault("metrics_enabled", True)
        module_config.setdefault("performance_tracking", True)
        module_config.setdefault("connection_pool_enabled", True)
        module_config.setdefault("default_max_connections", 10)
        module_config.setdefault("default_max_keepalive", 10)
        module_config.setdefault("default_connection_timeout", 30.0)
        
        return config
    
    
    
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
        provider_dir = self._base_path / "provider"
        
        if not provider_dir.exists():
            logger.warning(f"Provider配置目录不存在: {provider_dir}")
            return providers
        
        # 扫描provider目录下的子目录
        for provider_path in provider_dir.iterdir():
            if not provider_path.is_dir():
                continue
                
            provider_name = provider_path.name
            provider_info = self._scan_provider_directory(provider_name, provider_path)
            
            if provider_info:
                providers[provider_name] = provider_info
                logger.debug(f"发现Provider: {provider_name}, 配置文件: {len(provider_info.config_files)}")
        
        self._providers_cache = providers
        logger.info(f"发现 {len(providers)} 个Provider配置")
        
        return providers
    
    def get_provider_config(self, provider_name: str, model_name: str) -> Optional[Dict[str, Any]]:
        """获取Provider配置
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称
            
        Returns:
            Provider配置，如果不存在则返回None
        """
        providers = self.discover_providers()
        
        if provider_name not in providers:
            logger.warning(f"未找到Provider: {provider_name}")
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
            logger.warning(f"Provider {provider_name} 中未找到模型 {model_name} 的配置")
            return None
        
        try:
            # 加载配置文件
            model_config = self._load_config_file(Path(model_config_path))
            common_config = self._load_config_file(Path(provider_info.common_config_path))
            
            # 合并配置（模型配置覆盖common配置）
            merged_config = self._merge_configs(common_config, model_config)
            
            # 添加Provider元信息
            merged_config["_provider_meta"] = {
                "provider_name": provider_name,
                "model_name": model_name,
                "common_config_path": provider_info.common_config_path,
                "model_config_path": model_config_path
            }
            
            logger.debug(f"成功加载Provider配置: {provider_name}/{model_name}")
            return merged_config
            
        except Exception as e:
            logger.error(f"加载Provider配置失败 {provider_name}/{model_name}: {e}")
            return None
    
    def list_provider_models(self, provider_name: str) -> List[str]:
        """列出Provider的所有模型
        
        Args:
            provider_name: Provider名称
            
        Returns:
            模型名称列表
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
    
    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """获取Provider信息
        
        Args:
            provider_name: Provider名称
            
        Returns:
            Provider信息，如果不存在则返回None
        """
        providers = self.discover_providers()
        provider_info = providers.get(provider_name)
        if provider_info:
            return {
                "name": provider_info.name,
                "config_files": provider_info.config_files,
                "common_config_path": provider_info.common_config_path,
                "enabled": provider_info.enabled,
                "models": provider_info.models
            }
        return None
    
    def is_provider_available(self, provider_name: str) -> bool:
        """检查Provider是否可用
        
        Args:
            provider_name: Provider名称
            
        Returns:
            是否可用
        """
        provider_info = self.get_provider_info(provider_name)
        return provider_info is not None and provider_info.get("enabled", False)
    
    def enable_provider(self, provider_name: str) -> bool:
        """启用Provider
        
        Args:
            provider_name: Provider名称
            
        Returns:
            是否成功启用
        """
        if self._providers_cache is None:
            self.discover_providers()
        
        if self._providers_cache and provider_name in self._providers_cache:
            self._providers_cache[provider_name].enabled = True
            logger.info(f"已启用Provider: {provider_name}")
            return True
        
        return False
    
    def disable_provider(self, provider_name: str) -> bool:
        """禁用Provider
        
        Args:
            provider_name: Provider名称
            
        Returns:
            是否成功禁用
        """
        if self._providers_cache is None:
            self.discover_providers()
        
        if self._providers_cache and provider_name in self._providers_cache:
            self._providers_cache[provider_name].enabled = False
            logger.info(f"已禁用Provider: {provider_name}")
            return True
        
        return False
    
    def get_config_hierarchy(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取配置层次结构
        
        Returns:
            配置层次结构
        """
        hierarchy: Dict[str, List[Dict[str, Any]]] = {
            "global": [],
            "provider": [],
            "model": [],
            "tools": [],
            "other": []
        }
        
        if not self._base_path.exists():
            return hierarchy
        
        # 遍历配置目录
        for config_file in self._base_path.rglob("*"):
            if config_file.suffix.lower() in self._supported_extensions and config_file.is_file():
                try:
                    config_info = {
                        "path": str(config_file.relative_to(self._base_path)),
                        "name": config_file.stem,
                        "size": config_file.stat().st_size
                    }
                    
                    # 确定配置类型
                    path_parts = config_file.relative_to(self._base_path).parts
                    
                    if len(path_parts) == 1 and path_parts[0].startswith("global"):
                        hierarchy["global"].append(config_info)
                    elif len(path_parts) == 2 and path_parts[0] == "provider":
                        hierarchy["provider"].append(config_info)
                    elif len(path_parts) == 3 and path_parts[0] == "provider":
                        hierarchy["model"].append(config_info)
                    elif "tools" in path_parts:
                        hierarchy["tools"].append(config_info)
                    else:
                        hierarchy["other"].append(config_info)
                        
                except Exception as e:
                    logger.warning(f"处理配置文件失败 {config_file}: {e}")
                    continue
        
        return hierarchy
    
    def get_client_config(self, model_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """获取客户端配置
        
        Args:
            model_name: 模型名称
            use_cache: 是否使用缓存
            
        Returns:
            客户端配置，如果不存在则返回None
        """
        # 检查缓存
        cache_key = f"client_config:{model_name}"
        if use_cache:
            cached_config = self.cache_manager.get(cache_key)
            if cached_config is not None:
                logger.debug(f"从缓存获取客户端配置: {model_name}")
                return cached_config  # type: ignore
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        
        # 查找匹配的客户端配置
        client_config = None
        for client_name, config_data in config.get("clients", {}).items():
            if config_data.get("model_name") == model_name:
                client_config = config_data.copy()
                break
        
        # 如果没有找到，尝试使用默认模型
        if client_config is None:
            default_model = config.get("module", {}).get("default_model")
            if default_model and default_model == model_name:
                # 返回第一个可用的配置
                clients = config.get("clients", {})
                if clients:
                    client_config = list(clients.values())[0].copy()
        
        # 缓存结果
        if client_config and use_cache:
            self.cache_manager.set(cache_key, client_config)
        
        return client_config or None
    
    def get_module_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """获取模块配置
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            模块配置
        """
        # 检查缓存
        cache_key = "module_config"
        if use_cache:
            cached_config = self.cache_manager.get(cache_key)
            if cached_config is not None:
                logger.debug("从缓存获取模块配置")
                return cached_config  # type: ignore
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        module_config = config.get("module", {})
        if not isinstance(module_config, dict):
            module_config = {}
        module_config = module_config.copy()
        
        # 缓存结果
        if use_cache:
            self.cache_manager.set(cache_key, module_config)
        
        return module_config
    
    def list_available_models(self, use_cache: bool = True) -> List[str]:
        """列出可用的模型
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            可用模型列表
        """
        # 检查缓存
        cache_key = "available_models"
        if use_cache:
            cached_models = self.cache_manager.get(cache_key)
            if cached_models is not None:
                logger.debug("从缓存获取可用模型列表")
                return cached_models  # type: ignore
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        models = []
        
        for client_config in config.get("clients", {}).values():
            model_name = client_config.get("model_name")
            if model_name:
                models.append(model_name)
        
        # 缓存结果
        if use_cache:
            self.cache_manager.set(cache_key, models)
        
        return models
    
    def get_models_by_type(self, model_type: str) -> List[str]:
        """根据类型获取模型列表
        
        Args:
            model_type: 模型类型
            
        Returns:
            指定类型的模型列表
        """
        config = self.get_config()
        models = []
        
        for client_config in config.get("clients", {}).values():
            if client_config.get("model_type") == model_type:
                model_name = client_config.get("model_name")
                if model_name:
                    models.append(model_name)
        
        return models
    
    def validate_client_config(self, model_name: str) -> bool:
        """验证客户端配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            配置是否有效
        """
        client_config = self.get_client_config(model_name)
        if not client_config:
            return False
        
        # 验证必要字段
        required_fields = ["model_type", "model_name"]
        for field in required_fields:
            if field not in client_config:
                return False
        
        # 验证模型类型
        model_type = client_config["model_type"]
        if model_type not in self._supported_model_types:
            return False
        
        return True
    
    def get_config_summary(self, use_cache: bool = True) -> Dict[str, Any]:
        """获取配置摘要
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            配置摘要信息
        """
        # 检查缓存
        cache_key = "config_summary"
        if use_cache:
            cached_summary = self.cache_manager.get(cache_key)
            if cached_summary is not None:
                logger.debug("从缓存获取配置摘要")
                return cached_summary  # type: ignore
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        
        summary = {
            "version": config.get("version", "unknown"),
            "total_clients": len(config.get("clients", {})),
            "model_types": {},
            "default_model": config.get("module", {}).get("default_model"),
            "cache_enabled": config.get("module", {}).get("cache_enabled", False),
            "fallback_enabled": config.get("module", {}).get("fallback_enabled", False)
        }
        
        # 统计模型类型
        for client_config in config.get("clients", {}).values():
            model_type = client_config.get("model_type", "unknown")
            summary["model_types"][model_type] = summary["model_types"].get(model_type, 0) + 1
        
        # 缓存结果
        if use_cache:
            self.cache_manager.set(cache_key, summary)
        
        return summary
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径，如果为None则清除所有相关缓存
        """
        if config_path:
            cache_key = f"llm:{config_path}"
            self.cache_manager.delete(cache_key)
        else:
            # 清除LLM相关的所有缓存
            cache_keys = [
                "module_config",
                "available_models",
                "config_summary"
            ]
            
            # 清除客户端配置缓存
            models = self.list_available_models(use_cache=False)
            for model in models:
                cache_keys.append(f"client_config:{model}")
            
            for key in cache_keys:
                self.cache_manager.delete(key)
            
            logger.debug("清除LLM模块所有缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return self.cache_manager.get_stats()
    
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
            models = []
            
            # 查找common配置文件
            for ext in self._supported_extensions:
                common_file = provider_path / f"common{ext}"
                if common_file.exists():
                    common_config_path = str(common_file.relative_to(self._base_path))
                    break
            
            if not common_config_path:
                logger.warning(f"Provider {provider_name} 缺少common配置文件")
                return None
            
            # 查找模型特定配置文件
            for config_file in provider_path.iterdir():
                if config_file.is_file() and config_file.suffix in self._supported_extensions:
                    # 跳过common配置文件，因为它已经单独处理
                    if config_file.stem == "common":
                        continue
                    
                    relative_path = str(config_file.relative_to(self._base_path))
                    config_files.append(relative_path)
                    models.append(config_file.stem)
            
            if not config_files:
                logger.warning(f"Provider {provider_name} 没有找到模型配置文件")
                return None
            
            return ProviderInfo(
                name=provider_name,
                config_files=config_files,
                common_config_path=common_config_path,
                enabled=True,
                models=models
            )
            
        except Exception as e:
            logger.error(f"扫描Provider目录失败 {provider_name}: {e}")
            return None
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            full_path = self._base_path / config_path
            with open(full_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_path}: {e}")
            return {}
    
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
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _process_llm_config_structure(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理LLM特定的配置结构
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        # 如果配置文件路径包含provider信息，需要特殊处理
        if "provider" in config_path:
            return self._process_provider_config(config, config_path)
        
        # 否则返回原始配置
        return config
    
    def _process_provider_config(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理Provider特定配置
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        # 解析配置路径，提取provider和模型信息
        path_parts = Path(config_path).relative_to(self._base_path).parts
        
        if len(path_parts) >= 3 and path_parts[0] == "provider":
            provider_name = path_parts[1]
            config_name = path_parts[2].split('.')[0]  # 去除扩展名
            
            # 添加provider和模型信息到配置中
            config["_provider_info"] = {
                "provider_name": provider_name,
                "config_name": config_name,
                "is_common": config_name == "common"
            }
            
            # 如果是common配置，添加provider标识
            if config_name == "common":
                config["provider"] = provider_name
            else:
                # 如果是模型特定配置，添加模型名称
                config["model"] = config_name
                config["provider"] = provider_name
        
        return config