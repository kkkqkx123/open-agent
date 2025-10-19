"""LLM客户端工厂实现"""

from typing import Dict, Any, Optional, Type
from threading import RLock

from .interfaces import ILLMClient, ILLMClientFactory
from .config import LLMClientConfig, LLMModuleConfig
from .exceptions import LLMClientCreationError, UnsupportedModelTypeError


class LLMFactory(ILLMClientFactory):
    """LLM客户端工厂实现"""
    
    def __init__(self, config: Optional[LLMModuleConfig] = None) -> None:
        """
        初始化工厂
        
        Args:
            config: 模块配置
        """
        self.config = config or LLMModuleConfig()
        self._client_cache: Dict[str, ILLMClient] = {}
        self._client_types: Dict[str, Type[ILLMClient]] = {}
        self._lock = RLock()
        
        # 注册默认客户端类型
        self._register_default_clients()
    
    def _register_default_clients(self) -> None:
        """注册默认客户端类型"""
        # 延迟导入避免循环依赖
        try:
            from .clients.openai.unified_client import OpenAIUnifiedClient
            self._client_types["openai"] = OpenAIUnifiedClient
        except ImportError:
            pass
            
        try:
            from .clients.gemini_client import GeminiClient
            self._client_types["gemini"] = GeminiClient
        except ImportError:
            pass
            
        try:
            from .clients.anthropic_client import AnthropicClient
            self._client_types["anthropic"] = AnthropicClient
            self._client_types["claude"] = AnthropicClient
        except ImportError:
            pass
            
        try:
            from .clients.mock_client import MockLLMClient
            self._client_types["mock"] = MockLLMClient
        except ImportError:
            pass
    
    def register_client_type(self, model_type: str, client_class: Type[ILLMClient]) -> None:
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
        # 转换配置
        if isinstance(config, dict):
            # 验证基本配置字段
            if not config.get("model_type"):
                raise LLMClientCreationError("配置中缺少model_type字段")
            if not config.get("model_name"):
                raise LLMClientCreationError("配置中缺少model_name字段")
            
            try:
                client_config = LLMClientConfig.from_dict(config)
            except Exception as e:
                raise LLMClientCreationError(f"配置转换失败: {e}")
        else:
            # 如果已经是LLMClientConfig实例，直接使用
            client_config = config
        
        # 检查模型类型是否支持
        model_type = client_config.model_type
        if model_type not in self._client_types:
            raise UnsupportedModelTypeError(f"不支持的模型类型: {model_type}")
        
        # 创建客户端实例
        try:
            client_class = self._client_types[model_type]
            client = client_class(client_config)
            
            # 如果配置了降级模型，包装为降级客户端
            if client_config.fallback_enabled and client_config.fallback_models:
                from .fallback_client import FallbackClientWrapper
                client = FallbackClientWrapper(client, client_config.fallback_models)
            
            # 自动缓存客户端
            if self.config.cache_enabled:
                self.cache_client(client_config.model_name, client)
            
            return client
        except Exception as e:
            raise LLMClientCreationError(f"创建LLM客户端失败: {e}")
    
    def create_client_from_config(self, client_config: LLMClientConfig) -> ILLMClient:
        """
        从LLMClientConfig创建客户端实例
        
        Args:
            client_config: 客户端配置
            
        Returns:
            ILLMClient: 客户端实例
            
        Raises:
            LLMClientCreationError: 客户端创建失败
            UnsupportedModelTypeError: 不支持的模型类型
        """
        # 检查模型类型是否支持
        model_type = client_config.model_type
        if model_type not in self._client_types:
            raise UnsupportedModelTypeError(f"不支持的模型类型: {model_type}")
        
        # 创建客户端实例
        try:
            client_class = self._client_types[model_type]
            client = client_class(client_config)
            return client
        except Exception as e:
            raise LLMClientCreationError(f"创建LLM客户端失败: {e}")
    
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
            if len(self._client_cache) >= self.config.cache_max_size:
                # 移除最旧的缓存项（简单的LRU实现）
                oldest_key = next(iter(self._client_cache))
                del self._client_cache[oldest_key]
            
            self._client_cache[model_name] = client
    
    def clear_cache(self) -> None:
        """清除所有缓存的客户端实例"""
        with self._lock:
            self._client_cache.clear()
    
    def get_or_create_client(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ) -> ILLMClient:
        """
        获取或创建客户端实例
        
        Args:
            model_name: 模型名称
            config: 客户端配置
            
        Returns:
            ILLMClient: 客户端实例
        """
        # 尝试从缓存获取
        client = self.get_cached_client(model_name)
        if client is not None:
            return client
        
        # 创建新客户端
        client = self.create_client(config)
        
        # 缓存客户端
        if self.config.cache_enabled:
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
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        with self._lock:
            return {
                "cache_size": len(self._client_cache),
                "max_cache_size": self.config.cache_max_size,
                "cached_models": list(self._client_cache.keys()),
                "cache_enabled": self.config.cache_enabled
            }


# 全局工厂实例
_global_factory: Optional[LLMFactory] = None


def get_global_factory() -> LLMFactory:
    """
    获取全局工厂实例
    
    Returns:
        LLMFactory: 全局工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = LLMFactory()
    return _global_factory


def set_global_factory(factory: LLMFactory) -> None:
    """
    设置全局工厂实例
    
    Args:
        factory: 工厂实例
    """
    global _global_factory
    _global_factory = factory


def create_client(config: Dict[str, Any]) -> ILLMClient:
    """
    使用全局工厂创建客户端
    
    Args:
        config: 客户端配置
        
    Returns:
        ILLMClient: 客户端实例
    """
    return get_global_factory().create_client(config)


def get_cached_client(model_name: str) -> Optional[ILLMClient]:
    """
    使用全局工厂获取缓存的客户端
    
    Args:
        model_name: 模型名称
        
    Returns:
        Optional[ILLMClient]: 缓存的客户端实例
    """
    return get_global_factory().get_cached_client(model_name)