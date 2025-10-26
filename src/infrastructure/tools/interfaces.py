"""
工具系统基础设施接口定义

定义了工具系统的技术实现接口，专注于基础设施层面的功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.tools.interfaces import ITool, ToolCall, ToolResult


class IToolManager(ABC):
    """工具管理器接口 - Infrastructure层实现"""

    @abstractmethod
    def load_tools(self) -> List["ITool"]:
        """从配置加载所有可用工具
        
        Returns:
            List[ITool]: 已加载的工具列表
        """
        pass

    @abstractmethod
    def get_tool(self, name: str) -> "ITool":
        """根据名称获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            ITool: 工具实例
            
        Raises:
            ValueError: 工具不存在
        """
        pass

    @abstractmethod
    def get_tool_set(self, name: str) -> List["ITool"]:
        """获取工具集
        
        Args:
            name: 工具集名称
            
        Returns:
            List[ITool]: 工具集中的工具列表
            
        Raises:
            ValueError: 工具集不存在
        """
        pass

    @abstractmethod
    def register_tool(self, tool: "ITool") -> None:
        """注册新工具
        
        Args:
            tool: 工具实例
            
        Raises:
            ValueError: 工具名称已存在
        """
        pass

    @abstractmethod
    def list_tools(self) -> List[str]:
        """列出所有可用工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        pass

    @abstractmethod
    def list_tool_sets(self) -> List[str]:
        """列出所有可用工具集名称
        
        Returns:
            List[str]: 工具集名称列表
        """
        pass

    @abstractmethod
    def reload_tools(self) -> List["ITool"]:
        """重新加载所有工具
        
        Returns:
            List[ITool]: 重新加载后的工具列表
        """
        pass


class IToolAdapter(ABC):
    """工具适配器接口 - 用于外部工具集成"""

    @abstractmethod
    def adapt_tool(self, external_tool: Any) -> "ITool":
        """将外部工具适配为内部工具接口
        
        Args:
            external_tool: 外部工具实例
            
        Returns:
            ITool: 适配后的工具实例
        """
        pass

    @abstractmethod
    def can_adapt(self, external_tool: Any) -> bool:
        """检查是否可以适配指定工具
        
        Args:
            external_tool: 外部工具实例
            
        Returns:
            bool: 是否可以适配
        """
        pass


class IToolLoader(ABC):
    """工具加载器接口"""

    @abstractmethod
    def load_from_config(self, config_path: str) -> List["ToolConfig"]:
        """从配置文件加载工具配置

        Args:
            config_path: 配置文件路径

        Returns:
            List[ToolConfig]: 加载的工具配置列表
        """
        pass

    @abstractmethod
    def load_from_module(self, module_path: str) -> List["ITool"]:
        """从模块加载工具
        
        Args:
            module_path: 模块路径
            
        Returns:
            List[ITool]: 加载的工具列表
        """
        pass


class IToolCache(ABC):
    """工具缓存接口"""

    @abstractmethod
    def get(self, key: str) -> Optional["ITool"]:
        """获取缓存的工具
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[ITool]: 工具实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def set(self, key: str, tool: "ITool", ttl: Optional[int] = None) -> None:
        """缓存工具
        
        Args:
            key: 缓存键
            tool: 工具实例
            ttl: 生存时间（秒）
        """
        pass

    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """使缓存失效
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功失效
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """清除所有缓存"""
        pass