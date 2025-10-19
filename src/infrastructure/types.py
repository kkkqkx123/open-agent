"""基础设施模块类型定义"""

from typing import TypeVar, Type, Dict, Any, Callable, Optional, Union

# 泛型类型变量
T = TypeVar("T")

# 服务工厂函数类型
ServiceFactory = Callable[[], Any]


# 服务生命周期类型
class ServiceLifetime:
    """服务生命周期枚举"""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


# 服务注册信息
class ServiceRegistration:
    """服务注册信息"""

    def __init__(
        self,
        implementation: Type,
        lifetime: str = ServiceLifetime.SINGLETON,
        factory: Optional[ServiceFactory] = None,
        instance: Optional[Any] = None,
    ):
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance = instance


# 环境检查结果
class CheckResult:
    """环境检查结果"""

    def __init__(
        self,
        component: str,
        status: str,  # "PASS", "WARNING", "ERROR"
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.component = component
        self.status = status
        self.message = message
        self.details = details or {}

    def is_pass(self) -> bool:
        """检查是否通过"""
        return self.status == "PASS"

    def is_warning(self) -> bool:
        """检查是否为警告"""
        return self.status == "WARNING"

    def is_error(self) -> bool:
        """检查是否为错误"""
        return self.status == "ERROR"
