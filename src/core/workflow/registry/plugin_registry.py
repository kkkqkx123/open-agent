"""插件注册表

管理插件的注册、获取和查询功能。
"""

from typing import Any, Dict, List, Optional, Type, cast
from src.interfaces.dependency_injection import get_logger
from src.interfaces.workflow.plugins import IPlugin, PluginType, PluginStatus
from .base_registry import BaseRegistry, TypedRegistry

logger = get_logger(__name__)


class PluginRegistry(TypedRegistry):
    """插件注册表
    
    负责管理所有已注册的插件实例。
    """
    
    def __init__(self) -> None:
        """初始化插件注册表"""
        super().__init__(
            "plugin",
            [plugin_type.value for plugin_type in PluginType]
        )
        self._plugin_statuses: Dict[str, PluginStatus] = {}
    
    def register_plugin(self, plugin: Optional[IPlugin]) -> bool:
        """注册插件
        
        Args:
            plugin: 插件实例
            
        Returns:
            bool: 注册是否成功
        """
        if plugin is None:
            self._logger.error("插件实例不能为None")
            return False
        
        try:
            plugin_name = plugin.metadata.name
            
            # 检查是否已注册
            if plugin_name in self._items:
                self._logger.warning(f"插件 {plugin_name} 已存在，将被覆盖")
            
            # 注册插件
            self.register(plugin_name, plugin)
            self._plugin_statuses[plugin_name] = PluginStatus.ENABLED
            
            # 按类型分类
            plugin_type = plugin.metadata.plugin_type
            if plugin_name not in self._items_by_type[plugin_type.value]:
                self._items_by_type[plugin_type.value].append(plugin_name)
            
            self._logger.info(f"成功注册插件: {plugin_name} (类型: {plugin_type.value})")
            return True
            
        except Exception as e:
            self._logger.error(f"注册插件失败: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 注销是否成功
        """
        if plugin_name not in self._items:
            self._logger.warning(f"插件 {plugin_name} 不存在")
            return False
        
        try:
            plugin = self._items[plugin_name]
            plugin_type = plugin.metadata.plugin_type
            
            # 清理插件资源
            plugin.cleanup()
            
            # 从注册表中移除
            self.unregister(plugin_name)
            del self._plugin_statuses[plugin_name]
            
            # 从类型列表中移除
            if plugin_name in self._items_by_type[plugin_type.value]:
                self._items_by_type[plugin_type.value].remove(plugin_name)
            
            self._logger.info(f"成功注销插件: {plugin_name}")
            return True
            
        except Exception as e:
            self._logger.error(f"注销插件失败 {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[IPlugin]: 插件实例，如果不存在返回None
        """
        return self.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[IPlugin]:
        """根据类型获取插件列表
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            List[IPlugin]: 插件列表
        """
        plugin_names = self._items_by_type.get(plugin_type.value, [])
        plugins: List[IPlugin] = []
        for name in plugin_names:
            if self.has_item(name):
                plugin = self.get(name)
                if plugin is not None:
                    plugins.append(cast(IPlugin, plugin))
        return plugins
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None, 
                    status: Optional[PluginStatus] = None) -> List[str]:
        """列出插件名称
        
        Args:
            plugin_type: 插件类型过滤器
            status: 插件状态过滤器
            
        Returns:
            List[str]: 插件名称列表
        """
        plugin_names = list(self._items.keys())
        
        # 按类型过滤
        if plugin_type is not None:
            plugin_names = [
                name for name in plugin_names
                if self._items[name].metadata.plugin_type == plugin_type
            ]
        
        # 按状态过滤
        if status is not None:
            plugin_names = [
                name for name in plugin_names
                if self._plugin_statuses.get(name) == status
            ]
        
        return plugin_names
    
    def get_plugin_status(self, plugin_name: str) -> PluginStatus:
        """获取插件状态
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            PluginStatus: 插件状态
        """
        return self._plugin_statuses.get(plugin_name, PluginStatus.DISABLED)
    
    def set_plugin_status(self, plugin_name: str, status: PluginStatus) -> bool:
        """设置插件状态
        
        Args:
            plugin_name: 插件名称
            status: 新状态
            
        Returns:
            bool: 设置是否成功
        """
        if plugin_name not in self._items:
            self._logger.error(f"插件 {plugin_name} 不存在")
            return False
        
        old_status = self._plugin_statuses[plugin_name]
        self._plugin_statuses[plugin_name] = status
        
        self._logger.info(f"插件 {plugin_name} 状态从 {old_status.value} 更改为 {status.value}")
        return True
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 启用是否成功
        """
        return self.set_plugin_status(plugin_name, PluginStatus.ENABLED)
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 禁用是否成功
        """
        return self.set_plugin_status(plugin_name, PluginStatus.DISABLED)
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Dict[str, any]]: 插件信息，如果不存在返回None
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            return None
        
        metadata = plugin.metadata
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "type": metadata.plugin_type.value,
            "dependencies": metadata.dependencies,
            "status": self.get_plugin_status(plugin_name).value,
            "config_schema": metadata.config_schema
        }
    
    def validate_dependencies(self, plugin_name: str) -> List[str]:
        """验证插件依赖
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            List[str]: 缺失的依赖列表，空列表表示所有依赖都满足
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            return [f"插件 {plugin_name} 不存在"]
        
        missing_deps = []
        for dep in plugin.metadata.dependencies or []:
            if dep not in self._items:
                missing_deps.append(dep)
        
        return missing_deps
    
    def get_dependency_order(self, plugin_names: List[str]) -> List[str]:
        """获取插件的依赖顺序
        
        Args:
            plugin_names: 插件名称列表
            
        Returns:
            List[str]: 按依赖顺序排序的插件名称列表
        """
        # 简单的拓扑排序实现
        ordered = []
        remaining = plugin_names.copy()
        visited = set()
        
        def visit(plugin_name: str) -> None:
            if plugin_name in visited or plugin_name not in remaining:
                return
            
            visited.add(plugin_name)
            plugin = self.get_plugin(plugin_name)
            
            if plugin:
                # 先访问依赖
                for dep in plugin.metadata.dependencies or []:
                    if dep in remaining:
                        visit(dep)
            
            ordered.append(plugin_name)
        
        for plugin_name in remaining:
            visit(plugin_name)
        
        return ordered
    
    def get_enabled_plugins(self) -> List[IPlugin]:
        """获取所有启用的插件
        
        Returns:
            List[IPlugin]: 启用的插件列表
        """
        enabled_plugins = []
        for plugin_name, status in self._plugin_statuses.items():
            if status == PluginStatus.ENABLED:
                plugin = self.get_plugin(plugin_name)
                if plugin:
                    enabled_plugins.append(plugin)
        return enabled_plugins
    
    def get_plugins_by_hook_point(self, hook_point: str) -> List[IPlugin]:
        """根据Hook点获取支持该点的插件
        
        Note:
            此方法已不再使用，因为Hook系统已与插件系统分离。
            请使用Hook注册表来管理Hook点相关的功能。
        
        Args:
            hook_point: Hook点
            
        Returns:
            List[IPlugin]: 支持该Hook点的插件列表（通常返回空列表）
        """
        # Hook系统已与插件系统分离，此方法保留以保持向后兼容性
        return []
    
    def validate_all_dependencies(self) -> Dict[str, List[str]]:
        """验证所有插件的依赖关系
        
        Returns:
            Dict[str, List[str]]: 每个插件的缺失依赖列表
        """
        dependency_issues = {}
        for plugin_name in self.list_items():
            missing_deps = self.validate_dependencies(plugin_name)
            if missing_deps:
                dependency_issues[plugin_name] = missing_deps
        return dependency_issues
    
    def clear(self) -> None:
        """清除所有插件"""
        # 清理所有插件资源
        for plugin in self._items.values():
            try:
                plugin.cleanup()
            except Exception as e:
                self._logger.error(f"清理插件资源失败 {plugin.metadata.name}: {e}")
        
        # 清空注册表
        super().clear()
        self._plugin_statuses.clear()
        
        self._logger.info("已清除所有插件")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, any]: 统计信息
        """
        stats = super().get_stats()
        
        # 按状态统计
        status_stats = {}
        for status in PluginStatus:
            count = sum(1 for s in self._plugin_statuses.values() if s == status)
            status_stats[status.value] = count
        
        stats.update({
            "total_plugins": len(self._items),
            "by_status": status_stats,
            "enabled_plugins": len(self.get_enabled_plugins()),
            "dependency_issues": len(self.validate_all_dependencies())
        })
        
        return stats
    
    def validate_item(self, name: str, item: Any) -> None:
        """验证项目
        
        Args:
            name: 项目名称
            item: 项目对象
            
        Raises:
            ValueError: 项目验证失败
        """
        super().validate_item(name, item)
        
        if not isinstance(item, IPlugin):
            raise ValueError("项目必须实现 IPlugin 接口")
        
        if not hasattr(item, 'metadata') or not item.metadata:
            raise ValueError("插件必须具有有效的metadata属性")
        
        if not hasattr(item.metadata, 'name') or not item.metadata.name:
            raise ValueError("插件metadata必须具有有效的name属性")
        
        if not hasattr(item, 'cleanup') or not callable(item.cleanup):
            raise ValueError("插件必须实现cleanup方法")