"""工作流注册表模块

提供统一的工作流组件注册表实现，支持依赖注入。
"""

from .base_registry import IRegistry, BaseRegistry, TypedRegistry
from .node_registry import NodeRegistry, BaseNode, node
from .function_registry import (
    FunctionRegistry, 
    FunctionType, 
    FunctionConfig, 
    RegisteredFunction,
    FunctionRegistrationError,
    FunctionDiscoveryError,
    IFunctionRegistry,
    get_global_function_registry,
    reset_global_function_registry
)
from .hook_registry import HookRegistry, HookRegistration, IHookRegistry
from .plugin_registry import PluginRegistry, IPluginRegistry
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
from .registry_factory import (
    RegistryFactory,
    RegistryBuilder,
    create_registry,
    create_registry_with_auto_discovery
)

__all__ = [
    # 基础接口和类
    "IRegistry",
    "BaseRegistry", 
    "TypedRegistry",
    
    # 节点注册表
    "NodeRegistry",
    "BaseNode",
    "node",
    
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
    
    # 工厂和构建器
    "RegistryFactory",
    "RegistryBuilder",
    "create_registry",
    "create_registry_with_auto_discovery",
]