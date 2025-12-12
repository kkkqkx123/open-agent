"""配置加载器接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path


class IConfigLoader(ABC):
    """
    配置加载器接口
    
    负责配置文件的加载、解析和环境变量处理。
    这是基础设施层的核心组件，为整个系统提供配置支持。
    """
    
    @property
    @abstractmethod
    def base_path(self) -> Path:
        """
        获取配置基础路径
        
        Returns:
            Path: 配置文件的基础路径
        """
        pass
    
    @abstractmethod
    def load_config(self, config_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型（可选）
            
        Returns:
            Dict[str, Any]: 解析后的配置数据
            
        Raises:
            ConfigLoadError: 配置加载失败时抛出
        """
        pass
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """
        加载配置文件（简化接口）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 解析后的配置数据
        """
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """
        重新加载所有配置
        
        重新加载已加载的配置文件，支持热更新。
        """
        pass
    
    @abstractmethod
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        监听配置变化
        
        Args:
            callback: 配置变化时的回调函数
        """
        pass
    
    @abstractmethod
    def stop_watching(self) -> None:
        """
        停止监听配置变化
        """
        pass
    
    @abstractmethod
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析环境变量
        
        Args:
            config: 原始配置数据
            
        Returns:
            Dict[str, Any]: 解析环境变量后的配置数据
        """
        pass
    
    @abstractmethod
    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存中的配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 缓存的配置数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], config_path: str, config_type: Optional[str] = None) -> None:
        """
        保存配置
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            config_type: 配置类型（可选）
        """
        pass
    
    @abstractmethod
    def list_configs(self, config_type: Optional[str] = None) -> List[str]:
        """
        列出配置文件
        
        Args:
            config_type: 配置类型（可选）
            
        Returns:
            List[str]: 配置文件路径列表
        """
        pass
    
    @abstractmethod
    def validate_config_path(self, config_path: str) -> bool:
        """
        验证配置路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 路径是否有效
        """
        pass


class IHotReloadManager(ABC):
    """热重载管理器接口"""
    
    @abstractmethod
    def watch_file(self, file_path: str, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """监听文件变化
        
        Args:
            file_path: 文件路径
            callback: 变化回调函数
        """
        pass
    
    @abstractmethod
    def stop_watching(self, file_path: str) -> None:
        """停止监听文件变化
        
        Args:
            file_path: 文件路径
        """
        pass