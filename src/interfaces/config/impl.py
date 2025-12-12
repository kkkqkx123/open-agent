"""配置实现相关接口定义

提供配置实现的接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.interfaces.common_domain import IValidationResult


class IConfigImpl(ABC):
    """配置实现接口"""
    
    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置数据
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换配置为模块特定格式
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        pass
    
    @abstractmethod
    def get_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """获取当前配置
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            当前配置数据
        """
        pass
    
    @abstractmethod
    def get_config_path(self, config_name: str) -> str:
        """获取配置文件完整路径
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置文件路径
        """
        pass
    
    @abstractmethod
    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            重新加载的配置数据
        """
        pass