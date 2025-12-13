"""
存储服务绑定
"""

from typing import Dict, Any
from src.interfaces.storage import IStorageService
from src.interfaces.container.core import ServiceLifetime

class StorageServiceBindings:
    """存储服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册存储服务"""
        # 注册存储服务
        def storage_service():
            from src.infrastructure.storage.storage_service import StorageService
            return StorageService(config)
        
        container.register_factory(
            IStorageService,
            storage_service,
            lifetime=ServiceLifetime.SINGLETON
        )