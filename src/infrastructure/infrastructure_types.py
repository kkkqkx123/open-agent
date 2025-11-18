"""基础设施模块类型定义 - 保持向后兼容性"""

# 从新的核心位置重新导出类型以保持向后兼容性
from src.core.common.types import (
    T,
    ServiceFactory,
    ServiceLifetime,
    ServiceRegistration,
    CheckResult,
)

# 为了向后兼容，仍然保留这些类的引用
T = T
ServiceFactory = ServiceFactory
ServiceLifetime = ServiceLifetime
ServiceRegistration = ServiceRegistration
CheckResult = CheckResult
