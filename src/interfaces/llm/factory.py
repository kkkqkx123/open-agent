"""LLM工厂接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .base import ILLMClient


class ILLMClientFactory(ABC):
    """LLM客户端工厂接口"""

    @abstractmethod
    def create_client(self, config: Dict[str, Any]) -> ILLMClient:
        """
        创建LLM客户端实例

        Args:
            config: 客户端配置

        Returns:
            ILLMClient: 客户端实例
        """
        pass

    @abstractmethod
    def get_cached_client(self, model_name: str) -> Optional[ILLMClient]:
        """
        获取缓存的客户端实例

        Args:
            model_name: 模型名称

        Returns:
            Optional[ILLMClient]: 缓存的客户端实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def cache_client(self, model_name: str, client: ILLMClient) -> None:
        """
        缓存客户端实例

        Args:
            model_name: 模型名称
            client: 客户端实例
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """清除所有缓存的客户端实例"""
        pass


class IClientFactory(ABC):
    """客户端工厂接口"""
    
    @abstractmethod
    def create_client(self, model_name: str) -> ILLMClient:
        """创建客户端实例"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        pass