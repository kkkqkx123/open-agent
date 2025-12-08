"""统一函数注册表

提供统一的节点函数、条件函数和触发器函数的注册、发现和管理功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass
from src.services.logger.injection import get_logger
import importlib
import inspect
from pathlib import Path

from .base_registry import BaseRegistry, TypedRegistry

if TYPE_CHECKING:
    from src.core.workflow.entities import WorkflowState

logger = get_logger(__name__)


class FunctionType(Enum):
    """函数类型枚举"""
    NODE_FUNCTION = "node_function"
    CONDITION_FUNCTION = "condition_function"
    TRIGGER_FUNCTION = "trigger_function"
    ROUTE_FUNCTION = "route_function"


@dataclass
class FunctionConfig:
    """函数配置"""
    name: str
    function_type: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_async: bool = False
    category: Optional[str] = None


@dataclass
class RegisteredFunction:
    """已注册的函数"""
    name: str
    function: Callable
    config: FunctionConfig
    is_builtin: bool = False


class FunctionRegistrationError(Exception):
    """函数注册异常"""
    pass


class FunctionDiscoveryError(Exception):
    """函数发现异常"""
    pass


class IFunctionRegistry(ABC):
    """函数注册表接口"""
    
    @abstractmethod
    def register_node_function(self, name: str, function: Callable) -> None:
        """注册节点函数"""
        pass
    
    @abstractmethod
    def register_condition_function(self, name: str, function: Callable) -> None:
        """注册条件函数"""
        pass
    
    @abstractmethod
    def register_trigger_function(self, name: str, function: Callable, config: FunctionConfig) -> None:
        """注册触发器函数"""
        pass
    
    @abstractmethod
    def get_node_function(self, name: str) -> Optional[Callable]:
        """获取节点函数"""
        pass
    
    @abstractmethod
    def get_condition_function(self, name: str) -> Optional[Callable]:
        """获取条件函数"""
        pass
    
    @abstractmethod
    def get_trigger_function(self, name: str) -> Optional[Callable]:
        """获取触发器函数"""
        pass
    
    @abstractmethod
    def list_node_functions(self) -> List[str]:
        """列出所有节点函数"""
        pass
    
    @abstractmethod
    def list_condition_functions(self) -> List[str]:
        """列出所有条件函数"""
        pass
    
    @abstractmethod
    def list_trigger_functions(self) -> List[str]:
        """列出所有触发器函数"""
        pass
    
    @abstractmethod
    def register_route_function(self, name: str, function: Callable) -> None:
        """注册路由函数"""
        pass
    
    @abstractmethod
    def get_route_function(self, name: str) -> Optional[Callable]:
        """获取路由函数"""
        pass
    
    @abstractmethod
    def list_route_functions(self) -> List[str]:
        """列出所有路由函数"""
        pass
    
    @abstractmethod
    def discover_functions(self, module_paths: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """自动发现并注册函数"""
        pass


class FunctionRegistry(BaseRegistry, IFunctionRegistry):
    """统一函数注册表
    
    管理节点函数、条件函数和触发器函数的注册、发现和获取。
    """
    
    def __init__(self, enable_auto_discovery: bool = False):
        """初始化函数注册表
        
        Args:
            enable_auto_discovery: 是否启用自动发现功能
        """
        super().__init__("function")
        self._node_functions: Dict[str, Callable] = {}
        self._condition_functions: Dict[str, Callable] = {}
        self._trigger_functions: Dict[str, RegisteredFunction] = {}
        self._route_functions: Dict[str, Callable] = {}
        self._enable_auto_discovery = enable_auto_discovery
        self._discovery_cache: Dict[str, Dict[str, List[str]]] = {}
        
        # 注册内置函数
        self._register_builtin_functions()
    
    def register_node_function(self, name: str, function: Callable) -> None:
        """注册节点函数
        
        Args:
            name: 函数名称
            function: 函数对象
            
        Raises:
            FunctionRegistrationError: 函数注册失败
        """
        self._validate_function_registration(name, function, FunctionType.NODE_FUNCTION)
        
        if name in self._node_functions:
            self._logger.warning(f"节点函数 '{name}' 已存在，将被覆盖")
        
        self._node_functions[name] = function
        self._logger.debug(f"注册节点函数: {name}")
    
    def register_condition_function(self, name: str, function: Callable) -> None:
        """注册条件函数
        
        Args:
            name: 函数名称
            function: 函数对象
            
        Raises:
            FunctionRegistrationError: 函数注册失败
        """
        self._validate_function_registration(name, function, FunctionType.CONDITION_FUNCTION)
        
        if name in self._condition_functions:
            self._logger.warning(f"条件函数 '{name}' 已存在，将被覆盖")
        
        self._condition_functions[name] = function
        self._logger.debug(f"注册条件函数: {name}")
    
    def register_trigger_function(self, name: str, function: Callable, config: FunctionConfig) -> None:
        """注册触发器函数
        
        Args:
            name: 函数名称
            function: 函数对象
            config: 函数配置
            
        Raises:
            FunctionRegistrationError: 函数注册失败
        """
        self._validate_function_registration(name, function, FunctionType.TRIGGER_FUNCTION)
        
        registered_func = RegisteredFunction(
            name=name,
            function=function,
            config=config,
            is_builtin=False
        )
        
        self._trigger_functions[name] = registered_func
        self._logger.debug(f"注册触发器函数: {name} (类型: {config.function_type})")
    
    def get_node_function(self, name: str) -> Optional[Callable]:
        """获取节点函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 节点函数，如果不存在返回None
        """
        return self._node_functions.get(name)
    
    def get_condition_function(self, name: str) -> Optional[Callable]:
        """获取条件函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 条件函数，如果不存在返回None
        """
        return self._condition_functions.get(name)
    
    def get_trigger_function(self, name: str) -> Optional[Callable]:
        """获取触发器函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 触发器函数，如果不存在返回None
        """
        registered_func = self._trigger_functions.get(name)
        return registered_func.function if registered_func else None
    
    def get_trigger_function_config(self, name: str) -> Optional[FunctionConfig]:
        """获取触发器函数配置
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[FunctionConfig]: 函数配置，如果不存在返回None
        """
        registered_func = self._trigger_functions.get(name)
        return registered_func.config if registered_func else None
    
    def list_node_functions(self) -> List[str]:
        """列出所有节点函数
        
        Returns:
            List[str]: 节点函数名称列表
        """
        return list(self._node_functions.keys())
    
    def list_condition_functions(self) -> List[str]:
        """列出所有条件函数
        
        Returns:
            List[str]: 条件函数名称列表
        """
        return list(self._condition_functions.keys())
    
    def list_trigger_functions(self) -> List[str]:
        """列出所有触发器函数
        
        Returns:
            List[str]: 触发器函数名称列表
        """
        return list(self._trigger_functions.keys())
    
    def register_route_function(self, name: str, function: Callable) -> None:
        """注册路由函数
        
        Args:
            name: 函数名称
            function: 函数对象
            
        Raises:
            FunctionRegistrationError: 函数注册失败
        """
        self._validate_function_registration(name, function, FunctionType.ROUTE_FUNCTION)
        
        if name in self._route_functions:
            self._logger.warning(f"路由函数 '{name}' 已存在，将被覆盖")
        
        self._route_functions[name] = function
        self._logger.debug(f"注册路由函数: {name}")
    
    def get_route_function(self, name: str) -> Optional[Callable]:
        """获取路由函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 路由函数，如果不存在返回None
        """
        return self._route_functions.get(name)
    
    def list_route_functions(self) -> List[str]:
        """列出所有路由函数
        
        Returns:
            List[str]: 路由函数名称列表
        """
        return list(self._route_functions.keys())
    
    def list_functions(self, function_type: Optional[FunctionType] = None) -> Dict[str, List[str]]:
        """列出已注册的函数
        
        Args:
            function_type: 函数类型过滤器，如果为None则返回所有函数
            
        Returns:
            Dict[str, List[str]]: 函数分类列表
        """
        result = {}
        
        if function_type is None or function_type == FunctionType.NODE_FUNCTION:
            result["nodes"] = self.list_node_functions()
        
        if function_type is None or function_type == FunctionType.CONDITION_FUNCTION:
            result["conditions"] = self.list_condition_functions()
        
        if function_type is None or function_type == FunctionType.TRIGGER_FUNCTION:
            result["triggers"] = self.list_trigger_functions()
        
        if function_type is None or function_type == FunctionType.ROUTE_FUNCTION:
            result["routes"] = self.list_route_functions()
        
        return result
    
    def unregister_node_function(self, name: str) -> bool:
        """注销节点函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._node_functions:
            del self._node_functions[name]
            self._logger.debug(f"注销节点函数: {name}")
            return True
        return False
    
    def unregister_condition_function(self, name: str) -> bool:
        """注销条件函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._condition_functions:
            del self._condition_functions[name]
            self._logger.debug(f"注销条件函数: {name}")
            return True
        return False
    
    def unregister_trigger_function(self, name: str) -> bool:
        """注销触发器函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._trigger_functions:
            del self._trigger_functions[name]
            self._logger.debug(f"注销触发器函数: {name}")
            return True
        return False
    
    def unregister_route_function(self, name: str) -> bool:
        """注销路由函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._route_functions:
            del self._route_functions[name]
            self._logger.debug(f"注销路由函数: {name}")
            return True
        return False
    
    def clear(self, function_type: Optional[FunctionType] = None) -> None:
        """清除注册的函数
        
        Args:
            function_type: 要清除的函数类型，如果为None则清除所有函数
        """
        if function_type is None or function_type == FunctionType.NODE_FUNCTION:
            self._node_functions.clear()
            self._logger.debug("清除所有节点函数")
        
        if function_type is None or function_type == FunctionType.CONDITION_FUNCTION:
            self._condition_functions.clear()
            self._logger.debug("清除所有条件函数")
        
        if function_type is None or function_type == FunctionType.TRIGGER_FUNCTION:
            self._trigger_functions.clear()
            self._logger.debug("清除所有触发器函数")
        
        if function_type is None or function_type == FunctionType.ROUTE_FUNCTION:
            self._route_functions.clear()
            self._logger.debug("清除所有路由函数")
        
        super().clear()
    
    def validate_function_exists(self, name: str, function_type: FunctionType) -> bool:
        """验证函数是否存在
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            bool: 函数是否存在
        """
        if function_type == FunctionType.NODE_FUNCTION:
            return name in self._node_functions
        elif function_type == FunctionType.CONDITION_FUNCTION:
            return name in self._condition_functions
        elif function_type == FunctionType.TRIGGER_FUNCTION:
            return name in self._trigger_functions
        elif function_type == FunctionType.ROUTE_FUNCTION:
            return name in self._route_functions
        return False
    
    def get_function_info(self, name: str, function_type: FunctionType) -> Optional[Dict[str, Any]]:
        """获取函数信息
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            Optional[Dict[str, Any]]: 函数信息，如果不存在返回None
        """
        if function_type == FunctionType.NODE_FUNCTION:
            function = self._node_functions.get(name)
        elif function_type == FunctionType.CONDITION_FUNCTION:
            function = self._condition_functions.get(name)
        elif function_type == FunctionType.TRIGGER_FUNCTION:
            registered_func = self._trigger_functions.get(name)
            function = registered_func.function if registered_func else None
        elif function_type == FunctionType.ROUTE_FUNCTION:
            function = self._route_functions.get(name)
        else:
            return None
        
        if function is None:
            return None
        
        try:
            sig = inspect.signature(function)
            doc = inspect.getdoc(function) or ""
            
            info = {
                "name": name,
                "type": function_type.value,
                "signature": str(sig),
                "doc": doc,
                "module": function.__module__,
                "is_async": inspect.iscoroutinefunction(function)
            }
            
            # 添加触发器函数特有信息
            if function_type == FunctionType.TRIGGER_FUNCTION and name in self._trigger_functions:
                registered_func = self._trigger_functions[name]
                info["config"] = registered_func.config
                info["is_builtin"] = registered_func.is_builtin
            
            return info
        except Exception as e:
            self._logger.warning(f"获取函数 '{name}' 信息失败: {e}")
            return {
                "name": name,
                "type": function_type.value,
                "error": str(e)
            }
    
    def discover_functions(self, module_paths: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """自动发现并注册函数
        
        Args:
            module_paths: 要扫描的模块路径列表，如果为None则使用默认路径
            
        Returns:
            Dict[str, List[str]]: 发现的函数统计信息
            
        Raises:
            FunctionDiscoveryError: 函数发现失败
        """
        if not self._enable_auto_discovery:
            self._logger.warning("自动发现功能未启用")
            return {"nodes": [], "conditions": [], "triggers": [], "routes": []}
        
        if module_paths is None:
            module_paths = [
                "src.workflow.nodes",
                "src.workflow.conditions",
                "src.infrastructure.graph.builtin_functions"
            ]
        
        discovered: Dict[str, List[str]] = {"nodes": [], "conditions": [], "triggers": [], "routes": []}
        
        for module_path in module_paths:
            try:
                module_functions = self._discover_from_module(module_path)
                discovered["nodes"].extend(module_functions["nodes"])
                discovered["conditions"].extend(module_functions["conditions"])
                discovered["triggers"].extend(module_functions["triggers"])
                discovered["routes"].extend(module_functions["routes"])
                
            except Exception as e:
                self._logger.error(f"从模块 '{module_path}' 发现函数失败: {e}")
                # 继续处理其他模块
                continue
        
        self._logger.info(f"自动发现完成: 节点函数 {len(discovered['nodes'])} 个, 条件函数 {len(discovered['conditions'])} 个, 触发器函数 {len(discovered['triggers'])} 个, 路由函数 {len(discovered['routes'])} 个")
        return discovered
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = super().get_stats()
        stats.update({
            "node_functions": len(self._node_functions),
            "condition_functions": len(self._condition_functions),
            "trigger_functions": len(self._trigger_functions),
            "route_functions": len(self._route_functions),
            "total_functions": len(self._node_functions) + len(self._condition_functions) + len(self._trigger_functions) + len(self._route_functions),
            "auto_discovery_enabled": self._enable_auto_discovery
        })
        return stats
    
    def get_function_schema(self, function_type: str, name: str) -> Dict[str, Any]:
        """获取函数配置Schema
        
        Args:
            function_type: 函数类型（node_function, condition_function, route_function）
            name: 函数名称
            
        Returns:
            Dict: 配置Schema
            
        Raises:
            ValueError: 函数不存在
        """
        if function_type == "node_function":
            function = self.get_node_function(name)
        elif function_type == "condition_function":
            function = self.get_condition_function(name)
        elif function_type == "route_function":
            function = self.get_route_function(name)
        else:
            raise ValueError(f"未知的函数类型: {function_type}")
        
        if function is None:
            raise ValueError(f"函数 '{name}' 不存在")
        
        # 对于普通函数，返回基本Schema
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def _validate_function_registration(self, name: str, function: Callable, function_type: FunctionType) -> None:
        """验证函数注册
        
        Args:
            name: 函数名称
            function: 函数对象
            function_type: 函数类型
            
        Raises:
            FunctionRegistrationError: 函数注册失败
        """
        if not name or not isinstance(name, str):
            raise FunctionRegistrationError("函数名称必须是非空字符串")
        
        if not callable(function):
            raise FunctionRegistrationError("注册的对象必须是可调用的")
        
        # 检查函数签名
        self._validate_function_signature(function, function_type)
    
    def _validate_function_signature(self, function: Callable, function_type: FunctionType) -> None:
        """验证函数签名
        
        Args:
            function: 函数对象
            function_type: 函数类型
            
        Raises:
            FunctionRegistrationError: 函数签名无效
        """
        try:
            sig = inspect.signature(function)
            params = list(sig.parameters.keys())
            
            if function_type in [FunctionType.NODE_FUNCTION, FunctionType.CONDITION_FUNCTION, FunctionType.ROUTE_FUNCTION]:
                # 节点函数、条件函数和路由函数应该至少接受一个参数（state）
                if len(params) < 1:
                    raise FunctionRegistrationError("函数必须至少接受一个参数（state）")
            
        except Exception as e:
            raise FunctionRegistrationError(f"函数签名验证失败: {e}")
    
    def _discover_from_module(self, module_path: str) -> Dict[str, List[str]]:
        """从模块发现函数
        
        Args:
            module_path: 模块路径
            
        Returns:
            Dict[str, List[str]]: 发现的函数列表
            
        Raises:
            FunctionDiscoveryError: 模块加载失败
        """
        # 检查缓存
        if module_path in self._discovery_cache:
            return self._discovery_cache[module_path]
        
        discovered: Dict[str, List[str]] = {"nodes": [], "conditions": [], "triggers": [], "routes": []}
        
        try:
            module = importlib.import_module(module_path)
            
            # 遍历模块中的所有成员
            for name, obj in inspect.getmembers(module):
                if not callable(obj) or name.startswith('_'):
                    continue
                
                # 检查是否是函数而不是类
                if inspect.isfunction(obj):
                    # 根据函数名称推断类型
                    if name.endswith('_node') or name.endswith('_function'):
                        self.register_node_function(name, obj)
                        discovered["nodes"].append(name)
                    elif name.endswith('_condition') or name.endswith('_router'):
                        self.register_condition_function(name, obj)
                        discovered["conditions"].append(name)
                    elif name.endswith('_route') or name.endswith('_router'):
                        self.register_route_function(name, obj)
                        discovered["routes"].append(name)
                    elif name.endswith('_trigger'):
                        # 为触发器函数创建默认配置
                        config = FunctionConfig(
                            name=name,
                            function_type="custom",
                            description=f"自动发现的触发器函数: {name}"
                        )
                        self.register_trigger_function(name, obj, config)
                        discovered["triggers"].append(name)
                    else:
                        # 默认作为节点函数
                        self.register_node_function(name, obj)
                        discovered["nodes"].append(name)
        
        except ImportError as e:
            raise FunctionDiscoveryError(f"无法导入模块 '{module_path}': {e}")
        except Exception as e:
            raise FunctionDiscoveryError(f"扫描模块 '{module_path}' 时发生错误: {e}")
        
        # 缓存结果
        self._discovery_cache[module_path] = discovered
        return discovered
    
    def _register_builtin_functions(self) -> None:
        """注册内置函数"""
        try:
            # 尝试导入内置函数模块
            from . import builtin_functions  # type: ignore[import-not-found]
            
            # 注册内置节点函数
            builtin_nodes = getattr(builtin_functions, 'BUILTIN_NODE_FUNCTIONS', {})
            for name, func in builtin_nodes.items():
                self.register_node_function(name, func)
            
            # 注册内置条件函数
            builtin_conditions = getattr(builtin_functions, 'BUILTIN_CONDITION_FUNCTIONS', {})
            for name, func in builtin_conditions.items():
                self.register_condition_function(name, func)
            
            # 注册内置路由函数
            builtin_routes = getattr(builtin_functions, 'BUILTIN_ROUTE_FUNCTIONS', {})
            for name, func in builtin_routes.items():
                self.register_route_function(name, func)
            
            # 注册内置触发器函数
            builtin_triggers = getattr(builtin_functions, 'BUILTIN_TRIGGER_FUNCTIONS', {})
            for name, (func, config) in builtin_triggers.items():
                self.register_trigger_function(name, func, config)
            
            self._logger.debug("内置函数注册完成")
            
        except (ImportError, ModuleNotFoundError):
            self._logger.debug("内置函数模块不存在，跳过内置函数注册")
        except Exception as e:
            self._logger.warning(f"注册内置函数失败: {e}")


# 全局函数注册表实例
_global_function_registry: Optional[FunctionRegistry] = None


def get_global_function_registry() -> FunctionRegistry:
    """获取全局函数注册表
    
    Returns:
        FunctionRegistry: 全局函数注册表
    """
    global _global_function_registry
    if _global_function_registry is None:
        _global_function_registry = FunctionRegistry()
    return _global_function_registry


def reset_global_function_registry() -> None:
    """重置全局函数注册表（用于测试）"""
    global _global_function_registry
    _global_function_registry = None