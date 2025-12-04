"""
服务绑定基类

提供所有服务绑定的通用功能和最佳实践。
"""

import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable, TypeVar
from contextlib import contextmanager

T = TypeVar('T')

from src.interfaces.container import (
    IDependencyContainer,
    IExceptionHandler,
    ITestContainerManager
)
from src.interfaces.container.exceptions import (
    RegistrationError,
)
from src.interfaces.common_infra import ServiceLifetime
from src.services.container.injection.injection_base import get_global_injection_registry


class BaseServiceBindings(ABC):
    """服务绑定基类
    
    提供所有服务绑定的通用功能和最佳实践，包括：
    - 统一的异常处理
    - 延迟依赖解析支持
    - 测试隔离支持
    - 配置验证
    """
    
    def __init__(self):
        self._exception_handler: Optional[IExceptionHandler] = None
        self._test_manager: Optional[ITestContainerManager] = None
    
    def set_exception_handler(self, handler: IExceptionHandler) -> None:
        """设置异常处理器"""
        self._exception_handler = handler
    
    def set_test_manager(self, manager: ITestContainerManager) -> None:
        """设置测试管理器"""
        self._test_manager = manager
    
    def register_services(
        self, 
        container: IDependencyContainer, 
        config: Dict[str, Any], 
        environment: str = "default"
    ) -> None:
        """注册服务的统一入口
        
        Args:
            container: 依赖注入容器
            config: 配置字典
            environment: 环境名称
            
        Raises:
            ValidationError: 配置验证失败时抛出
            RegistrationError: 服务注册失败时抛出
        """
        try:
            # 验证配置
            self._validate_config(config)
            
            # 执行实际的服务注册
            self._do_register_services(container, config, environment)
            
            # 注册后处理
            self._post_register(container, config, environment)
            
        except Exception as e:
            self._handle_registration_error(e, environment)
            raise
    
    @abstractmethod
    def _do_register_services(
        self, 
        container: IDependencyContainer, 
        config: Dict[str, Any], 
        environment: str
    ) -> None:
        """实际的服务注册逻辑，子类必须实现"""
        pass
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置，子类可以重写
        
        Args:
            config: 配置字典
            
        Raises:
            ValidationError: 配置验证失败时抛出
        """
        pass
    
    def _post_register(
        self, 
        container: IDependencyContainer, 
        config: Dict[str, Any], 
        environment: str
    ) -> None:
        """注册后处理，子类可以重写
        
        Args:
            container: 依赖注入容器
            config: 配置字典
            environment: 环境名称
        """
        pass
    
    def _handle_registration_error(self, error: Exception, environment: str) -> None:
        """处理注册错误
        
        Args:
            error: 异常对象
            environment: 环境名称
        """
        if self._exception_handler:
            registration_error = RegistrationError(str(error))
            self._exception_handler.handle_registration_error(registration_error, environment)
        else:
            print(f"[ERROR] 服务注册失败 ({environment}): {error}", file=sys.stderr)
    
    def register_delayed_factory(
        self,
        container: IDependencyContainer,
        interface: Type,
        factory_factory: Callable[[], Callable[..., Any]],
        environment: str = "default",
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        **kwargs
    ) -> None:
        """注册延迟解析工厂的便捷方法
        
        Args:
            container: 依赖注入容器
            interface: 接口类型
            factory_factory: 工厂工厂函数
            environment: 环境名称
            lifetime: 生命周期类型
            **kwargs: 其他参数
        """
        try:
            if hasattr(container, 'register_factory_with_delayed_resolution'):
                container.register_factory_with_delayed_resolution(
                    interface, factory_factory, environment, lifetime, **kwargs
                )
            else:
                # 降级到普通工厂注册
                def delayed_factory():
                    actual_factory = factory_factory()
                    return actual_factory()
                
                container.register_factory(interface, delayed_factory, environment, lifetime, **kwargs)
        except Exception as e:
            registration_error = RegistrationError(
                f"延迟工厂注册失败: {e}",
                interface.__name__
            )
            self._handle_registration_error(registration_error, environment)
            raise
    
    @contextmanager
    def test_isolation(
        self, 
        container: IDependencyContainer, 
        config: Optional[Dict[str, Any]] = None,
        isolation_id: Optional[str] = None
    ):
        """创建测试隔离上下文
        
        Args:
            container: 依赖注入容器
            config: 测试配置
            isolation_id: 隔离ID
            
        Yields:
            IDependencyContainer: 隔离的容器实例
        """
        if self._test_manager:
            with self._test_manager.isolated_test_context(config) as test_container:
                yield test_container
        else:
            # 降级处理
            test_container = self._create_test_container(container, isolation_id)
            if config:
                self.register_services(test_container, config, f"test_{isolation_id or 'default'}")
            try:
                yield test_container
            finally:
                self._cleanup_test_container(test_container, isolation_id)
    
    def _create_test_container(
        self, 
        container: IDependencyContainer, 
        isolation_id: Optional[str] = None
    ) -> IDependencyContainer:
        """创建测试容器
        
        Args:
            container: 基础容器
            isolation_id: 隔离ID
            
        Returns:
            IDependencyContainer: 测试容器
        """
        if hasattr(container, 'create_test_isolation'):
            return container.create_test_isolation(isolation_id)
        else:
            # 降级处理：创建新容器实例
            from src.services.container import DependencyContainer
            return DependencyContainer(environment=f"test_{isolation_id or 'default'}")
    
    def _cleanup_test_container(
        self, 
        container: IDependencyContainer, 
        isolation_id: Optional[str] = None
    ) -> None:
        """清理测试容器
        
        Args:
            container: 测试容器
            isolation_id: 隔离ID
        """
        if hasattr(container, 'reset_test_state'):
            container.reset_test_state(isolation_id)
        elif hasattr(container, 'clear'):
            container.clear()
    
    def register_with_error_handling(
        self,
        container: IDependencyContainer,
        register_func: Callable[[], None],
        error_context: str,
        environment: str = "default"
    ) -> None:
        """带错误处理的注册方法
        
        Args:
            container: 依赖注入容器
            register_func: 注册函数
            error_context: 错误上下文
            environment: 环境名称
        """
        try:
            register_func()
        except Exception as e:
            registration_error = RegistrationError(
                f"{error_context}失败: {e}"
            )
            self._handle_registration_error(registration_error, environment)
            raise
    
    def safe_get_service(
        self, 
        container: IDependencyContainer, 
        service_type: Type
    ) -> Optional[Any]:
        """安全获取服务实例
        
        Args:
            container: 依赖注入容器
            service_type: 服务类型
            
        Returns:
            Optional[Any]: 服务实例，如果获取失败返回None
        """
        try:
            if hasattr(container, 'try_get'):
                return container.try_get(service_type)
            else:
                return container.get(service_type)
        except Exception:
            return None
    
    def validate_required_services(
        self, 
        container: IDependencyContainer, 
        required_services: List[Type],
        environment: str = "default"
    ) -> None:
        """验证必需的服务是否已注册
        
        Args:
            container: 依赖注入容器
            required_services: 必需的服务类型列表
            environment: 环境名称
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        missing_services = []
        for service_type in required_services:
            if not container.has_service(service_type):
                missing_services.append(service_type.__name__)
        
        if missing_services:
            from src.interfaces.container.exceptions import ValidationError
            error = ValidationError(
                f"缺少必需的服务: {', '.join(missing_services)}",
                missing_services
            )
            self._handle_registration_error(error, environment)
            raise error
    
    def setup_injection_layer(
        self,
        container: IDependencyContainer,
        service_types: List[Type],
        fallback_factories: Optional[Dict[Type, Callable[[], Any]]] = None
    ) -> None:
        """为指定服务设置注入层
        
        Args:
            container: 依赖注入容器
            service_types: 要设置注入层的服务类型列表
            fallback_factories: fallback工厂字典
        """
        if fallback_factories is None:
            fallback_factories = {}
        
        injection_registry = get_global_injection_registry()
        
        for service_type in service_types:
            try:
                # 获取服务实例
                service_instance = container.get(service_type)
                
                # 注册到注入层
                fallback_factory = fallback_factories.get(service_type)
                injection = injection_registry.register(service_type, fallback_factory)
                injection.set_instance(service_instance)
                
            except Exception as e:
                # 记录错误但不影响主要流程
                print(f"[WARNING] 设置注入层失败 {service_type.__name__}: {e}", file=sys.stderr)
    
    def setup_service_injection(
        self,
        container: IDependencyContainer,
        service_type: Type,
        fallback_factory: Optional[Callable[[], Any]] = None
    ) -> None:
        """为单个服务设置注入层
        
        Args:
            container: 依赖注入容器
            service_type: 服务类型
            fallback_factory: fallback工厂函数
        """
        fallback_factories = {service_type: fallback_factory} if fallback_factory else None
        self.setup_injection_layer(container, [service_type], fallback_factories)
    
    def clear_injection_layer(self, service_types: Optional[List[Type]] = None) -> None:
        """清除注入层实例
        
        Args:
            service_types: 要清除的服务类型列表，如果为None则清除所有
        """
        injection_registry = get_global_injection_registry()
        
        if service_types is None:
            injection_registry.clear_all()
        else:
            for service_type in service_types:
                try:
                    injection = injection_registry.get_injection(service_type)
                    injection.clear_instance()
                except ValueError:
                    # 服务类型未注册，忽略
                    pass
    
    def get_injection_status(self, service_types: Optional[List[Type]] = None) -> Dict[str, Dict[str, Any]]:
        """获取注入层状态
        
        Args:
            service_types: 要查询的服务类型列表，如果为None则查询所有
            
        Returns:
            状态信息字典
        """
        injection_registry = get_global_injection_registry()
        all_status = injection_registry.get_all_status()
        
        if service_types is None:
            return all_status
        
        # 过滤指定的服务类型
        filtered_status = {}
        for service_type in service_types:
            service_name = service_type.__name__
            if service_name in all_status:
                filtered_status[service_name] = all_status[service_name]
        
        return filtered_status


class EnvironmentSpecificBindings(BaseServiceBindings):
    """环境特定的服务绑定基类"""
    
    def register_for_environment(
        self, 
        container: IDependencyContainer, 
        config: Dict[str, Any], 
        environment: str
    ) -> None:
        """为特定环境注册服务
        
        Args:
            container: 依赖注入容器
            config: 配置字典
            environment: 环境名称
        """
        # 根据环境选择不同的配置
        env_config = self._get_environment_config(config, environment)
        
        # 注册服务
        self.register_services(container, env_config, environment)
    
    def _get_environment_config(
        self, 
        base_config: Dict[str, Any], 
        environment: str
    ) -> Dict[str, Any]:
        """获取环境特定的配置
        
        Args:
            base_config: 基础配置
            environment: 环境名称
            
        Returns:
            Dict[str, Any]: 环境特定的配置
        """
        # 子类可以重写此方法来提供环境特定的配置
        return base_config.copy()