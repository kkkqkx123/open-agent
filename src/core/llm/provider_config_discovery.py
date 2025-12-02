"""LLM Provider配置发现器

专门用于发现和加载configs/llms/provider目录下的配置文件。
重构版本：复用通用配置加载器，保留LLM特定的发现逻辑。
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

from src.services.logger import get_logger
from src.core.common.exceptions.config import ConfigNotFoundError, ConfigError
from src.core.config.config_loader import IConfigLoader
from src.core.common.utils.dict_merger import DictMerger

logger = get_logger(__name__)


@dataclass
class ProviderInfo:
    """Provider信息"""
    name: str
    config_files: List[str]
    common_config_path: str
    enabled: bool = True


class ProviderConfigDiscovery:
    """LLM Provider配置发现器
    
    负责：
    1. 扫描configs/llms/provider目录
    2. 发现可用的Provider配置
    3. 提供Provider配置加载接口
    4. 管理Provider配置的元数据
    
    重构说明：
    - 复用通用配置加载器进行文件I/O
    - 保留LLM特定的发现和合并逻辑
    - 使用配置合并适配器处理配置合并
    """
    
    def __init__(self, config_loader: IConfigLoader, base_config_path: str = "configs/llms"):
        """初始化Provider配置发现器
        
        Args:
            config_loader: 通用配置加载器
            base_config_path: LLM配置基础路径
        """
        self.config_loader = config_loader
        self.base_config_path = Path(base_config_path)
        self.provider_dir = self.base_config_path / "provider"
        self._providers_cache: Optional[Dict[str, ProviderInfo]] = None
        self._supported_formats = {'.yaml', '.yml', '.json'}
        self.config_merger = DictMerger()
        
        logger.debug(f"Provider配置发现器初始化完成，基础路径: {self.base_config_path}")
    
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
        
        if not self.provider_dir.exists():
            logger.warning(f"Provider配置目录不存在: {self.provider_dir}")
            return providers
        
        # 扫描provider目录下的子目录
        for provider_path in self.provider_dir.iterdir():
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
            for ext in self._supported_formats:
                common_file = provider_path / f"common{ext}"
                if common_file.exists():
                    common_config_path = str(common_file.relative_to(self.base_config_path))
                    break
            
            if not common_config_path:
                logger.warning(f"Provider {provider_name} 缺少common配置文件")
                return None
            
            # 查找模型特定配置文件
            for config_file in provider_path.iterdir():
                if config_file.is_file() and config_file.suffix in self._supported_formats:
                    # 跳过common配置文件，因为它已经单独处理
                    if config_file.stem == "common":
                        continue
                    
                    relative_path = str(config_file.relative_to(self.base_config_path))
                    config_files.append(relative_path)
            
            if not config_files:
                logger.warning(f"Provider {provider_name} 没有找到模型配置文件")
                return None
            
            return ProviderInfo(
                name=provider_name,
                config_files=config_files,
                common_config_path=common_config_path,
                enabled=True
            )
            
        except Exception as e:
            logger.error(f"扫描Provider目录失败 {provider_name}: {e}")
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
            # 使用通用配置加载器加载配置
            model_config = self.config_loader.load(model_config_path)
            common_config = self.config_loader.load(provider_info.common_config_path)
            
            # 使用DictMerger合并配置（模型配置覆盖common配置）
            merged_config = self.config_merger.deep_merge(common_config, model_config)
            
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
    
    def list_provider_models_legacy(self, provider_name: str) -> List[str]:
        """列出Provider下的所有模型（遗留方法）
        
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
    
    def list_all_models(self) -> Dict[str, List[str]]:
        """列出所有Provider下的所有模型
        
        Returns:
            Dict[str, List[str]]: Provider名称到模型名称列表的映射
        """
        providers = self.discover_providers()
        result = {}
        
        for provider_name, provider_info in providers.items():
            models = []
            for config_file in provider_info.config_files:
                model_name = Path(config_file).stem
                models.append(model_name)
            result[provider_name] = models
        
        return result
    
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
            logger.info(f"已启用Provider: {provider_name}")
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
            logger.info(f"已禁用Provider: {provider_name}")
            return True
        
        return False
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（override_config覆盖base_config）
        
        注意：此方法已弃用，请使用 config_merger.deep_merge()
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        logger.warning("_merge_configs方法已弃用，请使用config_merger.deep_merge()")
        return self.config_merger.deep_merge(base_config, override_config)
    
    def refresh_cache(self) -> None:
        """刷新缓存"""
        self._providers_cache = None
        logger.debug("Provider配置缓存已清除")
    
    def get_discovery_status(self) -> Dict[str, Any]:
        """获取发现状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        providers = self.discover_providers()
        
        total_models = sum(len(provider.config_files) for provider in providers.values())
        enabled_providers = sum(1 for provider in providers.values() if provider.enabled)
        
        return {
            "provider_directory_exists": self.provider_dir.exists(),
            "total_providers": len(providers),
            "enabled_providers": enabled_providers,
            "total_models": total_models,
            "config_loader_type": type(self.config_loader).__name__,
            "merger_adapter_type": type(self.config_merger).__name__,
            "providers": {
                name: {
                    "enabled": info.enabled,
                    "model_count": len(info.config_files),
                    "models": [Path(f).stem for f in info.config_files],
                    "common_config": info.common_config_path
                }
                for name, info in providers.items()
            }
        }
    
    def list_available_providers(self) -> List[str]:
        """列出所有可用的Provider
        
        Returns:
            List[str]: Provider名称列表
        """
        providers = self.discover_providers()
        return list(providers.keys())
    
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
    
    def validate_provider_config(self, provider_name: str, model_name: str) -> bool:
        """验证Provider配置是否有效
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称
            
        Returns:
            bool: 是否有效
        """
        try:
            config = self.get_provider_config(provider_name, model_name)
            return config is not None and "_provider_meta" in config
        except Exception as e:
            logger.error(f"验证Provider配置失败 {provider_name}/{model_name}: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息
        
        Returns:
            Dict[str, Any]: 摘要信息
        """
        providers = self.discover_providers()
        
        summary: Dict[str, Any] = {
            "total_providers": len(providers),
            "total_models": 0,
            "providers_by_type": {},
            "model_distribution": {}
        }
        
        for provider_name, provider_info in providers.items():
            model_count = len(provider_info.config_files)
            summary["total_models"] = summary["total_models"] + model_count
            
            # 按类型分组
            provider_type = provider_name  # 这里可以进一步解析provider类型
            if provider_type not in summary["providers_by_type"]:
                summary["providers_by_type"][provider_type] = 0
            summary["providers_by_type"][provider_type] = summary["providers_by_type"][provider_type] + 1
            
            # 模型分布
            summary["model_distribution"][provider_name] = model_count
        
        return summary