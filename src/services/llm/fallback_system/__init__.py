"""LLM降级模块"""

from typing import Any, List, Optional
from .fallback_manager import FallbackManager
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession
from .interfaces import IFallbackStrategy, IClientFactory, IFallbackLogger
from .strategies import (
    SequentialFallbackStrategy,
    PriorityFallbackStrategy,
    RandomFallbackStrategy,
    ErrorTypeBasedStrategy,
    ParallelFallbackStrategy,
    ConditionalFallbackStrategy,
    ConditionalFallback,
    create_fallback_strategy
)

# 新组件导入
from .fallback_executor import FallbackExecutor
from .fallback_orchestrator import FallbackOrchestrator
from .fallback_statistics import FallbackStatistics
from .fallback_session_manager import FallbackSessionManager
from .fallback_strategy_manager import FallbackStrategyManager
from .fallback_configuration_manager import FallbackConfigurationManager
from .logger_adapter import LoggerAdapter

# 使用 Core 层的 DefaultFallbackLogger
from src.core.llm.wrappers.fallback_manager import DefaultFallbackLogger


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
                # 对于自管理降级，我们直接调用主客户端的方法
                # 这里假设主客户端可以处理不同的模型参数
                original_model = None
                try:
                    # 尝试通过参数传递模型名称
                    if 'model' in kwargs:
                        original_model = kwargs['model']
                        kwargs['model'] = self.target_model
                    else:
                        kwargs['model'] = self.target_model
                    
                    return await self.owner.generate_async(messages, parameters, **kwargs)
                finally:
                    # 恢复原始模型名称
                    if original_model is not None:
                        kwargs['model'] = original_model
                    elif 'model' in kwargs:
                        del kwargs['model']
            
            def generate_sync(self, messages, parameters, **kwargs):
                # 对于自管理降级，我们直接调用主客户端的方法
                # 这里假设主客户端可以处理不同的模型参数
                original_model = None
                try:
                    # 尝试通过参数传递模型名称
                    if 'model' in kwargs:
                        original_model = kwargs['model']
                        kwargs['model'] = self.target_model
                    else:
                        kwargs['model'] = self.target_model
                    
                    return self.owner.generate(messages, parameters, **kwargs)
                finally:
                    # 恢复原始模型名称
                    if original_model is not None:
                        kwargs['model'] = original_model
                    elif 'model' in kwargs:
                        del kwargs['model']
        
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
    # 主要组件
    "FallbackManager",
    "DefaultFallbackLogger",
    
    # 配置和接口
    "FallbackConfig",
    "FallbackAttempt",
    "FallbackSession",
    "IFallbackStrategy",
    "IClientFactory",
    "IFallbackLogger",
    
    # 策略
    "SequentialFallbackStrategy",
    "PriorityFallbackStrategy",
    "RandomFallbackStrategy",
    "ErrorTypeBasedStrategy",
    "ParallelFallbackStrategy",
    "ConditionalFallbackStrategy",
    "ConditionalFallback",
    "create_fallback_strategy",
    
    # 新组件
    "FallbackExecutor",
    "FallbackOrchestrator",
    "FallbackStatistics",
    "FallbackSessionManager",
    "FallbackStrategyManager",
    "FallbackConfigurationManager",
    "LoggerAdapter",
    
    # 工厂函数
    "create_fallback_manager",
    "SelfManagingFallbackFactory"
]