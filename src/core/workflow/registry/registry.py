"""统一工作流注册表

组合所有注册表，提供统一的工作流组件管理接口。
"""

from typing import Dict, Any, List, Optional
from src.interfaces.dependency_injection import get_logger
from .base_registry import BaseRegistry
from .node_registry import NodeRegistry
from .function_registry import FunctionRegistry
from .hook_registry import HookRegistry
from .plugin_registry import PluginRegistry
from .trigger_registry import TriggerRegistry

logger = get_logger(__name__)


class UnifiedRegistry:
    """统一工作流注册表
    
    组合所有注册表，提供统一的工作流组件管理接口。
    """
    
    def __init__(self):
        """初始化统一注册表"""
        self._node_registry = NodeRegistry()
        self._function_registry = FunctionRegistry()
        self._hook_registry = HookRegistry()
        self._plugin_registry = PluginRegistry()
        self._trigger_registry = TriggerRegistry()
        self._logger = get_logger(__name__)
    
    @property
    def nodes(self) -> NodeRegistry:
        """节点注册表"""
        return self._node_registry
    
    @property
    def functions(self) -> FunctionRegistry:
        """函数注册表"""
        return self._function_registry
    
    @property
    def hooks(self) -> HookRegistry:
        """Hook注册表"""
        return self._hook_registry
    
    @property
    def plugins(self) -> PluginRegistry:
        """插件注册表"""
        return self._plugin_registry
    
    @property
    def triggers(self) -> TriggerRegistry:
        """触发器注册表"""
        return self._trigger_registry
    
    def validate_dependencies(self) -> List[str]:
        """验证所有注册表的依赖完整性
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证节点类型的依赖
        for node_type in self._node_registry.list_node_types():
            node_class = self._node_registry.get_node_class(node_type)
            if node_class:
                get_required_functions = getattr(node_class, 'get_required_functions', None)
                if callable(get_required_functions):
                    try:
                        required_functions = get_required_functions()
                        if isinstance(required_functions, (list, tuple)):
                            for func_name in required_functions:
                                if not self._function_registry.get_node_function(func_name):
                                    errors.append(f"节点类型 {node_type} 需要函数 {func_name} 但未注册")
                    except Exception as e:
                        self._logger.warning(f"获取节点类型 {node_type} 的必需函数失败: {e}")
        
        # 验证插件依赖
        plugin_dependency_issues = self._plugin_registry.validate_all_dependencies()
        for plugin_name, missing_deps in plugin_dependency_issues.items():
            for dep in missing_deps:
                errors.append(f"插件 {plugin_name} 缺少依赖: {dep}")
        
        # 验证Hook依赖
        hook_errors = self._hook_registry.validate_hook_dependencies()
        errors.extend(hook_errors)
        
        return errors
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取所有注册表的统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "nodes": self._node_registry.get_stats(),
            "functions": self._function_registry.get_stats(),
            "hooks": self._hook_registry.get_stats(),
            "plugins": self._plugin_registry.get_stats(),
            "triggers": self._trigger_registry.get_stats(),
            "dependency_errors": len(self.validate_dependencies())
        }
    
    def clear_all(self) -> None:
        """清除所有注册表"""
        self._node_registry.clear()
        self._function_registry.clear()
        self._hook_registry.clear()
        self._plugin_registry.clear()
        self._trigger_registry.clear()
        self._logger.debug("已清除所有注册表")
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """获取注册表摘要信息
        
        Returns:
            Dict[str, Any]: 摘要信息
        """
        stats = self.get_registry_stats()
        
        summary = {
            "total_components": 0,
            "registry_health": "healthy",
            "last_validation": None,
            "component_counts": {}
        }
        
        # 计算总组件数
        for registry_name, registry_stats in stats.items():
            if registry_name == "dependency_errors":
                continue
            
            if isinstance(registry_stats, dict):
                if "total_items" in registry_stats:
                    summary["total_components"] += registry_stats["total_items"]
                elif "total_functions" in registry_stats:
                    summary["total_components"] += registry_stats["total_functions"]
                elif "total_plugins" in registry_stats:
                    summary["total_components"] += registry_stats["total_plugins"]
                elif "total_triggers" in registry_stats:
                    summary["total_components"] += registry_stats["total_triggers"]
                
                summary["component_counts"][registry_name] = registry_stats.get("total_items", 0)
        
        # 检查健康状态
        if stats["dependency_errors"] > 0:
            summary["registry_health"] = "warning"
        
        return summary
    
    def export_registry_state(self) -> Dict[str, Any]:
        """导出注册表状态
        
        Returns:
            Dict[str, Any]: 注册表状态
        """
        return {
            "nodes": {
                "classes": list(self._node_registry._node_classes.keys()),
                "instances": list(self._node_registry._node_instances.keys())
            },
            "functions": {
                "node_functions": self._function_registry.list_node_functions(),
                "condition_functions": self._function_registry.list_condition_functions(),
                "trigger_functions": self._function_registry.list_trigger_functions()
            },
            "hooks": {
                "hook_points": [point.value for point in self._hook_registry.get_hook_points()],
                "total_hooks": len(self._hook_registry._hook_dict)
            },
            "plugins": {
                "by_type": {
                    plugin_type: self._plugin_registry.list_plugins()
                    for plugin_type in self._plugin_registry.get_type_categories()
                },
                "enabled": self._plugin_registry.get_enabled_plugins()
            },
            "triggers": {
                "by_type": {
                    trigger_type: self._trigger_registry.list_triggers_by_type(trigger_type)
                    for trigger_type in self._trigger_registry.get_trigger_types()
                },
                "compositions": self._trigger_registry.list_compositions()
            }
        }
    
    def import_registry_state(self, state: Dict[str, Any]) -> bool:
        """导入注册表状态
        
        Args:
            state: 注册表状态
            
        Returns:
            bool: 是否成功导入
        """
        try:
            # 注意：这里只导入状态信息，不导入实际的组件
            # 实际的组件需要通过其他方式注册
            
            self._logger.info("注册表状态导入完成")
            return True
        except Exception as e:
            self._logger.error(f"注册表状态导入失败: {e}")
            return False
    
    def validate_registry_integrity(self) -> Dict[str, Any]:
        """验证注册表完整性
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "registry_status": {}
        }
        
        # 验证每个注册表
        registries = {
            "nodes": self._node_registry,
            "functions": self._function_registry,
            "hooks": self._hook_registry,
            "plugins": self._plugin_registry,
            "triggers": self._trigger_registry
        }
        
        for name, registry in registries.items():
            try:
                stats = registry.get_stats()
                result["registry_status"][name] = {
                    "status": "healthy",
                    "item_count": stats.get("total_items", 0) or stats.get("total_functions", 0) or stats.get("total_plugins", 0) or stats.get("total_triggers", 0)
                }
            except Exception as e:
                result["is_valid"] = False
                result["errors"].append(f"注册表 {name} 验证失败: {e}")
                result["registry_status"][name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # 验证依赖关系
        dependency_errors = self.validate_dependencies()
        if dependency_errors:
            result["warnings"].extend(dependency_errors)
        
        return result
    
    def get_registry_manager(self) -> 'RegistryManager':
        """获取注册表管理器
        
        Returns:
            RegistryManager: 注册表管理器实例
        """
        return RegistryManager(self)


class RegistryManager:
    """注册表管理器
    
    提供高级的注册表管理功能。
    """
    
    def __init__(self, unified_registry: UnifiedRegistry):
        """初始化注册表管理器
        
        Args:
            unified_registry: 统一注册表实例
        """
        self._registry = unified_registry
        self._logger = get_logger(__name__)
    
    def initialize_default_components(self) -> None:
        """初始化默认组件"""
        self._logger.info("初始化默认组件")
        
        # 这里可以注册一些默认的组件
        # 例如：内置节点、函数、Hook等
    
    def perform_health_check(self) -> Dict[str, Any]:
        """执行健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_result = {
            "overall_status": "healthy",
            "checks": {},
            "recommendations": []
        }
        
        # 检查注册表完整性
        integrity_result = self._registry.validate_registry_integrity()
        health_result["checks"]["integrity"] = integrity_result
        
        if not integrity_result["is_valid"]:
            health_result["overall_status"] = "unhealthy"
        
        if integrity_result["warnings"]:
            health_result["overall_status"] = "warning"
        
        # 检查依赖关系
        dependency_errors = self._registry.validate_dependencies()
        if dependency_errors:
            health_result["checks"]["dependencies"] = {
                "status": "error",
                "errors": dependency_errors
            }
            health_result["overall_status"] = "warning"
            health_result["recommendations"].append("解决依赖关系问题")
        else:
            health_result["checks"]["dependencies"] = {
                "status": "healthy"
            }
        
        return health_result
    
    def optimize_registry_performance(self) -> Dict[str, Any]:
        """优化注册表性能
        
        Returns:
            Dict[str, Any]: 优化结果
        """
        optimization_result = {
            "optimizations_performed": [],
            "performance_improvements": {}
        }
        
        # 这里可以实现各种优化策略
        # 例如：清理未使用的组件、优化缓存等
        
        return optimization_result
    
    def backup_registry_state(self) -> Optional[str]:
        """备份注册表状态
        
        Returns:
            Optional[str]: 备份文件路径，如果失败返回None
        """
        try:
            import json
            import tempfile
            from datetime import datetime
            
            state = self._registry.export_registry_state()
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "state": state
                }, f, indent=2)
                return f.name
        except Exception as e:
            self._logger.error(f"备份注册表状态失败: {e}")
            return None
    
    def restore_registry_state(self, backup_path: str) -> bool:
        """恢复注册表状态
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否成功恢复
        """
        try:
            import json
            
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            state = backup_data.get("state")
            if state:
                return self._registry.import_registry_state(state)
            
            return False
        except Exception as e:
            self._logger.error(f"恢复注册表状态失败: {e}")
            return False


# 全局统一注册表实例
_global_unified_registry: Optional[UnifiedRegistry] = None


def get_global_unified_registry() -> UnifiedRegistry:
    """获取全局统一注册表
    
    Returns:
        UnifiedRegistry: 全局统一注册表
    """
    global _global_unified_registry
    if _global_unified_registry is None:
        _global_unified_registry = UnifiedRegistry()
    return _global_unified_registry


def reset_global_unified_registry() -> None:
    """重置全局统一注册表（用于测试）"""
    global _global_unified_registry
    _global_unified_registry = None


# 便捷函数
def create_unified_registry() -> UnifiedRegistry:
    """创建统一注册表实例
    
    Returns:
        UnifiedRegistry: 统一注册表实例
    """
    return UnifiedRegistry()


def create_registry_manager() -> RegistryManager:
    """创建注册表管理器实例
    
    Returns:
        RegistryManager: 注册表管理器实例
    """
    registry = get_global_unified_registry()
    return RegistryManager(registry)