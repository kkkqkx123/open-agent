"""
历史服务绑定
"""

from typing import Dict, Any
from src.interfaces.history import IHistoryManager
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class HistoryServiceBindings:
    """历史服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册历史服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册历史存储
        def history_repository_factory():
            from src.infrastructure.repository.history.memory_repository import MemoryHistoryRepository
            # 从配置中获取历史存储配置
            history_config = config.get("storage", {}).get("repositories", {}).get("history", {})
            backend_config = config.get("storage", {}).get("backends", {}).get("memory", {})
            
            # 合并配置
            repository_config = {
                "max_records": backend_config.get("max_items", 10000),
                **history_config
            }
            
            return MemoryHistoryRepository(repository_config)
        
        from src.interfaces.repository.history import IHistoryRepository
        container.register_factory(
            IHistoryRepository,
            history_repository_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册历史管理器
        def history_manager_factory():
            from src.services.history.manager import HistoryManager
            from src.interfaces.repository.history import IHistoryRepository
            from src.interfaces.logger import ILogger
            
            storage = container.get(IHistoryRepository)
            
            # 获取日志实例
            try:
                logger = container.get(ILogger)
            except:
                logger = None
            
            return HistoryManager(
                storage=storage,
                logger=logger,
                enable_async_batching=config.get("history", {}).get("enable_async_batching", True),
                batch_size=config.get("history", {}).get("batch_size", 10),
                batch_timeout=config.get("history", {}).get("batch_timeout", 1.0)
            )
        
        container.register_factory(
            IHistoryManager,
            history_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )