"""配置提供者相关接口定义

提供配置提供者的接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IConfigProvider(ABC):
    """配置提供者接口"""
    
    @abstractmethod
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """获取配置数据
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置数据
        """
        pass
    
    @abstractmethod
    def get_config_model(self, config_name: str) -> Any:
        """获取配置模型
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置模型实例
        """
        pass
    
    @abstractmethod
    def reload_config(self, config_name: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            重新加载的配置数据
        """
        pass