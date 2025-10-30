"""LLM降级模块"""

from typing import Any, List, Optional
from .fallback_manager import FallbackManager, DefaultFallbackLogger
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession
from .interfaces import IFallbackStrategy, IClientFactory, IFallbackLogger
from .strategies import (
    SequentialFallbackStrategy,
    PriorityFallbackStrategy,
    RandomFallbackStrategy,
    ErrorTypeBasedStrategy,
    create_fallback_strategy
)


class SelfManagingFallbackFactory(IClientFactory):
    """自管理的降级工厂 - 用于EnhancedLLMClient的自我降级"""
    
    def __init__(self, owner_client: Any):
        """
        初始化自管理降级工厂
        
        Args:
            owner_client: 拥有者客户端（EnhancedLLMClient实例）
        """
        self.owner_client = owner_client
        
    def create_client(self, model_name: str) -> Any:
        """
        创建客户端 - 对于自管理降级，返回一个能调用指定模型的包装器
        
        Args:
            model_name: 模型名称
            
        Returns:
            客户端包装器
        """
        # 创建一个包装器，可以调用指定模型
        class ModelSpecificClient:
            def __init__(self, owner, target_model: str):
                self.owner = owner
                self.target_model = target_model
            
            async def generate_async(self, messages, parameters, **kwargs):
                # 临时修改配置中的模型名称来调用不同模型
                original_model = self.owner.config.model_name
                try:
                    self.owner.config.model_name = self.target_model
                    return await self.owner._do_generate_async(messages, parameters, **kwargs)
                finally:
                    self.owner.config.model_name = original_model
            
            def generate_sync(self, messages, parameters, **kwargs):
                # 临时修改配置中的模型名称来调用不同模型
                original_model = self.owner.config.model_name
                try:
                    self.owner.config.model_name = self.target_model
                    return self.owner._do_generate_sync(messages, parameters, **kwargs)
                finally:
                    self.owner.config.model_name = original_model
        
        return ModelSpecificClient(self.owner_client, model_name)
        
    def get_available_models(self) -> List[str]:
        """获取可用的降级模型列表"""
        if hasattr(self.owner_client.config, 'fallback_models'):
            return self.owner_client.config.fallback_models
        return []


def create_fallback_manager(config: FallbackConfig, owner_client: Optional[Any] = None) -> FallbackManager:
    """
    创建降级管理器
    
    Args:
        config: 降级配置
        owner_client: 拥有者客户端（可选，用于自管理降级）
        
    Returns:
        降级管理器实例
    """
    if owner_client is not None:
        factory = SelfManagingFallbackFactory(owner_client)
    else:
        # 创建一个占位符工厂，等待后续设置
        class PlaceholderFactory(IClientFactory):
            def create_client(self, model_name: str) -> Any:
                raise NotImplementedError("Placeholder factory cannot create clients")
            
            def get_available_models(self) -> List[str]:
                return []
        
        factory = PlaceholderFactory()
    
    return FallbackManager(config, factory)


__all__ = [
    "FallbackManager",
    "DefaultFallbackLogger",
    "FallbackConfig",
    "FallbackAttempt",
    "FallbackSession",
    "IFallbackStrategy",
    "IClientFactory",
    "IFallbackLogger",
    "SequentialFallbackStrategy",
    "PriorityFallbackStrategy",
    "RandomFallbackStrategy",
    "ErrorTypeBasedStrategy",
    "create_fallback_strategy",
    "create_fallback_manager",
    "SelfManagingFallbackFactory"
]