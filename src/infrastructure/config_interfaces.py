"""配置系统接口定义

定义配置系统的共享接口，避免循环导入问题。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List


class IConfigLoader(ABC):
    """配置加载器接口"""

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
    def resolve_inheritance(self, config: Dict[str, Any], base_path: Optional[str] = None) -> Dict[str, Any]:
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