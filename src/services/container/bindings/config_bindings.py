"""
配置服务绑定
"""

from typing import Dict, Any
from src.interfaces.config import IConfigLoader
from src.interfaces.container.core import ServiceLifetime

class ConfigServiceBindings:
    """配置服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册配置服务"""
        # 注册配置加载器
        def config_loader():
            from src.infrastructure.config.loader import ConfigLoader
            return ConfigLoader()
        
        container.register_factory(
            IConfigLoader,
            config_loader,
            lifetime=ServiceLifetime.SINGLETON
        )