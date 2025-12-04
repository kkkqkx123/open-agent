"""LLM配置处理器 - 适配器模式

作为基础设施层配置系统的适配器，为核心层提供统一的配置接口。
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.common_infra import ILogger


class LLMConfigProcessor:
    """LLM配置处理器 - 适配器模式
    
    作为基础设施层配置系统的适配器，为核心层提供统一的配置接口。
    所有实际的配置处理逻辑都委托给基础设施层的ConfigLoader。
    """
    
    def __init__(self, base_config_path: str = "configs/llms", logger: Optional["ILogger"] = None):
        """初始化LLM配置处理器
        
        Args:
            base_config_path: LLM配置基础路径（保持向后兼容）
            logger: 日志记录器实例（可选）
        """
        self.base_config_path = base_config_path
        self.logger = logger
        
        # 使用 infrastructure 层的配置加载器
        from src.infrastructure.llm.config import get_config_loader
        self._config_loader = get_config_loader()
        
        if self.logger:
            self.logger.debug(f"LLM配置处理器初始化完成，基础路径: {self.base_config_path}")
    
    def process_config(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
            
        Note:
            此方法保持向后兼容，实际处理逻辑已在基础设施层完成。
        """
        if self.logger:
            self.logger.debug(f"处理LLM配置: {config_path}")
        
        # 基础设施层已经处理了继承、环境变量等，直接返回
        return config
    
    def load_config(self, config_type: str, provider: Optional[str] = None, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """加载配置
        
        Args:
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        return self._config_loader.load_config(config_type, provider, model)
    
    def load_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """加载提供商配置
        
        Args:
            provider: 提供商名称
            
        Returns:
            Optional[Dict[str, Any]]: 提供商配置数据
        """
        return self._config_loader.load_provider_config(provider)
    
    def load_model_config(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """加载模型配置
        
        Args:
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            Optional[Dict[str, Any]]: 模型配置数据
        """
        return self._config_loader.load_model_config(provider, model)
    
    def load_config_with_fallback(
        self,
        config_type: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        fallback_configs: Optional[list[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """加载配置，支持回退配置
        
        Args:
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            fallback_configs: 回退配置列表
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        from src.infrastructure.llm.config import LoadOptions
        options = LoadOptions(
            resolve_env_vars=True,
            resolve_inheritance=True,
            validate_schema=True,
            cache_enabled=True
        )
        
        return self._config_loader.load_config_with_fallback(
            config_type, provider, model, fallback_configs, options
        )
    
    def clear_cache(self) -> None:
        """清空配置缓存"""
        self._config_loader.clear_cache()
        if self.logger:
            self.logger.debug("LLM配置处理器缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return self._config_loader.get_cache_stats()


# 为了向后兼容，保留原有的类名作为别名
LLMInheritanceProcessor = LLMConfigProcessor
LLMConfigProcessorChain = LLMConfigProcessor