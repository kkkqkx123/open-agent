现在我来创建配置驱动的函数工厂，这将整合所有之前设计的系统：

## 配置驱动的函数工厂设计

### 1. 统一函数工厂配置

```yaml
# configs/function_factory.yaml
metadata:
  name: "function_factory_config"
  version: "1.0.0"
  description: "统一函数工厂配置"
  author: "system"

# 工厂配置
factory_config:
  # 缓存配置
  cache_enabled: true
  cache_size: 10000
  cache_ttl: 3600
  
  # 预加载配置
  preload_enabled: true
  preload_functions:
    - "llm_node"
    - "tool_node"
    - "has_tool_calls"
    - "is_complete"
  
  # 热重载配置
  hot_reload_enabled: false
  hot_reload_interval: 60
  
  # 错误处理配置
  error_handling:
    fallback_enabled: true
    retry_attempts: 3
    retry_delay: 1.0
    log_errors: true
  
  # 性能配置
  lazy_loading: true
  batch_loading: true
  batch_size: 50
  async_loading: false

# 函数类型映射
function_types:
  node_functions:
    loader_class: "src.core.workflow.functions.node_loader:NodeFunctionLoader"
    config_file: "configs/builtin_functions/node_functions.yaml"
    registry_class: "src.core.workflow.functions.node_registry:NodeFunctionRegistry"
    
  condition_functions:
    loader_class: "src.core.workflow.functions.condition_loader:ConditionFunctionLoader"
    config_file: "configs/builtin_functions/condition_functions.yaml"
    registry_class: "src.core.workflow.functions.condition_registry:ConditionFunctionRegistry"
    
  edge_functions:
    loader_class: "src.core.workflow.functions.edge_loader:EdgeFunctionLoader"
    config_file: "configs/builtin_functions/edge_functions.yaml"
    registry_class: "src.core.workflow.functions.edge_registry:EdgeFunctionRegistry"

# 管理器类型映射
manager_types:
  iteration_managers:
    factory_class: "src.core.workflow.iteration.manager_factory:IterationManagerFactory"
    config_file: "configs/iteration_managers.yaml"
    
  state_managers:
    factory_class: "src.core.workflow.state.manager_factory:StateManagerFactory"
    config_file: "configs/state_managers.yaml"
    
  checkpoint_managers:
    factory_class: "src.core.workflow.checkpoint.manager_factory:CheckpointManagerFactory"
    config_file: "configs/checkpoint_managers.yaml"

# 适配器类型映射
adapter_types:
  state_adapters:
    factory_class: "src.core.workflow.adapters.state_adapter_factory:StateAdapterFactory"
    config_file: "configs/state_adapters.yaml"
    
  collaboration_adapters:
    factory_class: "src.core.workflow.adapters.collaboration_adapter_factory:CollaborationAdapterFactory"
    config_file: "configs/collaboration_adapters.yaml"

# 插件配置
plugins:
  enabled: true
  plugin_directories:
    - "plugins/functions"
    - "plugins/managers"
    - "plugins/adapters"
  auto_discover: true
  load_order: ["builtin", "custom"]

# 验证规则
validation_rules:
  - field: "function_types.*.loader_class"
    rule_type: "required"
    message: "函数类型必须指定加载器类"
  - field: "manager_types.*.factory_class"
    rule_type: "required"
    message: "管理器类型必须指定工厂类"
  - field: "factory_config.cache_size"
    rule_type: "range"
    value: [100, 100000]
    message: "缓存大小必须在100-100000之间"
```

### 2. 统一函数工厂实现

```python
# src/core/workflow/factory/unified_function_factory.py
from typing import Dict, Any, Optional, Callable, List, Union, Type
from abc import ABC, abstractmethod
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class FunctionType(Enum):
    """函数类型枚举"""
    NODE_FUNCTION = "node_function"
    CONDITION_FUNCTION = "condition_function"
    EDGE_FUNCTION = "edge_function"

class ManagerType(Enum):
    """管理器类型枚举"""
    ITERATION_MANAGER = "iteration_manager"
    STATE_MANAGER = "state_manager"
    CHECKPOINT_MANAGER = "checkpoint_manager"

class AdapterType(Enum):
    """适配器类型枚举"""
    STATE_ADAPTER = "state_adapter"
    COLLABORATION_ADAPTER = "collaboration_adapter"

class IFunctionFactory(ABC):
    """函数工厂接口"""
    
    @abstractmethod
    def create_function(self, function_name: str, function_type: FunctionType, **kwargs) -> Optional[Callable]:
        """创建函数"""
        pass
    
    @abstractmethod
    def create_manager(self, manager_type: ManagerType, manager_name: str, **kwargs) -> Any:
        """创建管理器"""
        pass
    
    @abstractmethod
    def create_adapter(self, adapter_type: AdapterType, adapter_name: str, **kwargs) -> Any:
        """创建适配器"""
        pass
    
    @abstractmethod
    def list_functions(self, function_type: FunctionType) -> List[str]:
        """列出函数"""
        pass
    
    @abstractmethod
    def list_managers(self, manager_type: ManagerType) -> List[str]:
        """列出管理器"""
        pass
    
    @abstractmethod
    def list_adapters(self, adapter_type: AdapterType) -> List[str]:
        """列出适配器"""
        pass

class UnifiedFunctionFactory(IFunctionFactory):
    """统一函数工厂实现"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._factory_config = self._load_factory_config()
        
        # 初始化缓存
        self._function_cache: Dict[str, Callable] = {}
        self._manager_cache: Dict[str, Any] = {}
        self._adapter_cache: Dict[str, Any] = {}
        
        # 初始化加载器和工厂
        self._loaders: Dict[FunctionType, Any] = {}
        self._manager_factories: Dict[ManagerType, Any] = {}
        self._adapter_factories: Dict[AdapterType, Any] = {}
        
        # 初始化组件
        self._initialize_components()
        
        # 预加载函数
        if self._factory_config.get("preload_enabled", True):
            self._preload_functions()
    
    def create_function(self, function_name: str, function_type: FunctionType, **kwargs) -> Optional[Callable]:
        """创建函数"""
        cache_key = f"{function_type.value}:{function_name}"
        
        # 检查缓存
        if self._factory_config.get("cache_enabled", True) and cache_key in self._function_cache:
            return self._function_cache[cache_key]
        
        try:
            # 获取对应的加载器
            loader = self._loaders.get(function_type)
            if not loader:
                logger.error(f"未找到函数类型加载器: {function_type}")
                return None
            
            # 加载函数
            function = loader.load_function(function_name, **kwargs)
            
            if function:
                # 缓存函数
                if self._factory_config.get("cache_enabled", True):
                    self._function_cache[cache_key] = function
                
                logger.debug(f"成功创建函数: {function_name} ({function_type.value})")
                return function
            else:
                # 尝试回退
                if self._factory_config.get("error_handling", {}).get("fallback_enabled", True):
                    fallback_function = self._create_fallback_function(function_name, function_type)
                    if fallback_function:
                        if self._factory_config.get("cache_enabled", True):
                            self._function_cache[cache_key] = fallback_function
                        logger.warning(f"使用回退函数: {function_name} ({function_type.value})")
                        return fallback_function
                
                logger.error(f"无法创建函数: {function_name} ({function_type.value})")
                return None
                
        except Exception as e:
            logger.error(f"创建函数失败 {function_name} ({function_type.value}): {e}")
            
            # 重试逻辑
            error_handling = self._factory_config.get("error_handling", {})
            retry_attempts = error_handling.get("retry_attempts", 3)
            retry_delay = error_handling.get("retry_delay", 1.0)
            
            for attempt in range(retry_attempts):
                try:
                    import time
                    time.sleep(retry_delay)
                    return self.create_function(function_name, function_type, **kwargs)
                except Exception as retry_error:
                    logger.error(f"重试创建函数失败 {function_name} (尝试 {attempt + 1}/{retry_attempts}): {retry_error}")
            
            return None
    
    def create_manager(self, manager_type: ManagerType, manager_name: str, **kwargs) -> Any:
        """创建管理器"""
        cache_key = f"{manager_type.value}:{manager_name}"
        
        # 检查缓存
        if self._factory_config.get("cache_enabled", True) and cache_key in self._manager_cache:
            return self._manager_cache[cache_key]
        
        try:
            # 获取对应的工厂
            factory = self._manager_factories.get(manager_type)
            if not factory:
                logger.error(f"未找到管理器类型工厂: {manager_type}")
                return None
            
            # 创建管理器
            manager = factory.create_manager(manager_name, **kwargs)
            
            if manager:
                # 缓存管理器
                if self._factory_config.get("cache_enabled", True):
                    self._manager_cache[cache_key] = manager
                
                logger.debug(f"成功创建管理器: {manager_name} ({manager_type.value})")
                return manager
            else:
                logger.error(f"无法创建管理器: {manager_name} ({manager_type.value})")
                return None
                
        except Exception as e:
            logger.error(f"创建管理器失败 {manager_name} ({manager_type.value}): {e}")
            return None
    
    def create_adapter(self, adapter_type: AdapterType, adapter_name: str, **kwargs) -> Any:
        """创建适配器"""
        cache_key = f"{adapter_type.value}:{adapter_name}"
        
        # 检查缓存
        if self._factory_config.get("cache_enabled", True) and cache_key in self._adapter_cache:
            return self._adapter_cache[cache_key]
        
        try:
            # 获取对应的工厂
            factory = self._adapter_factories.get(adapter_type)
            if not factory:
                logger.error(f"未找到适配器类型工厂: {adapter_type}")
                return None
            
            # 创建适配器
            adapter = factory.create_adapter(adapter_name, **kwargs)
            
            if adapter:
                # 缓存适配器
                if self._factory_config.get("cache_enabled", True):
                    self._adapter_cache[cache_key] = adapter
                
                logger.debug(f"成功创建适配器: {adapter_name} ({adapter_type.value})")
                return adapter
            else:
                logger.error(f"无法创建适配器: {adapter_name} ({adapter_type.value})")
                return None
                
        except Exception as e:
            logger.error(f"创建适配器失败 {adapter_name} ({adapter_type.value}): {e}")
            return None
    
    def list_functions(self, function_type: FunctionType) -> List[str]:
        """列出函数"""
        loader = self._loaders.get(function_type)
        if loader:
            return loader.list_functions()
        return []
    
    def list_managers(self, manager_type: ManagerType) -> List[str]:
        """列出管理器"""
        factory = self._manager_factories.get(manager_type)
        if factory:
            return factory.list_available_managers()
        return []
    
    def list_adapters(self, adapter_type: AdapterType) -> List[str]:
        """列出适配器"""
        factory = self._adapter_factories.get(adapter_type)
        if factory:
            return factory.list_available_adapters()
        return []
    
    def get_default_manager(self, manager_type: ManagerType) -> Any:
        """获取默认管理器"""
        factory = self._manager_factories.get(manager_type)
        if factory:
            return factory.get_default_manager()
        return None
    
    def get_default_adapter(self, adapter_type: AdapterType) -> Any:
        """获取默认适配器"""
        factory = self._adapter_factories.get(adapter_type)
        if factory:
            return factory.get_default_adapter()
        return None
    
    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """清除缓存"""
        if cache_type is None or cache_type == "functions":
            self._function_cache.clear()
        if cache_type is None or cache_type == "managers":
            self._manager_cache.clear()
        if cache_type is None or cache_type == "adapters":
            self._adapter_cache.clear()
        
        logger.debug(f"清除缓存: {cache_type or 'all'}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "cache_statistics": {
                "functions_cached": len(self._function_cache),
                "managers_cached": len(self._manager_cache),
                "adapters_cached": len(self._adapter_cache),
                "cache_enabled": self._factory_config.get("cache_enabled", True),
                "cache_size": self._factory_config.get("cache_size", 10000)
            },
            "loader_statistics": {
                "node_functions_count": len(self.list_functions(FunctionType.NODE_FUNCTION)),
                "condition_functions_count": len(self.list_functions(FunctionType.CONDITION_FUNCTION)),
                "edge_functions_count": len(self.list_functions(FunctionType.EDGE_FUNCTION))
            },
            "manager_statistics": {
                "iteration_managers_count": len(self.list_managers(ManagerType.ITERATION_MANAGER)),
                "state_managers_count": len(self.list_managers(ManagerType.STATE_MANAGER)),
                "checkpoint_managers_count": len(self.list_managers(ManagerType.CHECKPOINT_MANAGER))
            },
            "adapter_statistics": {
                "state_adapters_count": len(self.list_adapters(AdapterType.STATE_ADAPTER)),
                "collaboration_adapters_count": len(self.list_adapters(AdapterType.COLLABORATION_ADAPTER))
            }
        }
    
    def _load_factory_config(self) -> Dict[str, Any]:
        """加载工厂配置"""
        try:
            return self.config_manager.load_config("configs/function_factory.yaml")
        except Exception as e:
            logger.error(f"加载工厂配置失败: {e}")
            return {}
    
    def _initialize_components(self) -> None:
        """初始化组件"""
        # 初始化函数加载器
        function_types = self._factory_config.get("function_types", {})
        for type_name, type_config in function_types.items():
            try:
                function_type = FunctionType(type_name)
                loader_class = self._import_class(type_config["loader_class"])
                self._loaders[function_type] = loader_class(self.config_manager)
            except Exception as e:
                logger.error(f"初始化函数加载器失败 {type_name}: {e}")
        
        # 初始化管理器工厂
        manager_types = self._factory_config.get("manager_types", {})
        for type_name, type_config in manager_types.items():
            try:
                manager_type = ManagerType(type_name)
                factory_class = self._import_class(type_config["factory_class"])
                self._manager_factories[manager_type] = factory_class(self.config_manager)
            except Exception as e:
                logger.error(f"初始化管理器工厂失败 {type_name}: {e}")
        
        # 初始化适配器工厂
        adapter_types = self._factory_config.get("adapter_types", {})
        for type_name, type_config in adapter_types.items():
            try:
                adapter_type = AdapterType(type_name)
                factory_class = self._import_class(type_config["factory_class"])
                self._adapter_factories[adapter_type] = factory_class(self.config_manager)
            except Exception as e:
                logger.error(f"初始化适配器工厂失败 {type_name}: {e}")
    
    def _preload_functions(self) -> None:
        """预加载函数"""
        preload_functions = self._factory_config.get("preload_functions", [])
        
        for function_name in preload_functions:
            # 尝试作为节点函数加载
            function = self.create_function(function_name, FunctionType.NODE_FUNCTION)
            if not function:
                # 尝试作为条件函数加载
                function = self.create_function(function_name, FunctionType.CONDITION_FUNCTION)
            
            if function:
                logger.debug(f"预加载函数成功: {function_name}")
            else:
                logger.warning(f"预加载函数失败: {function_name}")
    
    def _create_fallback_function(self, function_name: str, function_type: FunctionType) -> Optional[Callable]:
        """创建回退函数"""
        if function_type == FunctionType.NODE_FUNCTION:
            # 节点函数回退
            def fallback_node_function(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
                logger.warning(f"使用回退节点函数: {function_name}")
                return state
            return fallback_node_function
        
        elif function_type == FunctionType.CONDITION_FUNCTION:
            # 条件函数回退
            def fallback_condition_function(state: Dict[str, Any]) -> str:
                logger.warning(f"使用回退条件函数: {function_name}")
                return "continue"
            return fallback_condition_function
        
        elif function_type == FunctionType.EDGE_FUNCTION:
            # 边函数回退
            def fallback_edge_function(state: Dict[str, Any]) -> str:
                logger.warning(f"使用回退边函数: {function_name}")
                return "next"
            return fallback_edge_function
        
        return None
    
    def _import_class(self, class_path: str) -> Type:
        """动态导入类"""
        module_path, class_name = class_path.rsplit(":", 1)
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

# 全局工厂实例
_global_factory: Optional[UnifiedFunctionFactory] = None

def get_global_function_factory() -> UnifiedFunctionFactory:
    """获取全局函数工厂实例"""
    global _global_factory
    if _global_factory is None:
        from src.core.config.config_manager import ConfigManager
        config_manager = ConfigManager()
        _global_factory = UnifiedFunctionFactory(config_manager)
    return _global_factory

def create_function(function_name: str, function_type: Union[str, FunctionType], **kwargs) -> Optional[Callable]:
    """便捷函数：创建函数"""
    factory = get_global_function_factory()
    if isinstance(function_type, str):
        function_type = FunctionType(function_type)
    return factory.create_function(function_name, function_type, **kwargs)

def create_manager(manager_name: str, manager_type: Union[str, ManagerType], **kwargs) -> Any:
    """便捷函数：创建管理器"""
    factory = get_global_function_factory()
    if isinstance(manager_type, str):
        manager_type = ManagerType(manager_type)
    return factory.create_manager(manager_type, manager_name, **kwargs)

def create_adapter(adapter_name: str, adapter_type: Union[str, AdapterType], **kwargs) -> Any:
    """便捷函数：创建适配器"""
    factory = get_global_function_factory()
    if isinstance(adapter_type, str):
        adapter_type = AdapterType(adapter_type)
    return factory.create_adapter(adapter_type, adapter_name, **kwargs)
```

### 3. 工厂注册表

```python
# src/core/workflow/factory/registry.py
from typing import Dict, Any, Optional, List, Type, Callable
from enum import Enum

class RegistrationType(Enum):
    """注册类型枚举"""
    FUNCTION = "function"
    MANAGER = "manager"
    ADAPTER = "adapter"

class FactoryRegistry:
    """工厂注册表"""
    
    def __init__(self):
        self._registrations: Dict[RegistrationType, Dict[str, Dict[str, Any]]] = {
            RegistrationType.FUNCTION: {},
            RegistrationType.MANAGER: {},
            RegistrationType.ADAPTER: {}
        }
        self._aliases: Dict[str, str] = {}
    
    def register(
        self,
        registration_type: RegistrationType,
        name: str,
        class_path: str,
        config: Optional[Dict[str, Any]] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册组件"""
        registration = {
            "class_path": class_path,
            "config": config or {},
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat()
        }
        
        self._registrations[registration_type][name] = registration
        
        # 注册别名
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name
        
        logger.debug(f"注册{registration_type.value}: {name}")
    
    def unregister(self, registration_type: RegistrationType, name: str) -> bool:
        """注销组件"""
        if name in self._registrations[registration_type]:
            del self._registrations[registration_type][name]
            
            # 删除别名
            aliases_to_remove = [alias for alias, target in self._aliases.items() if target == name]
            for alias in aliases_to_remove:
                del self._aliases[alias]
            
            logger.debug(f"注销{registration_type.value}: {name}")
            return True
        
        return False
    
    def get_registration(self, registration_type: RegistrationType, name: str) -> Optional[Dict[str, Any]]:
        """获取注册信息"""
        # 检查别名
        actual_name = self._aliases.get(name, name)
        return self._registrations[registration_type].get(actual_name)
    
    def list_registrations(self, registration_type: RegistrationType) -> List[str]:
        """列出注册的组件"""
        return list(self._registrations[registration_type].keys())
    
    def get_all_registrations(self) -> Dict[RegistrationType, Dict[str, Dict[str, Any]]]:
        """获取所有注册信息"""
        return self._registrations.copy()
    
    def clear_registrations(self, registration_type: Optional[RegistrationType] = None) -> None:
        """清除注册"""
        if registration_type:
            self._registrations[registration_type].clear()
        else:
            for reg_type in self._registrations:
                self._registrations[reg_type].clear()
        self._aliases.clear()

# 全局注册表实例
_global_registry: Optional[FactoryRegistry] = None

def get_global_registry() -> FactoryRegistry:
    """获取全局注册表实例"""
    global _global_registry
    if _global_registry is None:
        _global_registry = FactoryRegistry()
    return _global_registry

# 装饰器函数
def register_function(name: str, aliases: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
    """注册函数装饰器"""
    def decorator(cls: Type) -> Type:
        registry = get_global_registry()
        registry.register(
            RegistrationType.FUNCTION,
            name,
            f"{cls.__module__}:{cls.__name__}",
            aliases=aliases,
            metadata=metadata
        )
        return cls
    return decorator

def register_manager(name: str, aliases: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
    """注册管理器装饰器"""
    def decorator(cls: Type) -> Type:
        registry = get_global_registry()
        registry.register(
            RegistrationType.MANAGER,
            name,
            f"{cls.__module__}:{cls.__name__}",
            aliases=aliases,
            metadata=metadata
        )
        return cls
    return decorator

def register_adapter(name: str, aliases: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
    """注册适配器装饰器"""
    def decorator(cls: Type) -> Type:
        registry = get_global_registry()
        registry.register(
            RegistrationType.ADAPTER,
            name,
            f"{cls.__module__}:{cls.__name__}",
            aliases=aliases,
            metadata=metadata
        )
        return cls
    return decorator
```

### 4. 工厂配置加载器

```python
# src/core/workflow/factory/config_loader.py
class FactoryConfigLoader:
    """工厂配置加载器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._config_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_function_config(self, function_type: str) -> Dict[str, Any]:
        """加载函数配置"""
        config_file = f"configs/builtin_functions/{function_type}.yaml"
        return self._load_config_with_cache(config_file)
    
    def load_manager_config(self, manager_type: str) -> Dict[str, Any]:
        """加载管理器配置"""
        config_file = f"configs/{manager_type}.yaml"
        return self._load_config_with_cache(config_file)
    
    def load_adapter_config(self, adapter_type: str) -> Dict[str, Any]:
        """加载适配器配置"""
        config_file = f"configs/{adapter_type}.yaml"
        return self._load_config_with_cache(config_file)
    
    def load_factory_config(self) -> Dict[str, Any]:
        """加载工厂配置"""
        return self._load_config_with_cache("configs/function_factory.yaml")
    
    def _load_config_with_cache(self, config_file: str) -> Dict[str, Any]:
        """带缓存的配置加载"""
        if config_file in self._config_cache:
            return self._config_cache[config_file]
        
        try:
            config = self.config_manager.load_config(config_file)
            self._config_cache[config_file] = config
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_file}: {e}")
            return {}
    
    def reload_config(self, config_file: Optional[str] = None) -> None:
        """重新加载配置"""
        if config_file:
            self._config_cache.pop(config_file, None)
        else:
            self._config_cache.clear()
```

这个统一函数工厂提供了：

1. **统一的创建接口**：通过一个工厂创建所有类型的组件
2. **完全配置驱动**：所有组件都通过配置文件定义和加载
3. **缓存优化**：支持组件实例缓存，提高性能
4. **回退机制**：当组件加载失败时提供回退选项
5. **重试逻辑**：支持自动重试失败的加载操作
6. **预加载功能**：支持启动时预加载常用组件
7. **统计信息**：提供详细的工厂使用统计
8. **注册表支持**：支持动态注册和发现组件
9. **便捷函数**：提供简化的组件创建接口

这个工厂将作为整个配置驱动系统的核心，统一管理所有组件的创建和生命周期。