"""
验证服务绑定
"""

from typing import Dict, Any
from src.interfaces.config import IConfigValidator
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class ValidationServiceBindings:
    """验证服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册验证服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册配置验证器
        def config_validator_factory():
            from src.infrastructure.config.validation.config_validator import ConfigValidator
            
            # 获取日志实例
            try:
                from src.interfaces.logger import ILogger
                logger = container.get(ILogger)
            except:
                logger = None
            
            return ConfigValidator(
                cache_manager=None,
                config_fixer=None,
                logger=logger  # type: ignore
            )
        
        container.register_factory(
            IConfigValidator,
            config_validator_factory,
            lifetime=ServiceLifetime.SINGLETON
        )