"""工作流注册表模块

提供统一的工作流组件注册表实现，支持依赖注入。

注册器类型：
├─ BaseRegistry: 基础注册表
├─ NodeRegistry: 节点注册表
├─ EdgeRegistry: 边注册表
├─ FunctionRegistry: 函数注册表（节点函数、条件函数、触发器函数）
├─ HookRegistry: Hook注册表
├─ PluginRegistry: 插件注册表
├─ TriggerRegistry: 触发器注册表
└─ UnifiedRegistry: 统一注册表

使用方式：
1. 通过依赖注入获取注册器实例
2. 注册相应的类型或实例
3. 通过注册器查询和管理已注册的项目
"""

from .base_registry import IRegistry, BaseRegistry, TypedRegistry
from .node_registry import NodeRegistry, BaseNode, node
from .edge_registry import EdgeRegistry, edge
from .function_registry import (
    FunctionRegistry,
    get_global_function_registry,
    reset_global_function_registry
)

# 从接口层导入
from src.interfaces.workflow.functions import FunctionType
from src.interfaces.workflow.registry import IFunctionRegistry

# 创建缺失的类
class FunctionConfig:
    """函数配置"""
    pass

class RegisteredFunction:
    """已注册函数"""
    pass

class FunctionRegistrationError(Exception):
    """函数注册错误"""
    pass

class FunctionDiscoveryError(Exception):
    """函数发现错误"""
    pass
from .hook_registry import HookRegistry, HookRegistration, IHookRegistry
from .plugin_registry import PluginRegistry

# 从接口层导入
# from src.interfaces.workflow.registry import IPluginRegistry  # 接口不存在，创建简单替代

# 创建缺失的接口
from abc import ABC, abstractmethod

class IPluginRegistry(ABC):
    """插件注册表接口"""
    @abstractmethod
    def register(self, plugin: Any) -> None:
        pass
from .trigger_registry import (
    TriggerRegistry,
    TriggerConfig,
    RegisteredTrigger
)
from .registry import (
    UnifiedRegistry,
    RegistryManager,
    get_global_unified_registry,
    reset_global_unified_registry,
    create_unified_registry,
    create_registry_manager
)
# registry_factory.py 已删除，这些功能现在通过依赖注入容器提供

__all__ = [
    # 基础接口和类
    "IRegistry",
    "BaseRegistry",
    "TypedRegistry",
    
    # 节点注册表
    "NodeRegistry",
    "BaseNode",
    "node",
    
    # 边注册表
    "EdgeRegistry",
    "edge",
    
    # 函数注册表
    "FunctionRegistry",
    "FunctionType",
    "FunctionConfig",
    "RegisteredFunction",
    "FunctionRegistrationError",
    "FunctionDiscoveryError",
    "IFunctionRegistry",
    "get_global_function_registry",
    "reset_global_function_registry",
    
    # Hook注册表
    "HookRegistry",
    "HookRegistration",
    "IHookRegistry",
    
    # 插件注册表
    "PluginRegistry",
    "IPluginRegistry",
    
    # 触发器注册表
    "TriggerRegistry",
    "TriggerConfig",
    "RegisteredTrigger",
    
    # 统一注册表
    "UnifiedRegistry",
    "RegistryManager",
    "get_global_unified_registry",
    "reset_global_unified_registry",
    "create_unified_registry",
    "create_registry_manager",
    
    # 注意：工厂和构建器已删除，现在使用依赖注入容器
]