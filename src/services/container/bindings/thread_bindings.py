"""
线程服务绑定
"""

from typing import Dict, Any
from src.interfaces.threads import IThreadService
from src.interfaces.container.core import ServiceLifetime

class ThreadServiceBindings:
    """线程服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册线程服务"""
        # 注册线程服务
        def thread_service():
            from src.infrastructure.threads.thread_service import ThreadService
            return ThreadService(config)
        
        container.register_factory(
            IThreadService,
            thread_service,
            lifetime=ServiceLifetime.SINGLETON
        )