"""函数注册表

提供统一的节点函数和条件函数注册、发现和管理功能。
"""

from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from src.interfaces.dependency_injection import get_logger
import importlib
import inspect


logger = get_logger(__name__)


class FunctionType(Enum):
    """函数类型枚举"""
    NODE_FUNCTION = "node_function"
    CONDITION_FUNCTION = "condition_function"


class FunctionRegistrationError(Exception):
    """函数注册异常"""
    pass


class FunctionDiscoveryError(Exception):
    """函数发现异常"""
    pass


class FunctionRegistry:
    """函数注册表
    
    统一管理节点函数和条件函数的注册、发现和获取。
    """
    
    def __init__(self, enable_auto_discovery: bool = False):
        """初始化函数注册表
        
        Args:
            enable_auto_discovery: 是否启用自动发现功能
        """
        self._node_functions: Dict[str, Callable] = {}
        self._condition_functions: Dict[str, Callable] = {}
        self._enable_auto_discovery = enable_auto_discovery
        self._discovery_cache: Dict[str, Dict[str, List[str]]] = {}
        
        # 注册内置函数
        self._register_builtin_functions()
    
    def register(self, name: str, function: Callable, function_type: FunctionType) -> None:
        """注册函数
        
        Args:
            name: 函数名称（配置文件中使用的名称）
            function: 函数对象
            function_type: 函数类型
            
        Raises:
            FunctionRegistrationError: 函数名称已存在或函数类型无效
        """
        if not name or not isinstance(name, str):
            raise FunctionRegistrationError("函数名称必须是非空字符串")
        
        if not callable(function):
            raise FunctionRegistrationError("注册的对象必须是可调用的")
        
        if not isinstance(function_type, FunctionType):
            raise FunctionRegistrationError("函数类型必须是 FunctionType 枚举值")
        
        # 检查函数签名
        self._validate_function_signature(function, function_type)
        
        if function_type == FunctionType.NODE_FUNCTION:
            if name in self._node_functions:
                logger.warning(f"节点函数 '{name}' 已存在，将被覆盖")
            self._node_functions[name] = function
            logger.debug(f"注册节点函数: {name}")
            
        elif function_type == FunctionType.CONDITION_FUNCTION:
            if name in self._condition_functions:
                logger.warning(f"条件函数 '{name}' 已存在，将被覆盖")
            self._condition_functions[name] = function
            logger.debug(f"注册条件函数: {name}")
    
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
    
    def unregister(self, name: str, function_type: FunctionType) -> bool:
        """注销函数
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            bool: 是否成功注销
        """
        if function_type == FunctionType.NODE_FUNCTION:
            if name in self._node_functions:
                del self._node_functions[name]
                logger.debug(f"注销节点函数: {name}")
                return True
                
        elif function_type == FunctionType.CONDITION_FUNCTION:
            if name in self._condition_functions:
                del self._condition_functions[name]
                logger.debug(f"注销条件函数: {name}")
                return True
        
        return False
    
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
            logger.warning("自动发现功能未启用")
            return {"nodes": [], "conditions": []}
        
        if module_paths is None:
            module_paths = [
                "src.workflow.nodes",
                "src.workflow.conditions",
                "src.infrastructure.graph.builtin_functions"
            ]
        
        discovered: Dict[str, List[str]] = {"nodes": [], "conditions": []}
        
        for module_path in module_paths:
            try:
                module_functions = self._discover_from_module(module_path)
                discovered["nodes"].extend(module_functions["nodes"])
                discovered["conditions"].extend(module_functions["conditions"])
                
            except Exception as e:
                logger.error(f"从模块 '{module_path}' 发现函数失败: {e}")
                # 继续处理其他模块
                continue
        
        logger.info(f"自动发现完成: 节点函数 {len(discovered['nodes'])} 个, 条件函数 {len(discovered['conditions'])} 个")
        return discovered
    
    def list_functions(self, function_type: Optional[FunctionType] = None) -> Dict[str, List[str]]:
        """列出已注册的函数
        
        Args:
            function_type: 函数类型过滤器，如果为None则返回所有函数
            
        Returns:
            Dict[str, List[str]]: 函数分类列表
        """
        result = {}
        
        if function_type is None or function_type == FunctionType.NODE_FUNCTION:
            result["nodes"] = list(self._node_functions.keys())
        
        if function_type is None or function_type == FunctionType.CONDITION_FUNCTION:
            result["conditions"] = list(self._condition_functions.keys())
        
        return result
    
    def clear(self, function_type: Optional[FunctionType] = None) -> None:
        """清除注册的函数
        
        Args:
            function_type: 要清除的函数类型，如果为None则清除所有函数
        """
        if function_type is None or function_type == FunctionType.NODE_FUNCTION:
            self._node_functions.clear()
            logger.debug("清除所有节点函数")
        
        if function_type is None or function_type == FunctionType.CONDITION_FUNCTION:
            self._condition_functions.clear()
            logger.debug("清除所有条件函数")
    
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
        else:
            return None
        
        if function is None:
            return None
        
        try:
            sig = inspect.signature(function)
            doc = inspect.getdoc(function) or ""
            
            return {
                "name": name,
                "type": function_type.value,
                "signature": str(sig),
                "doc": doc,
                "module": function.__module__,
                "file": inspect.getfile(function) if hasattr(function, '__file__') else None
            }
        except Exception as e:
            logger.warning(f"获取函数 '{name}' 信息失败: {e}")
            return {
                "name": name,
                "type": function_type.value,
                "error": str(e)
            }
    
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
            
            if function_type == FunctionType.NODE_FUNCTION:
                # 节点函数应该至少接受一个参数（state）
                if len(params) < 1:
                    raise FunctionRegistrationError("节点函数必须至少接受一个参数（state）")
                
            elif function_type == FunctionType.CONDITION_FUNCTION:
                # 条件函数应该至少接受一个参数（state）
                if len(params) < 1:
                    raise FunctionRegistrationError("条件函数必须至少接受一个参数（state）")
        
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
        
        discovered: Dict[str, List[str]] = {"nodes": [], "conditions": []}
        
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
                        self.register(name, obj, FunctionType.NODE_FUNCTION)
                        discovered["nodes"].append(name)
                    elif name.endswith('_condition') or name.endswith('_router'):
                        self.register(name, obj, FunctionType.CONDITION_FUNCTION)
                        discovered["conditions"].append(name)
                    else:
                        # 默认作为节点函数
                        self.register(name, obj, FunctionType.NODE_FUNCTION)
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
            rest_nodes = getattr(builtin_functions, 'BUILTIN_NODE_FUNCTIONS', {})
            for name, func in rest_nodes.items():
                self.register(name, func, FunctionType.NODE_FUNCTION)
            
            # 注册内置条件函数
            rest_conditions = getattr(builtin_functions, 'BUILTIN_CONDITION_FUNCTIONS', {})
            for name, func in rest_conditions.items():
                self.register(name, func, FunctionType.CONDITION_FUNCTION)
            
            logger.debug("内置函数注册完成")
            
        except (ImportError, ModuleNotFoundError):
            logger.debug("内置函数模块不存在，跳过内置函数注册")
        except Exception as e:
            logger.warning(f"注册内置函数失败: {e}")


# 全局函数注册表实例
_global_registry: Optional[FunctionRegistry] = None


def get_global_function_registry() -> FunctionRegistry:
    """获取全局函数注册表
    
    Returns:
        FunctionRegistry: 全局函数注册表
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = FunctionRegistry()
    return _global_registry


def register_node_function(name: str, function: Callable) -> None:
    """注册节点函数到全局注册表（已弃用）
    
    Args:
        name: 函数名称
        function: 函数对象
        
    Raises:
        DeprecationWarning: 此函数已被弃用，请使用依赖注入方式
    """
    import warnings
    warnings.warn(
        "register_node_function 已被弃用，请使用依赖注入方式注册节点函数",
        DeprecationWarning,
        stacklevel=2
    )
    get_global_function_registry().register(name, function, FunctionType.NODE_FUNCTION)


def register_condition_function(name: str, function: Callable) -> None:
    """注册条件函数到全局注册表（已弃用）
    
    Args:
        name: 函数名称
        function: 函数对象
        
    Raises:
        DeprecationWarning: 此函数已被弃用，请使用依赖注入方式
    """
    import warnings
    warnings.warn(
        "register_condition_function 已被弃用，请使用依赖注入方式注册条件函数",
        DeprecationWarning,
        stacklevel=2
    )
    get_global_function_registry().register(name, function, FunctionType.CONDITION_FUNCTION)


def get_node_function(name: str) -> Optional[Callable]:
    """从全局注册表获取节点函数（已弃用）
    
    Args:
        name: 函数名称
        
    Returns:
        Optional[Callable]: 节点函数
        
    Raises:
        DeprecationWarning: 此函数已被弃用，请使用依赖注入方式
    """
    import warnings
    warnings.warn(
        "get_node_function 已被弃用，请使用依赖注入方式获取节点函数",
        DeprecationWarning,
        stacklevel=2
    )
    return get_global_function_registry().get_node_function(name)


def get_condition_function(name: str) -> Optional[Callable]:
    """从全局注册表获取条件函数（已弃用）
    
    Args:
        name: 函数名称
        
    Returns:
        Optional[Callable]: 条件函数
        
    Raises:
        DeprecationWarning: 此函数已被弃用，请使用依赖注入方式
    """
    import warnings
    warnings.warn(
        "get_condition_function 已被弃用，请使用依赖注入方式获取条件函数",
        DeprecationWarning,
        stacklevel=2
    )
    return get_global_function_registry().get_condition_function(name)
