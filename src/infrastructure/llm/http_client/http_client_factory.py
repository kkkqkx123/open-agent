"""HTTP客户端工厂

负责创建和管理不同LLM提供商的HTTP客户端实例。
"""

from typing import Dict, Any, Optional, Type, Union
from pathlib import Path

from src.interfaces.llm.http_client import ILLMHttpClient
from src.infrastructure.llm.http_client.base_http_client import BaseHttpClient
from src.infrastructure.llm.http_client.openai_http_client import OpenAIHttpClient
from src.infrastructure.llm.http_client.gemini_http_client import GeminiHttpClient
from src.infrastructure.llm.http_client.anthropic_http_client import AnthropicHttpClient
from src.infrastructure.config.impl.llm_config_impl import LLMConfigImpl
from src.interfaces.dependency_injection import get_logger


class HttpClientFactory:
    """HTTP客户端工厂
    
    负责根据配置创建和管理不同LLM提供商的HTTP客户端实例。
    支持配置驱动的客户端创建和缓存管理。
    """
    
    # 支持的客户端类型映射
    _client_registry: Dict[str, Type[ILLMHttpClient]] = {
        "openai": OpenAIHttpClient,
        "gemini": GeminiHttpClient,
        "anthropic": AnthropicHttpClient,
    }
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """初始化HTTP客户端工厂
        
        Args:
            config_dir: 配置目录路径
        """
        self.logger = get_logger(__name__)
        # 使用新的配置系统
        from src.infrastructure.config.factory import ConfigFactory
        from src.infrastructure.config.schema.llm_schema import LLMSchema
        
        factory = ConfigFactory()
        if config_dir:
            factory.set_base_path(Path(config_dir))
        
        loader = factory.create_config_loader()
        processor_chain = factory.create_default_processor_chain()
        schema = LLMSchema()
        
        self.config_impl = LLMConfigImpl(loader, processor_chain, schema)
        self._client_cache: Dict[str, ILLMHttpClient] = {}
        
        self.logger.info("初始化HTTP客户端工厂")
    
    def create_client(
        self,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> ILLMHttpClient:
        """创建HTTP客户端
        
        Args:
            provider: 提供商名称
            model: 模型名称（可选）
            api_key: API密钥（可选，如果不提供则从配置中获取）
            **kwargs: 其他参数
            
        Returns:
            ILLMHttpClient: HTTP客户端实例
            
        Raises:
            ValueError: 不支持的提供商或配置错误
        """
        # 检查提供商是否支持
        if provider not in self._client_registry:
            raise ValueError(f"不支持的提供商: {provider}，支持的提供商: {list(self._client_registry.keys())}")
        
        # 生成缓存键
        cache_key = self._generate_cache_key(provider, model, api_key, kwargs)
        
        # 检查缓存
        if cache_key in self._client_cache:
            self.logger.debug(f"从缓存获取客户端: {provider}:{model}")
            return self._client_cache[cache_key]
        
        # 加载配置
        config = self._load_client_config(provider, model)
        
        # 合并参数
        merged_config = self._merge_config_with_params(config, api_key, **kwargs)
        
        # 验证配置
        self._validate_client_config(provider, merged_config)
        
        # 创建客户端
        client_class = self._client_registry[provider]
        client = self._create_client_instance(client_class, merged_config)
        
        # 缓存客户端
        self._client_cache[cache_key] = client
        
        self.logger.info(f"创建HTTP客户端: {provider}:{model}")
        return client
    
    def get_supported_providers(self) -> list[str]:
        """获取支持的提供商列表
        
        Returns:
            list[str]: 支持的提供商名称列表
        """
        return list(self._client_registry.keys())
    
    def register_provider(self, provider: str, client_class: Type[ILLMHttpClient]) -> None:
        """注册新的提供商
        
        Args:
            provider: 提供商名称
            client_class: 客户端类
        """
        if not issubclass(client_class, ILLMHttpClient):
            raise ValueError("客户端类必须实现ILLMHttpClient接口")
        
        self._client_registry[provider] = client_class
        self.logger.info(f"注册提供商: {provider}")
    
    def clear_cache(self) -> None:
        """清除客户端缓存
        
        关闭所有缓存的客户端连接。
        """
        import asyncio
        
        async def _close_clients() -> None:
            for client in self._client_cache.values():
                if hasattr(client, 'close'):
                    await client.close()
        
        # 运行异步关闭
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                asyncio.create_task(_close_clients())
            else:
                # 如果事件循环未运行，直接运行
                loop.run_until_complete(_close_clients())
        except Exception as e:
            self.logger.warning(f"关闭客户端连接时出错: {e}")
        
        self._client_cache.clear()
        self.logger.info("客户端缓存已清除")
    
    def reload_configs(self) -> None:
        """重新加载配置
        
        清除配置缓存并重新发现配置文件。
        """
        self.config_impl.invalidate_cache()
        self.logger.info("配置已重新加载")
    
    def _load_client_config(self, provider: str, model: Optional[str] = None) -> Dict[str, Any]:
        """加载客户端配置
        
        Args:
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        if model:
            return self.config_impl.get_provider_config(provider, model)
        else:
            # 如果没有指定模型，尝试获取提供商的通用配置
            config = self.config_impl.get_config()
            providers = config.get("providers", {})
            provider_config = providers.get(provider, {})
            return provider_config.get("common", {})
    
    def _merge_config_with_params(
        self,
        config: Dict[str, Any],
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """合并配置和参数
        
        Args:
            config: 基础配置
            api_key: API密钥
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        merged = config.copy()
        
        # 添加API密钥
        if api_key:
            merged["api_key"] = api_key
        
        # 合并其他参数
        merged.update(kwargs)
        
        return merged
    
    def _validate_client_config(self, provider: str, config: Dict[str, Any]) -> None:
        """验证客户端配置
        
        Args:
            provider: 提供商名称
            config: 配置数据
            
        Raises:
            ValueError: 配置验证失败
        """
        errors = []
        
        # 检查必需的API密钥
        if "api_key" not in config and "api_key" not in config.get("default_headers", {}):
            errors.append("缺少API密钥配置")
        
        # 检查基础URL（支持api_base_url别名）
        if "base_url" not in config and "api_base_url" not in config:
            errors.append("缺少基础URL配置")
        
        # 提供商特定验证
        if provider == "openai":
            self._validate_openai_config(config, errors)
        # 可以添加其他提供商的验证逻辑
        
        if errors:
            raise ValueError(f"配置验证失败: {'; '.join(errors)}")
    
    def _validate_openai_config(self, config: Dict[str, Any], errors: list[str]) -> None:
        """验证OpenAI特定配置
        
        Args:
            config: 配置数据
            errors: 错误列表
        """
        # 检查API版本
        if "api_version" in config:
            api_version = config["api_version"]
            if not isinstance(api_version, str) or not api_version.startswith("v"):
                errors.append("OpenAI API版本格式无效")
        
        # 检查组织ID（如果有）
        if "organization" in config:
            org = config["organization"]
            if not isinstance(org, str):
                errors.append("OpenAI组织ID必须是字符串")
    
    def _create_client_instance(
        self,
        client_class: Type[ILLMHttpClient],
        config: Dict[str, Any]
    ) -> ILLMHttpClient:
        """创建客户端实例
        
        Args:
            client_class: 客户端类
            config: 配置数据
            
        Returns:
            ILLMHttpClient: 客户端实例
        """
        try:
            # 提取构造函数参数
            init_params = self._extract_init_params(config)
            
            # 创建实例
            return client_class(**init_params)
            
        except Exception as e:
            self.logger.error(f"创建客户端实例失败: {e}")
            raise
    
    def _extract_init_params(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """提取客户端初始化参数
        
        Args:
            config: 配置数据
            
        Returns:
            Dict[str, Any]: 初始化参数
        """
        # 通用参数
        common_params = [
            "api_key", "base_url", "timeout", "max_retries", 
            "pool_connections", "retry_delay", "backoff_factor"
        ]
        
        # OpenAI特定参数
        openai_params = ["api_version", "organization", "api_format"]
        
        # 提取参数
        init_params = {}
        
        for param in common_params + openai_params:
            if param in config:
                init_params[param] = config[param]
        
        # 处理默认头部
        if "default_headers" in config:
            init_params["default_headers"] = config["default_headers"]
        
        return init_params
    
    def _generate_cache_key(
        self,
        provider: str,
        model: Optional[str],
        api_key: Optional[str],
        kwargs: Dict[str, Any]
    ) -> str:
        """生成缓存键
        
        Args:
            provider: 提供商名称
            model: 模型名称
            api_key: API密钥
            kwargs: 其他参数
            
        Returns:
            str: 缓存键
        """
        # 使用API密钥的前几位作为标识（避免完整密钥暴露）
        api_key_prefix = api_key[:8] if api_key else "no_key"
        
        # 创建参数字典的字符串表示（排除敏感信息）
        safe_kwargs = {k: v for k, v in kwargs.items() if k not in ["api_key"]}
        kwargs_str = str(sorted(safe_kwargs.items()))
        
        return f"{provider}:{model or 'default'}:{api_key_prefix}:{hash(kwargs_str)}"


# 全局工厂实例
_global_factory: Optional[HttpClientFactory] = None


def get_http_client_factory(config_dir: Optional[Union[str, Path]] = None) -> HttpClientFactory:
    """获取全局HTTP客户端工厂实例
    
    Args:
        config_dir: 配置目录路径
        
    Returns:
        HttpClientFactory: 工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = HttpClientFactory(config_dir)
    return _global_factory


def create_http_client(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> ILLMHttpClient:
    """创建HTTP客户端的便捷函数
    
    Args:
        provider: 提供商名称
        model: 模型名称
        api_key: API密钥
        **kwargs: 其他参数
        
    Returns:
        ILLMHttpClient: HTTP客户端实例
    """
    factory = get_http_client_factory()
    return factory.create_client(provider, model, api_key, **kwargs)