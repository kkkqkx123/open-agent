"""LLM客户端工厂实现 - 新配置系统版本

使用新的集中配置系统，专注于业务逻辑包装。
"""

from typing import Dict, Any, Optional, Type, cast
from threading import RLock

from src.interfaces.llm import ILLMClient, ILLMClientFactory
from src.interfaces.llm.exceptions import LLMClientCreationError, UnsupportedModelTypeError
from src.infrastructure.config import get_global_registry
from src.infrastructure.config.impl.llm_config_impl import LLMConfigImpl


class LLMFactoryNew(ILLMClientFactory):
    """LLM客户端工厂实现 - 新配置系统版本
    
    使用新的集中配置系统，专注于业务逻辑包装。
    """

    def __init__(self, config_impl_name: str = "llm") -> None:
        """
        初始化工厂

        Args:
            config_impl_name: 配置实现名称
        """
        # 获取配置实现
        self.config_registry = get_global_registry()
        impl = self.config_registry.get_implementation(config_impl_name)
        
        if not impl:
            raise ValueError(f"配置实现 '{config_impl_name}' 未找到")
        
        # 确保是LLMConfigImpl实例
        if not isinstance(impl, LLMConfigImpl):
            raise TypeError(f"配置实现必须是LLMConfigImpl实例，但得到 {type(impl)}")
        
        self.config_impl: LLMConfigImpl = impl
        
        self._client_cache: Dict[str, ILLMClient] = {}
        self._client_types: Dict[str, Type[ILLMClient]] = {}
        self._lock = RLock()

        # 使用基础设施层的HTTP客户端工厂
        from src.infrastructure.llm.http_client.http_client_factory import get_http_client_factory
        self._http_factory = get_http_client_factory()

        # 注册默认客户端类型
        self._register_default_clients()

    def _register_default_clients(self) -> None:
        """注册默认客户端类型"""
        # 延迟导入避免循环依赖
        try:
            from .clients.openai.openai_client import OpenAIClient

            self._client_types["openai"] = OpenAIClient
            # 注册siliconflow为OpenAI兼容客户端
            self._client_types["siliconflow"] = OpenAIClient
        except ImportError:
            pass

        try:
            from .clients.gemini import GeminiClient

            self._client_types["gemini"] = GeminiClient
        except ImportError:
            pass

        try:
            from .clients.anthropic import AnthropicClient

            self._client_types["anthropic"] = AnthropicClient
            self._client_types["claude"] = AnthropicClient
        except ImportError:
            pass

        try:
            from .clients.mock import MockLLMClient

            self._client_types["mock"] = MockLLMClient
            try:
                from .clients.human_relay import HumanRelayClient

                self._client_types["human_relay"] = HumanRelayClient
                self._client_types["human-relay-s"] = HumanRelayClient  # 单轮模式别名
                self._client_types["human-relay-m"] = HumanRelayClient  # 多轮模式别名
            except ImportError:
                pass
        except ImportError:
            pass

    def register_client_type(
        self, model_type: str, client_class: Type[ILLMClient]
    ) -> None:
        """
        注册客户端类型

        Args:
            model_type: 模型类型
            client_class: 客户端类
        """
        with self._lock:
            self._client_types[model_type] = client_class

    def create_client(self, config: Dict[str, Any]) -> ILLMClient:
        """
        创建LLM客户端实例

        Args:
            config: 客户端配置

        Returns:
            ILLMClient: 客户端实例

        Raises:
            LLMClientCreationError: 客户端创建失败
            UnsupportedModelTypeError: 不支持的模型类型
        """
        # 如果配置只包含model_name，从配置实现获取完整配置
        if isinstance(config, dict) and "model_name" in config and "model_type" not in config:
            model_name = config["model_name"]
            client_config = self.config_impl.get_client_config(model_name)
            if not client_config:
                raise LLMClientCreationError(f"未找到模型 {model_name} 的配置")
            config = client_config
        
        # 验证基本配置字段
        if not config.get("model_type"):
            raise LLMClientCreationError("配置中缺少model_type字段")
        if not config.get("model_name"):
            raise LLMClientCreationError("配置中缺少model_name字段")

        # 检查模型类型是否支持
        model_type = config["model_type"]
        if model_type not in self._client_types:
            raise UnsupportedModelTypeError(f"不支持的模型类型: {model_type}")

        # 创建客户端实例
        try:
            client_class = self._client_types[model_type]
            
            # 为客户端注入基础设施层的HTTP客户端
            client = self._create_client_with_http_infrastructure(client_class, config)

            # 自动缓存客户端
            module_config = self.config_impl.get_module_config()
            if module_config.get("cache_enabled", True):
                self.cache_client(config["model_name"], client)

            return client
        except Exception as e:
            raise LLMClientCreationError(f"创建LLM客户端失败: {e}")
    
    def _create_client_with_http_infrastructure(self, client_class: Type[ILLMClient], client_config: Dict[str, Any]) -> ILLMClient:
        """创建客户端实例并注入基础设施层的HTTP客户端
        
        Args:
            client_class: 客户端类
            client_config: 客户端配置
            
        Returns:
            ILLMClient: 客户端实例
        """
        # 创建基础设施层的HTTP客户端
        http_client = self._http_factory.create_client(
            provider=client_config["model_type"],
            model=client_config["model_name"],
            api_key=client_config.get("api_key"),
            base_url=client_config.get("base_url"),
            timeout=client_config.get("timeout", 30),
            max_retries=client_config.get("max_retries", 3),
            headers=client_config.get("headers", {})
        )
        
        # 创建核心层客户端并注入HTTP客户端
        client = client_class(client_config)
        
        # 如果客户端支持设置HTTP客户端，则注入
        if hasattr(client, 'set_http_client'):
            client.set_http_client(http_client)
        elif hasattr(client, '_http_client'):
            setattr(client, '_http_client', http_client)
        
        return client

    def create_client_from_model_name(self, model_name: str) -> ILLMClient:
        """
        根据模型名称创建客户端实例

        Args:
            model_name: 模型名称

        Returns:
            ILLMClient: 客户端实例

        Raises:
            LLMClientCreationError: 客户端创建失败
            UnsupportedModelTypeError: 不支持的模型类型
        """
        # 从配置实现获取客户端配置
        client_config = self.config_impl.get_client_config(model_name)
        if not client_config:
            raise LLMClientCreationError(f"未找到模型 {model_name} 的配置")
        
        return self.create_client(client_config)

    def get_cached_client(self, model_name: str) -> Optional[ILLMClient]:
        """
        获取缓存的客户端实例

        Args:
            model_name: 模型名称

        Returns:
            Optional[ILLMClient]: 缓存的客户端实例，如果不存在则返回None
        """
        with self._lock:
            return self._client_cache.get(model_name)

    def cache_client(self, model_name: str, client: ILLMClient) -> None:
        """
        缓存客户端实例

        Args:
            model_name: 模型名称
            client: 客户端实例
        """
        with self._lock:
            # 检查缓存大小限制
            module_config = self.config_impl.get_module_config()
            max_cache_size = module_config.get("cache_max_size", 100)
            
            if len(self._client_cache) >= max_cache_size:
                # 移除最旧的缓存项（简单的LRU实现）
                oldest_key = next(iter(self._client_cache))
                del self._client_cache[oldest_key]

            self._client_cache[model_name] = client

    def clear_cache(self) -> None:
        """清除所有缓存的客户端实例"""
        with self._lock:
            self._client_cache.clear()
        
        # 同时清除基础设施层的HTTP客户端缓存
        self._http_factory.clear_cache()
        
        # 清除配置实现缓存
        self.config_impl.invalidate_cache()

    def get_or_create_client(self, model_name: str) -> ILLMClient:
        """
        获取或创建客户端实例

        Args:
            model_name: 模型名称

        Returns:
            ILLMClient: 客户端实例
        """
        # 尝试从缓存获取
        client = self.get_cached_client(model_name)
        if client is not None:
            return client

        # 创建新客户端
        client = self.create_client_from_model_name(model_name)

        # 缓存客户端
        module_config = self.config_impl.get_module_config()
        if module_config.get("cache_enabled", True):
            self.cache_client(model_name, client)

        return client

    def list_supported_types(self) -> list[str]:
        """
        列出支持的模型类型

        Returns:
            list[str]: 支持的模型类型列表
        """
        with self._lock:
            return list(self._client_types.keys())

    def list_available_models(self) -> list[str]:
        """
        列出可用的模型

        Returns:
            list[str]: 可用模型列表
        """
        return self.config_impl.list_available_models()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息

        Returns:
            Dict[str, Any]: 缓存信息
        """
        with self._lock:
            module_config = self.config_impl.get_module_config()
            core_cache_info = {
                "cache_size": len(self._client_cache),
                "max_cache_size": module_config.get("cache_max_size", 100),
                "cached_models": list(self._client_cache.keys()),
                "cache_enabled": module_config.get("cache_enabled", True),
            }
        
        # 获取基础设施层的缓存信息
        try:
            # 获取HTTP客户端工厂的缓存信息
            infra_cache_info = {
                "cache_size": len(self._http_factory._client_cache),
                "cached_clients": list(self._http_factory._client_cache.keys())
            }
            core_cache_info["infrastructure_cache"] = infra_cache_info
        except Exception:
            # 如果获取基础设施层缓存信息失败，忽略错误
            pass
        
        # 获取配置实现缓存信息
        try:
            config_cache_info = self.config_impl.get_cache_stats()
            core_cache_info["config_cache"] = config_cache_info
        except Exception:
            pass
        
        return core_cache_info
    
    def get_supported_providers(self) -> list[str]:
        """获取支持的提供商列表
        
        Returns:
            list[str]: 支持的提供商名称列表
        """
        return self._http_factory.get_supported_providers()
    
    def reload_configs(self) -> None:
        """重新加载配置"""
        self._http_factory.reload_configs()
        self.config_impl.invalidate_cache()
        # 重新加载配置数据
        self.config_impl.get_config(use_cache=False)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要信息
        """
        return self.config_impl.get_config_summary()


# 全局工厂实例
_global_factory: Optional[LLMFactoryNew] = None


def get_global_factory_new() -> LLMFactoryNew:
    """
    获取全局工厂实例

    Returns:
        LLMFactoryNew: 全局工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = LLMFactoryNew()
    return _global_factory


def set_global_factory(factory: LLMFactoryNew) -> None:
    """
    设置全局工厂实例

    Args:
        factory: 工厂实例
    """
    global _global_factory
    _global_factory = factory


def create_client(model_name: str) -> ILLMClient:
    """
    使用全局工厂创建客户端

    Args:
        model_name: 模型名称

    Returns:
        ILLMClient: 客户端实例
    """
    return get_global_factory_new().create_client_from_model_name(model_name)


def get_cached_client(model_name: str) -> Optional[ILLMClient]:
    """
    使用全局工厂获取缓存的客户端

    Args:
        model_name: 模型名称

    Returns:
        Optional[ILLMClient]: 缓存的客户端实例
    """
    return get_global_factory_new().get_cached_client(model_name)


# 为了向后兼容，提供LLMFactory别名
LLMFactory = LLMFactoryNew