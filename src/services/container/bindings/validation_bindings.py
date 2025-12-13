"""
验证服务绑定
"""

from typing import Dict, Any
from src.interfaces.config import IConfigValidator
from src.interfaces.container.core import ServiceLifetime

class ValidationServiceBindings:
    """验证服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册验证服务"""
        # 注册配置验证器
        def config_validator():
            from src.infrastructure.config.config_validator import ConfigValidator
            return ConfigValidator(config)
        
        container.register_factory(
            IConfigValidator,
            config_validator,
            lifetime=ServiceLifetime.SINGLETON
        )