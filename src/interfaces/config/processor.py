"""配置处理器接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IConfigProcessor(ABC):
    """配置处理器接口"""
    
    @abstractmethod
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置数据
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取处理器名称
        
        Returns:
            处理器名称
        """
        pass