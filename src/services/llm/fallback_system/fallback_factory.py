"""Fallback系统工厂函数

提供创建FallbackManager实例的工厂函数。
"""

from typing import Any, Optional, List, cast
from .fallback_manager import FallbackManager
from .fallback_config import FallbackConfig
from src.interfaces.llm import IClientFactory, IFallbackLogger, ITaskGroupManager, IPollingPoolManager


def create_fallback_manager(
    config: Optional[FallbackConfig] = None,
    client: Optional[Any] = None,
    client_factory: Optional[IClientFactory] = None,
    logger: Optional[IFallbackLogger] = None,
    task_group_manager: Optional[ITaskGroupManager] = None,
    polling_pool_manager: Optional[IPollingPoolManager] = None
) -> FallbackManager:
    """
    创建FallbackManager实例
    
    Args:
        config: 降级配置
        client: LLM客户端实例
        client_factory: 客户端工厂
        logger: 日志记录器
        task_group_manager: 任务组管理器
        polling_pool_manager: 轮询池管理器
        
    Returns:
        FallbackManager实例
    """
    # 如果提供了client但没有client_factory，创建一个简单的工厂
    if client is not None and client_factory is None:
        class SimpleClientFactory(IClientFactory):
            def __init__(self, client_instance: Any):
                self._client = client_instance
                
            def create_client(self, model_name: str, **kwargs: Any) -> Any:
                return self._client
                
            def get_available_models(self) -> List[str]:
                # 返回一个包含当前模型名称的列表
                if hasattr(self._client, 'config') and hasattr(self._client.config, 'model_name'):
                    return [self._client.config.model_name]
                return []
                
        client_factory = SimpleClientFactory(client)
    
    return FallbackManager(
        config=config,
        client_factory=client_factory,
        logger=logger,
        task_group_manager=task_group_manager,
        polling_pool_manager=polling_pool_manager
    )


def create_default_fallback_logger() -> IFallbackLogger:
    """
    创建默认的降级日志记录器
    
    Returns:
        IFallbackLogger 实例，直接使用 Core 层的 DefaultFallbackLogger
    """
    from src.core.llm.wrappers.fallback_manager import DefaultFallbackLogger
    # 现在不需要类型转换，因为接口已经统一
    return DefaultFallbackLogger()