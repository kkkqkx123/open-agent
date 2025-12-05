"""
依赖注入容器接口模块

提供依赖注入容器的完整接口定义，按照单一职责原则拆分为多个小接口。
"""

# 核心接口
from .core import (
    IDependencyContainer,
    ServiceRegistration,
    DependencyChain,
    ServiceStatus,
    ServiceLifetime,
)

# 生命周期管理接口
from .lifecycle import (
    ILifecycleAware,
    ILifecycleManager,
)

# 服务注册接口
from .registry import (
    IServiceRegistry,
)

# 服务解析接口
from .resolver import (
    IServiceResolver,
)

# 监控和分析接口
from .monitoring import (
    IServiceTracker,
    IPerformanceMonitor,
    IDependencyAnalyzer,
)

# 缓存和作用域接口
from .caching import (
    IServiceCache,
)

from .scoping import (
    IScopeManager,
)

# 异常处理接口
from .exceptions import (
    ContainerException,
    RegistrationError,
    ServiceNotFoundError,
    ServiceCreationError,
    CircularDependencyError,
    ValidationError,
    IExceptionHandler,
    DefaultExceptionHandler,
)

# 测试支持接口
from .testing import (
    ITestContainerManager,
    IMockServiceRegistry,
    ITestIsolationStrategy,
    DefaultTestIsolationStrategy,
    TestContainerManager,
    MockServiceRegistry,
)

# 统一导出
__all__ = [
    # 核心接口
    "IDependencyContainer",
    "ServiceRegistration",
    "DependencyChain",
    "ServiceStatus",
    "ServiceLifetime",
    
    # 生命周期管理
    "ILifecycleAware",
    "ILifecycleManager",
    
    # 服务注册
    "IServiceRegistry",
    
    # 服务解析
    "IServiceResolver",
    
    # 监控和分析
    "IServiceTracker",
    "IPerformanceMonitor",
    "IDependencyAnalyzer",
    
    # 缓存和作用域
    "IServiceCache",
    "IScopeManager",
    
    # 异常处理
    "ContainerException",
    "RegistrationError",
    "ServiceNotFoundError",
    "ServiceCreationError",
    "CircularDependencyError",
    "ValidationError",
    "IExceptionHandler",
    "DefaultExceptionHandler",
    
    # 测试支持
    "ITestContainerManager",
    "IMockServiceRegistry",
    "ITestIsolationStrategy",
    "DefaultTestIsolationStrategy",
    "TestContainerManager",
    "MockServiceRegistry",
]