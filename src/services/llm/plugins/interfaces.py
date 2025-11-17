from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable
from pathlib import Path


class ILLMPlugin(ABC):
    """LLM插件接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化插件"""
        pass
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理插件资源"""
        pass


class IPluginManager(ABC):
    """插件管理器接口"""
    
    @abstractmethod
    def register_plugin(self, plugin: ILLMPlugin) -> None:
        """注册插件"""
        pass
    
    @abstractmethod
    async def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_name: str) -> Optional[ILLMPlugin]:
        """获取插件实例"""
        pass
    
    @abstractmethod
    async def execute_plugin(self, plugin_name: str, *args, **kwargs) -> Any:
        """执行指定插件"""
        pass
    
    @abstractmethod
    def list_plugins(self) -> List[str]:
        """列出所有已注册插件"""
        pass
    
    @abstractmethod
    async def load_plugins(self, plugin_dir: Path) -> None:
        """从目录加载插件"""
        pass
    
    @abstractmethod
    async def initialize_all_plugins(self) -> None:
        """初始化所有插件"""
        pass
    
    @abstractmethod
    async def cleanup_all_plugins(self) -> None:
        """清理所有插件"""
        pass