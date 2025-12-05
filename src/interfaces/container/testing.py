"""
依赖注入容器测试支持接口

定义容器测试相关的接口和工具。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, ContextManager, Type, Generator

from .core import IDependencyContainer


class ITestContainerManager(ABC):
    """测试容器管理器接口"""
    
    @abstractmethod
    def create_isolated_container(
        self, 
        isolation_id: Optional[str] = None
    ) -> IDependencyContainer:
        """
        创建隔离的测试容器
        
        Args:
            isolation_id: 隔离ID
            
        Returns:
            IDependencyContainer: 隔离的容器实例
        """
        pass
    
    @abstractmethod
    def register_test_services(
        self, 
        container: IDependencyContainer,
        service_configs: Dict[str, Any],
        isolation_id: Optional[str] = None
    ) -> None:
        """
        注册测试服务
        
        Args:
            container: 容器实例
            service_configs: 服务配置
            isolation_id: 隔离ID
        """
        pass
    
    @abstractmethod
    def reset_test_services(
        self, 
        container: IDependencyContainer,
        isolation_id: Optional[str] = None
    ) -> None:
        """
        重置测试服务
        
        Args:
            container: 容器实例
            isolation_id: 隔离ID
        """
        pass
    
    @abstractmethod
    def isolated_test_context(
        self, 
        service_configs: Optional[Dict[str, Any]] = None
    ) -> ContextManager[IDependencyContainer]:
        """
        创建隔离的测试上下文
        
        Args:
            service_configs: 服务配置
            
        Yields:
            IDependencyContainer: 隔离的容器实例
        """
        pass


class IMockServiceRegistry(ABC):
    """Mock服务注册器接口"""
    
    @abstractmethod
    def register_mock(
        self, 
        interface: Type, 
        mock_instance: Any,
        isolation_id: Optional[str] = None
    ) -> None:
        """
        注册Mock服务
        
        Args:
            interface: 接口类型
            mock_instance: Mock实例
            isolation_id: 隔离ID
        """
        pass
    
    @abstractmethod
    def get_mock(
        self, 
        interface: Type, 
        isolation_id: Optional[str] = None
    ) -> Any:
        """
        获取Mock服务
        
        Args:
            interface: 接口类型
            isolation_id: 隔离ID
            
        Returns:
            Any: Mock实例
        """
        pass
    
    @abstractmethod
    def clear_mocks(self, isolation_id: Optional[str] = None) -> None:
        """
        清除Mock服务
        
        Args:
            isolation_id: 隔离ID
        """
        pass
    
    @abstractmethod
    def has_mock(
        self, 
        interface: Type, 
        isolation_id: Optional[str] = None
    ) -> bool:
        """
        检查是否存在Mock服务
        
        Args:
            interface: 接口类型
            isolation_id: 隔离ID
            
        Returns:
            bool: 是否存在Mock服务
        """
        pass


class ITestIsolationStrategy(ABC):
    """测试隔离策略接口"""
    
    @abstractmethod
    def create_isolation_context(
        self, 
        base_container: IDependencyContainer,
        isolation_id: str
    ) -> IDependencyContainer:
        """
        创建隔离上下文
        
        Args:
            base_container: 基础容器
            isolation_id: 隔离ID
            
        Returns:
            IDependencyContainer: 隔离的容器
        """
        pass
    
    @abstractmethod
    def cleanup_isolation_context(
        self, 
        container: IDependencyContainer,
        isolation_id: str
    ) -> None:
        """
        清理隔离上下文
        
        Args:
            container: 容器实例
            isolation_id: 隔离ID
        """
        pass


class DefaultTestIsolationStrategy(ITestIsolationStrategy):
    """默认测试隔离策略"""
    
    def create_isolation_context(
        self, 
        base_container: IDependencyContainer,
        isolation_id: str
    ) -> IDependencyContainer:
        """创建隔离上下文"""
        # 创建新的容器实例
        from src.services.container import DependencyContainer
        isolated_container = DependencyContainer(environment=f"test_{isolation_id}")
        
        # 如果基础容器支持复制注册信息，则复制
        if hasattr(base_container, 'copy_registrations') and callable(getattr(base_container, 'copy_registrations')):
            base_container.copy_registrations(isolated_container)  # type: ignore
        
        return isolated_container
    
    def cleanup_isolation_context(
        self, 
        container: IDependencyContainer,
        isolation_id: str
    ) -> None:
        """清理隔离上下文"""
        if hasattr(container, 'clear'):
            container.clear()


class TestContainerManager(ITestContainerManager):
    """测试容器管理器实现"""
    
    def __init__(self, isolation_strategy: Optional[ITestIsolationStrategy] = None):
        self.isolation_strategy = isolation_strategy or DefaultTestIsolationStrategy()
        self.mock_registry = MockServiceRegistry()
    
    def create_isolated_container(
        self, 
        isolation_id: Optional[str] = None
    ) -> IDependencyContainer:
        """创建隔离的测试容器"""
        from src.services.container import get_global_container
        base_container = get_global_container()
        
        isolation_id = isolation_id or self._generate_isolation_id()
        return self.isolation_strategy.create_isolation_context(
            base_container, isolation_id
        )
    
    def register_test_services(
        self, 
        container: IDependencyContainer,
        service_configs: Dict[str, Any],
        isolation_id: Optional[str] = None
    ) -> None:
        """注册测试服务"""
        # 这里可以根据service_configs注册相应的测试服务
        # 具体实现由子类或配置驱动
        pass
    
    def reset_test_services(
        self, 
        container: IDependencyContainer,
        isolation_id: Optional[str] = None
    ) -> None:
        """重置测试服务"""
        isolation_id = isolation_id or "default"
        self.isolation_strategy.cleanup_isolation_context(container, isolation_id)
        self.mock_registry.clear_mocks(isolation_id)
    
    def isolated_test_context(
        self, 
        service_configs: Optional[Dict[str, Any]] = None
    ) -> ContextManager[IDependencyContainer]:
        """创建隔离的测试上下文"""
        from contextlib import contextmanager
        
        @contextmanager
        def _context_manager() -> Generator[IDependencyContainer, None, None]:
            isolation_id = self._generate_isolation_id()
            container = self.create_isolated_container(isolation_id)
            
            try:
                if service_configs:
                    self.register_test_services(container, service_configs, isolation_id)
                yield container
            finally:
                self.reset_test_services(container, isolation_id)
        
        return _context_manager()
    
    def _generate_isolation_id(self) -> str:
        """生成隔离ID"""
        import uuid
        return str(uuid.uuid4())[:8]


class MockServiceRegistry(IMockServiceRegistry):
    """Mock服务注册器实现"""
    
    def __init__(self):
        self._mocks: Dict[str, Dict[Type, Any]] = {}
    
    def _get_isolation_key(self, isolation_id: Optional[str] = None) -> str:
        """获取隔离键"""
        return isolation_id or "default"
    
    def register_mock(
        self, 
        interface: Type, 
        mock_instance: Any,
        isolation_id: Optional[str] = None
    ) -> None:
        """注册Mock服务"""
        key = self._get_isolation_key(isolation_id)
        if key not in self._mocks:
            self._mocks[key] = {}
        self._mocks[key][interface] = mock_instance
    
    def get_mock(
        self, 
        interface: Type, 
        isolation_id: Optional[str] = None
    ) -> Any:
        """获取Mock服务"""
        key = self._get_isolation_key(isolation_id)
        return self._mocks.get(key, {}).get(interface)
    
    def clear_mocks(self, isolation_id: Optional[str] = None) -> None:
        """清除Mock服务"""
        key = self._get_isolation_key(isolation_id)
        if key in self._mocks:
            del self._mocks[key]
    
    def has_mock(
        self, 
        interface: Type, 
        isolation_id: Optional[str] = None
    ) -> bool:
        """检查是否存在Mock服务"""
        key = self._get_isolation_key(isolation_id)
        return interface in self._mocks.get(key, {})