"""
配置服务绑定
"""

from typing import Dict, Any
from src.interfaces.config import IConfigLoader
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class ConfigServiceBindings:
    """配置服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册配置服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册配置加载器
        def config_loader_factory():
            from src.infrastructure.config.loader import ConfigLoader
            return ConfigLoader()
        
        container.register_factory(
            IConfigLoader,
            config_loader_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册配置门面
        def config_facade_factory():
            from src.core.config.config_facade import ConfigFacade
            from src.infrastructure.config.factory import ConfigFactory
            config_factory = ConfigFactory()
            return ConfigFacade(config_factory)
        
        from src.core.config.config_facade import ConfigFacade
        container.register_factory(
            ConfigFacade,
            config_facade_factory,
            lifetime=ServiceLifetime.SINGLETON
        )