"""配置系统接口定义

定义配置系统的共享接口，避免循环导入问题。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, TYPE_CHECKING
from pathlib import Path

# 避免循环导入的类型检查导入
if TYPE_CHECKING:
    from .models.global_config import GlobalConfig
    from .models.llm_config import LLMConfig
    from .models.tool_config import ToolConfig
    from .models.token_counter_config import TokenCounterConfig
    from .models.task_group_config import TaskGroupsConfig


class IConfigLoader(ABC):
    """配置加载器接口"""

    @property
    @abstractmethod
    def base_path(self) -> Path:
        """获取配置基础路径"""
        pass

    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass

    @abstractmethod
    def reload(self) -> None:
        """重新加载所有配置"""
        pass

    @abstractmethod
    def watch_for_changes(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """监听配置变化"""
        pass

    @abstractmethod
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量"""
        pass

    @abstractmethod
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        pass

    @abstractmethod
    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置，如果不存在则返回None"""
        pass

    @abstractmethod
    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件"""
        pass


class IConfigInheritanceHandler(ABC):
    """配置继承处理器接口"""
    @abstractmethod
    def resolve_inheritance(self, config: Dict[str, Any], base_path: Optional[Path] = None) -> Dict[str, Any]:
        """解析配置继承关系
        
        Args:
            config: 原始配置
            base_path: 基础路径
            
        Returns:
            解析后的配置
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any], schema: Optional[object] = None) -> List[str]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        pass


class IConfigMerger(ABC):
    """配置合并器接口"""
    
    @abstractmethod
    def merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            合并后的配置
        """
        pass


class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any], schema: Optional[object] = None) -> tuple[bool, List[str]]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            (是否有效, 错误消息列表)
        """
        pass


class IConfigSystem(ABC):
    """配置系统接口"""

    @abstractmethod
    def load_global_config(self) -> "GlobalConfig":
        """加载全局配置

        Returns:
            全局配置对象
        """
        pass

    @abstractmethod
    def load_llm_config(self, name: str) -> "LLMConfig":
        """加载LLM配置

        Args:
            name: 配置名称

        Returns:
            LLM配置对象
        """
        pass

    @abstractmethod
    def load_tool_config(self, name: str) -> "ToolConfig":
        """加载工具配置

        Args:
            name: 配置名称

        Returns:
            工具配置对象
        """
        pass

    @abstractmethod
    def load_token_counter_config(self, name: str) -> "TokenCounterConfig":
        """加载Token计数器配置

        Args:
            name: 配置名称

        Returns:
            Token计数器配置对象
        """
        pass

    @abstractmethod
    def load_task_groups_config(self) -> "TaskGroupsConfig":
        """加载任务组配置

        Returns:
            任务组配置对象
        """
        pass

    @abstractmethod
    def reload_configs(self) -> None:
        """重新加载所有配置"""
        pass

    @abstractmethod
    def get_config_path(self, config_type: str, name: str) -> str:
        """获取配置路径

        Args:
            config_type: 配置类型
            name: 配置名称

        Returns:
            配置路径
        """
        pass

    @abstractmethod
    def watch_for_changes(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """监听配置变化

        Args:
            callback: 变化回调函数
        """
        pass

    @abstractmethod
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        pass

    @abstractmethod
    def list_configs(self, config_type: str) -> List[str]:
        """列出指定类型的所有配置

        Args:
            config_type: 配置类型

        Returns:
            配置名称列表
        """
        pass

    @abstractmethod
    def config_exists(self, config_type: str, name: str) -> bool:
        """检查配置是否存在

        Args:
            config_type: 配置类型
            name: 配置名称

        Returns:
            是否存在
        """
        pass