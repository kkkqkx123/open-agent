"""
生命周期管理接口

定义服务生命周期管理的相关接口，支持服务的初始化、启动、停止和释放。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from enum import Enum

from .core import ServiceStatus


'''
生命周期感知接口
'''

class ILifecycleAware(ABC):
    """
    生命周期感知接口
    
    定义需要生命周期管理的服务契约。
    实现此接口的服务可以参与容器的生命周期管理。
    
    生命周期阶段：
    1. initialize() - 初始化
    2. start() - 启动（可选）
    3. stop() - 停止（可选）
    4. dispose() - 释放
    
    使用示例：
        ```python
        class DatabaseService(ILifecycleAware):
            def __init__(self):
                self._initialized = False
                self._connection = None
            
            def initialize(self):
                if not self._initialized:
                    self._connection = create_connection()
                    self._initialized = True
            
            def dispose(self):
                if self._connection:
                    self._connection.close()
                    self._connection = None
                    self._initialized = False
        ```
    """
    
    def __init__(self) -> None:
        """
        初始化生命周期状态
        
        子类应该调用此方法以确保正确的初始化。
        """
        self._initialized: bool = False

    @abstractmethod
    def initialize(self) -> None:
        """
        初始化服务
        
        执行服务初始化逻辑，如资源分配、配置加载、连接建立等。
        此方法只应该被调用一次，多次调用应该被忽略或抛出异常。
        
        Raises:
            InitializationException: 初始化失败时抛出
        """
        pass

    def start(self) -> None:
        """
        启动服务（可选）
        
        执行服务启动逻辑，如启动后台任务、开启监听等。
        默认实现为空，子类可以重写以提供启动功能。
        
        注意：此方法是可选的，不是所有服务都需要启动功能。
        """
        pass

    def stop(self) -> None:
        """
        停止服务（可选）
        
        执行服务停止逻辑，如停止后台任务、关闭监听等。
        默认实现为空，子类可以重写以提供停止功能。
        
        注意：此方法是可选的，不是所有服务都需要停止功能。
        """
        pass

    @abstractmethod
    def dispose(self) -> None:
        """
        释放服务资源
        
        执行资源清理逻辑，如关闭连接、释放内存、取消订阅等。
        此方法应该确保所有资源都被正确释放，即使发生异常。
        
        Raises:
            DisposalException: 释放失败时抛出
        """
        pass
    
    @property
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized
    
    @property
    def can_start(self) -> bool:
        """
        检查是否可以启动
        
        Returns:
            bool: 是否可以启动
        """
        return self._initialized and hasattr(self, 'start')
    
    @property
    def can_stop(self) -> bool:
        """
        检查是否可以停止
        
        Returns:
            bool: 是否可以停止
        """
        return self._initialized and hasattr(self, 'stop')


'''
生命周期管理器接口
'''

class ILifecycleManager(ABC):
    """
    生命周期管理器接口
    
    负责管理容器中所有服务的生命周期，包括初始化、启动、停止和释放。
    支持批量操作和事件通知。
    
    主要功能：
    - 批量生命周期管理
    - 依赖关系处理
    - 事件通知
    - 状态监控
    """
    
    @abstractmethod
    async def initialize_service(self, service_name: str) -> bool:
        """
        初始化单个服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否初始化成功
            
        Raises:
            ServiceNotFoundException: 服务不存在时抛出
            InitializationException: 初始化失败时抛出
        """
        pass
    
    @abstractmethod
    async def start_service(self, service_name: str) -> bool:
        """
        启动单个服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否启动成功
            
        Raises:
            ServiceNotFoundException: 服务不存在时抛出
            StartException: 启动失败时抛出
        """
        pass
    
    @abstractmethod
    async def stop_service(self, service_name: str) -> bool:
        """
        停止单个服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否停止成功
            
        Raises:
            ServiceNotFoundException: 服务不存在时抛出
            StopException: 停止失败时抛出
        """
        pass
    
    @abstractmethod
    async def dispose_service(self, service_name: str) -> bool:
        """
        释放单个服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否释放成功
            
        Raises:
            ServiceNotFoundException: 服务不存在时抛出
            DisposalException: 释放失败时抛出
        """
        pass
    
    @abstractmethod
    async def initialize_all_services(self) -> Dict[str, bool]:
        """
        初始化所有服务
        
        按照依赖关系顺序初始化所有已注册的服务。
        
        Returns:
            Dict[str, bool]: 服务名称到初始化结果的映射
            
        Note:
            失败的服务不会影响其他服务的初始化。
        """
        pass
    
    @abstractmethod
    async def start_all_services(self) -> Dict[str, bool]:
        """
        启动所有服务
        
        启动所有已初始化且支持启动的服务。
        
        Returns:
            Dict[str, bool]: 服务名称到启动结果的映射
            
        Note:
            失败的服务不会影响其他服务的启动。
        """
        pass
    
    @abstractmethod
    async def stop_all_services(self) -> Dict[str, bool]:
        """
        停止所有服务
        
        按照与启动相反的顺序停止所有正在运行的服务。
        
        Returns:
            Dict[str, bool]: 服务名称到停止结果的映射
            
        Note:
            失败的服务不会影响其他服务的停止。
        """
        pass
    
    @abstractmethod
    async def dispose_all_services(self) -> Dict[str, bool]:
        """
        释放所有服务
        
        按照与初始化相反的顺序释放所有服务。
        
        Returns:
            Dict[str, bool]: 服务名称到释放结果的映射
            
        Note:
            即使某些服务释放失败，也会尝试释放所有服务。
        """
        pass
    
    @abstractmethod
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """
        获取服务状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            Optional[ServiceStatus]: 服务状态，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_all_service_status(self) -> Dict[str, ServiceStatus]:
        """
        获取所有服务状态
        
        Returns:
            Dict[str, ServiceStatus]: 服务名称到状态的映射
        """
        pass
    
    @abstractmethod
    def get_services_by_status(self, status: ServiceStatus) -> List[str]:
        """
        根据状态获取服务列表
        
        Args:
            status: 服务状态
            
        Returns:
            List[str]: 处于指定状态的服务名称列表
        """
        pass
    
    @abstractmethod
    def register_lifecycle_event_handler(self, event_type: str, handler: Callable[[str], None]) -> None:
        """
        注册生命周期事件处理器
        
        Args:
            event_type: 事件类型（如 'initialized', 'started', 'stopped', 'disposed'）
            handler: 事件处理器函数，接收服务名称作为参数
            
        Raises:
            InvalidEventTypeException: 无效的事件类型时抛出
        """
        pass
    
    @abstractmethod
    def unregister_lifecycle_event_handler(self, event_type: str, handler: Callable[[str], None]) -> bool:
        """
        注销生命周期事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理器函数
            
        Returns:
            bool: 是否成功注销
        """
        pass
    
    @abstractmethod
    async def execute_lifecycle_phase(
        self, 
        phase: str, 
        service_names: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        执行生命周期阶段
        
        Args:
            phase: 生命周期阶段（'initialize', 'start', 'stop', 'dispose'）
            service_names: 要处理的服务名称列表，None表示所有服务
            
        Returns:
            Dict[str, bool]: 服务名称到执行结果的映射
            
        Raises:
            InvalidPhaseException: 无效的生命周期阶段时抛出
        """
        pass
    
    @abstractmethod
    def get_dependency_order(self, service_names: Optional[List[str]] = None) -> List[str]:
        """
        获取服务依赖顺序
        
        根据服务间的依赖关系，返回正确的初始化/释放顺序。
        
        Args:
            service_names: 要排序的服务名称列表，None表示所有服务
            
        Returns:
            List[str]: 按依赖顺序排列的服务名称列表
            
        Raises:
            CircularDependencyException: 存在循环依赖时抛出
        """
        pass


'''
生命周期事件接口
'''

class ILifecycleEventHandler(ABC):
    """
    生命周期事件处理器接口
    
    定义生命周期事件的处理契约。
    """
    
    @abstractmethod
    async def on_service_initializing(self, service_name: str) -> None:
        """
        服务初始化前事件
        
        Args:
            service_name: 服务名称
        """
        pass
    
    @abstractmethod
    async def on_service_initialized(self, service_name: str, success: bool) -> None:
        """
        服务初始化后事件
        
        Args:
            service_name: 服务名称
            success: 是否成功
        """
        pass
    
    @abstractmethod
    async def on_service_starting(self, service_name: str) -> None:
        """
        服务启动前事件
        
        Args:
            service_name: 服务名称
        """
        pass
    
    @abstractmethod
    async def on_service_started(self, service_name: str, success: bool) -> None:
        """
        服务启动后事件
        
        Args:
            service_name: 服务名称
            success: 是否成功
        """
        pass
    
    @abstractmethod
    async def on_service_stopping(self, service_name: str) -> None:
        """
        服务停止前事件
        
        Args:
            service_name: 服务名称
        """
        pass
    
    @abstractmethod
    async def on_service_stopped(self, service_name: str, success: bool) -> None:
        """
        服务停止后事件
        
        Args:
            service_name: 服务名称
            success: 是否成功
        """
        pass
    
    @abstractmethod
    async def on_service_disposing(self, service_name: str) -> None:
        """
        服务释放前事件
        
        Args:
            service_name: 服务名称
        """
        pass
    
    @abstractmethod
    async def on_service_disposed(self, service_name: str, success: bool) -> None:
        """
        服务释放后事件
        
        Args:
            service_name: 服务名称
            success: 是否成功
        """
        pass