"""配置加载器

处理配置文件加载和继承逻辑。
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .interfaces import IConfigLoader
from ..utils.dict_merger import IDictMerger
from .interfaces import IConfigInheritanceHandler


class ConfigLoader(IConfigInheritanceHandler):
    """配置加载器 - 处理文件加载和继承逻辑"""
    
    def __init__(self, yaml_loader: IConfigLoader, merger: IDictMerger):
        """初始化配置加载器
        
        Args:
            yaml_loader: YAML配置加载器
            merger: 配置合并器
        """
        self._yaml_loader = yaml_loader
        self._merger = merger
        self._base_path = yaml_loader.base_path
    
    def load_with_inheritance(self, config_type: str, name: str) -> Dict[str, Any]:
        """加载配置并处理继承关系
        
        Args:
            config_type: 配置类型
            name: 配置名称
            
        Returns:
            配置字典
        """
        # 检查是否为provider目录下的LLM配置
        if config_type == "llms":
            provider_config = self._try_load_provider_config(name)
            if provider_config:
                return provider_config

        # 加载个体配置
        individual_path = self.get_config_path(config_type, name)
        individual_config: Dict[str, Any] = self._yaml_loader.load(individual_path)

        # 检查是否有组配置
        if "group" in individual_config:
            group_name = individual_config["group"]
            group_path = f"{config_type}/_group.yaml"

            try:
                group_configs = self._yaml_loader.load(group_path)

                if group_name in group_configs:
                    group_config = group_configs[group_name]
                    # 合并组配置和个体配置
                    merged_config = self._merger.merge_group_config(
                        group_config, individual_config
                    )
                    # 重新添加group字段，因为在合并过程中它被移除了
                    merged_config["group"] = group_name
                    return merged_config
            except Exception as e:
                # 如果加载组配置失败，记录警告但继续使用个体配置
                print(f"警告: 加载组配置失败 {group_path}: {e}")

        return individual_config
    
    def resolve_inheritance(self, config: Dict[str, Any], base_path: Optional[Path] = None) -> Dict[str, Any]:
        """解析配置继承关系
        
        Args:
            config: 原始配置
            base_path: 基础路径
            
        Returns:
            解析后的配置
        """
        # 这个方法是为了实现IConfigInheritanceHandler接口
        # 实际的继承逻辑在load_with_inheritance中处理
        return config
    
    def validate_config(self, config: Dict[str, Any], schema: Optional[object] = None) -> list[str]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        # 这个方法是为了实现IConfigInheritanceHandler接口
        # 实际的验证逻辑在ConfigSystem中处理
        return []
    
    def _try_load_provider_config(self, name: str) -> Optional[Dict[str, Any]]:
        """尝试加载provider-based配置
        
        Args:
            name: 配置名称
            
        Returns:
            配置字典，如果不是provider配置则返回None
        """
        # 检查是否存在provider目录下的配置
        provider_paths = [
            f"llms/provider/openai/{name}.yaml",
            f"llms/provider/anthropic/{name}.yaml", 
            f"llms/provider/gemini/{name}.yaml"
        ]
        
        for provider_path in provider_paths:
            try:
                individual_config = self._yaml_loader.load(provider_path)
                
                # 获取provider类型
                provider_type = individual_config.get("provider")
                if not provider_type:
                    # 从路径推断provider类型
                    if "openai" in provider_path:
                        provider_type = "openai"
                    elif "anthropic" in provider_path:
                        provider_type = "anthropic"
                    elif "gemini" in provider_path:
                        provider_type = "gemini"
                
                if provider_type:
                    # 加载provider的common配置
                    common_config_path = f"llms/provider/{provider_type}/common.yaml"
                    try:
                        common_config = self._yaml_loader.load(common_config_path)
                        
                        # 合并provider common配置和个体配置
                        merged_config = self._merge_provider_config(
                            common_config, individual_config, provider_type
                        )
                        
                        # 检查是否还有组配置需要继承
                        if "group" in merged_config:
                            group_name = merged_config["group"]
                            group_path = "llms/_group.yaml"
                            
                            try:
                                group_configs = self._yaml_loader.load(group_path)
                                if group_name in group_configs:
                                    group_config = group_configs[group_name]
                                    # 合并组配置
                                    merged_config = self._merger.merge_group_config(
                                        group_config, merged_config
                                    )
                                    # 重新添加group字段
                                    merged_config["group"] = group_name
                            except Exception as e:
                                print(f"警告: 加载组配置失败 {group_path}: {e}")
                        
                        return merged_config
                        
                    except Exception as e:
                        print(f"警告: 加载provider common配置失败 {common_config_path}: {e}")
                        # 如果common配置加载失败，返回个体配置
                        return individual_config
                        
            except Exception:
                # 如果provider配置不存在，继续尝试下一个
                continue
        
        # 如果没有找到provider配置，返回None
        return None
    
    def _merge_provider_config(
        self, 
        common_config: Dict[str, Any], 
        individual_config: Dict[str, Any],
        provider_type: str
    ) -> Dict[str, Any]:
        """合并provider common配置和个体配置
        
        Args:
            common_config: provider common配置
            individual_config: 个体配置
            provider_type: provider类型
            
        Returns:
            合并后的配置
        """
        
        # 从common配置中提取默认参数
        default_parameters = common_config.get("default_parameters", {})
        cache_config = common_config.get("cache_config", {})
        fallback_config = common_config.get("fallback_config", {})
        
        # 创建合并后的配置
        merged = {
            # 基础配置从个体配置获取
            "model_type": individual_config.get("model_type", provider_type),
            "model_name": individual_config.get("model_name"),
            "base_url": individual_config.get("base_url", common_config.get("base_url")),
            "api_key": individual_config.get("api_key"),
            "headers": individual_config.get("headers", common_config.get("headers", {})),
            "provider": individual_config.get("provider", provider_type),
            "token_counter": individual_config.get("token_counter"),
            
            # 参数配置：合并默认参数和个体参数
            "parameters": self._merger.deep_merge(
                default_parameters, 
                individual_config.get("parameters", {})
            ),
            
            # 缓存配置：合并默认缓存配置和个体缓存配置
            "supports_caching": individual_config.get(
                "supports_caching", 
                common_config.get("supports_caching", False)
            ),
            "cache_config": self._merger.deep_merge(
                cache_config,
                individual_config.get("cache_config", {})
            ),
            
            # 其他配置
            "group": individual_config.get("group"),
            "fallback_enabled": individual_config.get(
                "fallback_enabled",
                fallback_config.get("enabled", True)
            ),
            "fallback_models": individual_config.get("fallback_models", []),
            "max_fallback_attempts": individual_config.get(
                "max_fallback_attempts",
                fallback_config.get("max_attempts", 3)
            ),
            
            # 元数据合并
            "metadata": self._merger.deep_merge(
                common_config.get("metadata", {}),
                individual_config.get("metadata", {})
            )
        }
        
        # 移除None值
        merged = {k: v for k, v in merged.items() if v is not None}
        
        return merged
    
    def get_config_path(self, config_type: str, name: str) -> str:
        """获取配置路径
        
        Args:
            config_type: 配置类型
            name: 配置名称
            
        Returns:
            配置路径
        """
        return f"{config_type}/{name}.yaml"