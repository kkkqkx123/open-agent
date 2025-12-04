"""Fallback系统工厂函数

提供创建FallbackManager实例的工厂函数。
"""

from typing import Any, Optional, List, TYPE_CHECKING
# 从基础设施层导入降级配置
from src.infrastructure.llm.fallback import FallbackConfig
from src.interfaces.llm import IClientFactory, IFallbackLogger, ITaskGroupManager, IPollingPoolManager

if TYPE_CHECKING:
    from .fallback_manager import FallbackManager


def create_fallback_manager(
    config: Optional[FallbackConfig] = None,
    client: Optional[Any] = None,
    client_factory: Optional[IClientFactory] = None,
    logger: Optional[IFallbackLogger] = None,
    task_group_manager: Optional[ITaskGroupManager] = None,
    polling_pool_manager: Optional[IPollingPoolManager] = None
) -> "FallbackManager":
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
    # 延迟导入避免循环依赖
    from .fallback_manager import FallbackManager
    
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