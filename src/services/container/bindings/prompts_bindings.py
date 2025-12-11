"""提示词系统依赖注入绑定配置

统一注册提示词相关的服务，包括消息工厂、类型注册表和错误处理器。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
重构后使用接口依赖，避免循环依赖。
"""

import sys
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环依赖
    from src.interfaces.messages import IMessageFactory
    from src.services.prompts.type_registry import PromptTypeRegistry
    from src.infrastructure.error_management.impl.prompts import PromptErrorHandler

# 接口导入 - 集中化的接口定义
from src.interfaces.messages import IMessageFactory
from src.interfaces.container.core import ServiceLifetime
from src.services.container.core.base_service_bindings import BaseServiceBindings


class PromptsServiceBindings(BaseServiceBindings):
    """提示词服务绑定类
    
    负责注册所有提示词相关服务，包括：
    - 消息工厂接口实现
    - 提示词类型注册表
    - 提示词错误处理器
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证提示词配置"""
        # 提示词系统通常不需要特殊验证
        pass
    
    def _do_register_services(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行提示词服务注册"""
        _register_message_factory(container, config, environment)
        _register_prompt_type_registry(container, config, environment)
        _register_prompt_error_handler(container, config, environment)
    
    def _post_register(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 延迟导入具体实现类，避免循环依赖
            def get_service_types() -> list:
                from src.services.prompts.type_registry import PromptTypeRegistry
                from src.infrastructure.error_management.impl.prompts import PromptErrorHandler
                
                return [
                    IMessageFactory,
                    PromptTypeRegistry,
                    PromptErrorHandler
                ]
            
            service_types = get_service_types()
            self.setup_injection_layer(container, service_types)
            
            print(f"[INFO] 已设置提示词服务注入层 (environment: {environment})", file=sys.stdout)
        except Exception as e:
            print(f"[WARNING] 设置提示词注入层失败: {e}", file=sys.stderr)


def _register_message_factory(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册消息工厂"""
    print(f"[INFO] 注册消息工厂...", file=sys.stdout)
    
    # 延迟导入具体实现
    def create_message_factory() -> 'IMessageFactory':
        from src.infrastructure.messages.factory import MessageFactory
        return MessageFactory()
    
    container.register_factory(
        IMessageFactory,
        create_message_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册消息工厂完成", file=sys.stdout)


def _register_prompt_type_registry(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册提示词类型注册表"""
    print(f"[INFO] 注册提示词类型注册表...", file=sys.stdout)
    
    # 延迟导入具体实现
    def create_prompt_type_registry() -> 'PromptTypeRegistry':
        from src.services.prompts.type_registry import PromptTypeRegistry
        return PromptTypeRegistry()
    
    container.register_factory(
        PromptTypeRegistry,
        create_prompt_type_registry,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册提示词类型注册表完成", file=sys.stdout)


def _register_prompt_error_handler(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册提示词错误处理器"""
    print(f"[INFO] 注册提示词错误处理器...", file=sys.stdout)
    
    # 延迟导入具体实现
    def create_prompt_error_handler() -> 'PromptErrorHandler':
        from src.infrastructure.error_management.impl.prompts import PromptErrorHandler
        return PromptErrorHandler()
    
    container.register_factory(
        PromptErrorHandler,
        create_prompt_error_handler,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册提示词错误处理器完成", file=sys.stdout)