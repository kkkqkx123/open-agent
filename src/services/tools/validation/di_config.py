"""
工具检验模块依赖注入配置
注册工具检验服务到依赖注入容器
"""

from src.infrastructure.container_interfaces import IDependencyContainer
from src.core.tools.validation.manager import ToolValidationManager
from src.core.tools.validation.interfaces import IToolValidator
from src.core.tools.validation.validators.config_validator import ConfigValidator
from src.core.tools.validation.validators.loading_validator import LoadingValidator
from src.core.tools.validation.validators.rest_validator import RestToolValidator
from src.core.tools.validation.validators.rest_validator import RestToolValidator
from src.core.tools.validation.validators.mcp_validator import MCPToolValidator


class ToolValidationModule:
    """工具检验模块依赖注入配置"""
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册工具检验服务
        
        Args:
            container: 依赖注入容器
        """
        # 注册验证管理器
        container.register(ToolValidationManager, ToolValidationManager)
        
        # 注册验证器接口和实现
        container.register(IToolValidator, ConfigValidator)
        container.register(IToolValidator, LoadingValidator)
        container.register(IToolValidator, RestToolValidator)
        container.register(IToolValidator, RestToolValidator)
        container.register(IToolValidator, MCPToolValidator)
        
        # 注册具体的验证器实现（用于直接获取）
        container.register(ConfigValidator, ConfigValidator)
        container.register(LoadingValidator, LoadingValidator)
        container.register(RestToolValidator, RestToolValidator)
        container.register(RestToolValidator, RestToolValidator)
        container.register(MCPToolValidator, MCPToolValidator)