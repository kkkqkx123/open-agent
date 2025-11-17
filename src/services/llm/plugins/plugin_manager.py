import asyncio
import importlib.util
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
from .interfaces import ILLMPlugin, IPluginManager
from ..core.base_factory import BaseFactory


class PluginManager(BaseFactory, IPluginManager):
    """插件管理器实现"""
    
    def __init__(self):
        self._plugins: Dict[str, ILLMPlugin] = {}
        self._loaded_modules: Dict[str, Any] = {}
    
    def create(self, *args, **kwargs) -> 'PluginManager':
        """
        创建插件管理器实例（工厂方法）
        
        Returns:
            PluginManager: 插件管理器实例
        """
        # 由于这是单例模式，直接返回自身
        return self
    
    def register_plugin(self, plugin: ILLMPlugin) -> None:
        """注册插件"""
        self._plugins[plugin.name] = plugin
    
    async def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            await plugin.cleanup()
            del self._plugins[plugin_name]
            return True
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[ILLMPlugin]:
        """获取插件实例"""
        return self._plugins.get(plugin_name)
    
    async def execute_plugin(self, plugin_name: str, *args, **kwargs) -> Any:
        """执行指定插件"""
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        return await plugin.execute(*args, **kwargs)
    
    def list_plugins(self) -> List[str]:
        """列出所有已注册插件"""
        return list(self._plugins.keys())
    
    async def load_plugins(self, plugin_dir: Path) -> None:
        """从目录加载插件"""
        if not plugin_dir.exists():
            return
        
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            await self._load_plugin_from_file(plugin_file)
    
    async def _load_plugin_from_file(self, plugin_file: Path) -> None:
        """从文件加载插件"""
        try:
            # 生成模块名
            module_name = f"llm_plugin_{plugin_file.stem}_{id(self)}"
            
            # 加载模块
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None or spec.loader is None:
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 查找插件类（继承自ILLMPlugin的类）
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) and 
                    issubclass(attr, ILLMPlugin) and 
                    attr != ILLMPlugin
                ):
                    plugin_instance = attr()
                    self.register_plugin(plugin_instance)
                    self._loaded_modules[plugin_file.name] = module
                    break
        except Exception as e:
            print(f"Failed to load plugin from {plugin_file}: {e}")
    
    async def initialize_all_plugins(self) -> None:
        """初始化所有插件"""
        for plugin_name, plugin in self._plugins.items():
            try:
                await plugin.initialize()
            except Exception as e:
                print(f"Failed to initialize plugin '{plugin_name}': {e}")
    
    async def cleanup_all_plugins(self) -> None:
        """清理所有插件"""
        for plugin_name, plugin in self._plugins.items():
            try:
                await plugin.cleanup()
            except Exception as e:
                print(f"Failed to cleanup plugin '{plugin_name}': {e}")
        
        self._plugins.clear()


class PluginManagerFactory:
    """插件管理器工厂（保持向后兼容）"""
    
    _instance: Optional['PluginManagerFactory'] = None
    _manager: Optional[PluginManager] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_manager(self) -> PluginManager:
        """获取插件管理器实例"""
        if self._manager is None:
            self._manager = PluginManager()
        return self._manager


# 全局插件管理器工厂实例
plugin_manager_factory = PluginManagerFactory()

# 注册到工厂注册表
BaseFactory.register("plugin_manager", PluginManager)