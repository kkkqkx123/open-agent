"""注册表工厂

提供创建和配置各种注册表的工厂方法。
"""

from typing import Dict, Any, Optional, List, Type
from src.services.logger.injection import get_logger
from .base_registry import BaseRegistry
from .node_registry import NodeRegistry
from .function_registry import FunctionRegistry
from .hook_registry import HookRegistry
from .plugin_registry import PluginRegistry
from .trigger_registry import TriggerRegistry
from .registry import UnifiedRegistry, RegistryManager

logger = get_logger(__name__)


class RegistryFactory:
    """注册表工厂
    
    提供创建和配置各种注册表的工厂方法。
    """
    
    @staticmethod
    def create_node_registry(config: Optional[Dict[str, Any]] = None) -> NodeRegistry:
        """创建节点注册表
        
        Args:
            config: 配置参数
            
        Returns:
            NodeRegistry: 节点注册表实例
        """
        registry = NodeRegistry()
        
        if config:
            # 应用配置
            if config.get("enable_validation", True):
                # 启用验证逻辑
                pass
        
        logger.debug("创建节点注册表")
        return registry
    
    @staticmethod
    def create_function_registry(config: Optional[Dict[str, Any]] = None) -> FunctionRegistry:
        """创建函数注册表
        
        Args:
            config: 配置参数
            
        Returns:
            FunctionRegistry: 函数注册表实例
        """
        enable_auto_discovery = config.get("enable_auto_discovery", False) if config else False
        registry = FunctionRegistry(enable_auto_discovery=enable_auto_discovery)
        
        if config:
            # 应用配置
            module_paths = config.get("auto_discovery_paths")
            if module_paths and enable_auto_discovery:
                registry.discover_functions(module_paths)
        
        logger.debug("创建函数注册表")
        return registry
    
    @staticmethod
    def create_hook_registry(config: Optional[Dict[str, Any]] = None) -> HookRegistry:
        """创建Hook注册表
        
        Args:
            config: 配置参数
            
        Returns:
            HookRegistry: Hook注册表实例
        """
        registry = HookRegistry()
        
        if config:
            # 应用配置
            if config.get("enable_validation", True):
                # 启用验证逻辑
                pass
        
        logger.debug("创建Hook注册表")
        return registry
    
    @staticmethod
    def create_plugin_registry(config: Optional[Dict[str, Any]] = None) -> PluginRegistry:
        """创建插件注册表
        
        Args:
            config: 配置参数
            
        Returns:
            PluginRegistry: 插件注册表实例
        """
        registry = PluginRegistry()
        
        if config:
            # 应用配置
            if config.get("auto_enable", False):
                # 自动启用插件
                pass
        
        logger.debug("创建插件注册表")
        return registry
    
    @staticmethod
    def create_trigger_registry(config: Optional[Dict[str, Any]] = None) -> TriggerRegistry:
        """创建触发器注册表
        
        Args:
            config: 配置参数
            
        Returns:
            TriggerRegistry: 触发器注册表实例
        """
        registry = TriggerRegistry()
        
        if config:
            # 应用配置
            if config.get("enable_builtin", True):
                # 启用内置触发器
                pass
        
        logger.debug("创建触发器注册表")
        return registry
    
    @staticmethod
    def create_unified_registry(config: Optional[Dict[str, Any]] = None) -> UnifiedRegistry:
        """创建统一注册表
        
        Args:
            config: 配置参数
            
        Returns:
            UnifiedRegistry: 统一注册表实例
        """
        registry = UnifiedRegistry()
        
        if config:
            # 应用配置到各个子注册表
            node_config = config.get("nodes")
            if node_config:
                # 这里可以重新创建节点注册表，但通常不需要
                pass
            
            function_config = config.get("functions")
            if function_config:
                # 重新创建函数注册表
                new_function_registry = RegistryFactory.create_function_registry(function_config)
                registry._function_registry = new_function_registry
            
            hook_config = config.get("hooks")
            if hook_config:
                # 重新创建Hook注册表
                new_hook_registry = RegistryFactory.create_hook_registry(hook_config)
                registry._hook_registry = new_hook_registry
            
            plugin_config = config.get("plugins")
            if plugin_config:
                # 重新创建插件注册表
                new_plugin_registry = RegistryFactory.create_plugin_registry(plugin_config)
                registry._plugin_registry = new_plugin_registry
            
            trigger_config = config.get("triggers")
            if trigger_config:
                # 重新创建触发器注册表
                new_trigger_registry = RegistryFactory.create_trigger_registry(trigger_config)
                registry._trigger_registry = new_trigger_registry
        
        logger.debug("创建统一注册表")
        return registry
    
    @staticmethod
    def create_registry_manager(unified_registry: Optional[UnifiedRegistry] = None, 
                              config: Optional[Dict[str, Any]] = None) -> RegistryManager:
        """创建注册表管理器
        
        Args:
            unified_registry: 统一注册表实例，如果为None则使用全局实例
            config: 配置参数
            
        Returns:
            RegistryManager: 注册表管理器实例
        """
        if unified_registry is None:
            unified_registry = RegistryFactory.create_unified_registry(config)
        
        manager = RegistryManager(unified_registry)
        
        if config:
            # 应用配置
            if config.get("initialize_defaults", False):
                manager.initialize_default_components()
        
        logger.debug("创建注册表管理器")
        return manager
    
    @staticmethod
    def create_registry_from_config(config: Dict[str, Any]) -> UnifiedRegistry:
        """从配置创建注册表
        
        Args:
            config: 完整的注册表配置
            
        Returns:
            UnifiedRegistry: 统一注册表实例
        """
        return RegistryFactory.create_unified_registry(config)
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            "nodes": {
                "enable_validation": True
            },
            "functions": {
                "enable_auto_discovery": False,
                "auto_discovery_paths": [
                    "src.workflow.nodes",
                    "src.workflow.conditions",
                    "src.infrastructure.graph.builtin_functions"
                ]
            },
            "hooks": {
                "enable_validation": True
            },
            "plugins": {
                "auto_enable": False
            },
            "triggers": {
                "enable_builtin": True
            }
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """验证配置
        
        Args:
            config: 配置参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证节点配置
        if "nodes" in config:
            node_config = config["nodes"]
            if not isinstance(node_config, dict):
                errors.append("节点配置必须是字典类型")
        
        # 验证函数配置
        if "functions" in config:
            function_config = config["functions"]
            if not isinstance(function_config, dict):
                errors.append("函数配置必须是字典类型")
            elif "auto_discovery_paths" in function_config:
                paths = function_config["auto_discovery_paths"]
                if not isinstance(paths, list):
                    errors.append("自动发现路径必须是列表类型")
        
        # 验证Hook配置
        if "hooks" in config:
            hook_config = config["hooks"]
            if not isinstance(hook_config, dict):
                errors.append("Hook配置必须是字典类型")
        
        # 验证插件配置
        if "plugins" in config:
            plugin_config = config["plugins"]
            if not isinstance(plugin_config, dict):
                errors.append("插件配置必须是字典类型")
        
        # 验证触发器配置
        if "triggers" in config:
            trigger_config = config["triggers"]
            if not isinstance(trigger_config, dict):
                errors.append("触发器配置必须是字典类型")
        
        return errors


class RegistryBuilder:
    """注册表构建器
    
    提供流式API来构建和配置注册表。
    """
    
    def __init__(self):
        """初始化注册表构建器"""
        self._config = {}
        self._node_registry: Optional[NodeRegistry] = None
        self._function_registry: Optional[FunctionRegistry] = None
        self._hook_registry: Optional[HookRegistry] = None
        self._plugin_registry: Optional[PluginRegistry] = None
        self._trigger_registry: Optional[TriggerRegistry] = None
    
    def with_node_config(self, config: Dict[str, Any]) -> 'RegistryBuilder':
        """设置节点配置
        
        Args:
            config: 节点配置
            
        Returns:
            RegistryBuilder: 构建器实例
        """
        self._config["nodes"] = config
        return self
    
    def with_function_config(self, config: Dict[str, Any]) -> 'RegistryBuilder':
        """设置函数配置
        
        Args:
            config: 函数配置
            
        Returns:
            RegistryBuilder: 构建器实例
        """
        self._config["functions"] = config
        return self
    
    def with_hook_config(self, config: Dict[str, Any]) -> 'RegistryBuilder':
        """设置Hook配置
        
        Args:
            config: Hook配置
            
        Returns:
            RegistryBuilder: 构建器实例
        """
        self._config["hooks"] = config
        return self
    
    def with_plugin_config(self, config: Dict[str, Any]) -> 'RegistryBuilder':
        """设置插件配置
        
        Args:
            config: 插件配置
            
        Returns:
            RegistryBuilder: 构建器实例
        """
        self._config["plugins"] = config
        return self
    
    def with_trigger_config(self, config: Dict[str, Any]) -> 'RegistryBuilder':
        """设置触发器配置
        
        Args:
            config: 触发器配置
            
        Returns:
            RegistryBuilder: 构建器实例
        """
        self._config["triggers"] = config
        return self
    
    def with_auto_discovery(self, paths: List[str]) -> 'RegistryBuilder':
        """启用自动发现
        
        Args:
            paths: 自动发现路径
            
        Returns:
            RegistryBuilder: 构建器实例
        """
        if "functions" not in self._config:
            self._config["functions"] = {}
        self._config["functions"]["enable_auto_discovery"] = True
        self._config["functions"]["auto_discovery_paths"] = paths
        return self
    
    def with_validation(self, enabled: bool = True) -> 'RegistryBuilder':
        """启用验证
        
        Args:
            enabled: 是否启用验证
            
        Returns:
            RegistryBuilder: 构建器实例
        """
        self._config["nodes"] = self._config.get("nodes", {})
        self._config["nodes"]["enable_validation"] = enabled
        
        self._config["hooks"] = self._config.get("hooks", {})
        self._config["hooks"]["enable_validation"] = enabled
        
        return self
    
    def build(self) -> UnifiedRegistry:
        """构建统一注册表
        
        Returns:
            UnifiedRegistry: 统一注册表实例
        """
        # 验证配置
        errors = RegistryFactory.validate_config(self._config)
        if errors:
            raise ValueError(f"配置验证失败: {errors}")
        
        return RegistryFactory.create_unified_registry(self._config)
    
    def build_manager(self) -> RegistryManager:
        """构建注册表管理器
        
        Returns:
            RegistryManager: 注册表管理器实例
        """
        registry = self.build()
        return RegistryManager(registry)


# 便捷函数
def create_registry() -> UnifiedRegistry:
    """创建默认配置的注册表
    
    Returns:
        UnifiedRegistry: 统一注册表实例
    """
    return RegistryFactory.create_unified_registry()


def create_registry_with_auto_discovery(paths: List[str]) -> UnifiedRegistry:
    """创建启用自动发现的注册表
    
    Args:
        paths: 自动发现路径
        
    Returns:
        UnifiedRegistry: 统一注册表实例
    """
    config = RegistryFactory.get_default_config()
    config["functions"]["enable_auto_discovery"] = True
    config["functions"]["auto_discovery_paths"] = paths
    
    return RegistryFactory.create_unified_registry(config)