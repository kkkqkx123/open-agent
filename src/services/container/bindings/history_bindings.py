"""
历史服务绑定
"""

from typing import Dict, Any
from src.interfaces.history import IHistoryManager
from src.interfaces.container.core import ServiceLifetime

class HistoryServiceBindings:
    """历史服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册历史服务"""
        # 注册历史管理器
        def history_manager():
            from src.infrastructure.history.history_manager import HistoryManager
            return HistoryManager(config)
        
        container.register_factory(
            IHistoryManager,
            history_manager,
            lifetime=ServiceLifetime.SINGLETON
        )