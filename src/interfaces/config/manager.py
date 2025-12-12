"""配置管理器接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from ..common_domain import IValidationResult
from .validation import IConfigValidator


class IConfigManager(ABC):
    """统一配置管理器接口"""
    
    @abstractmethod
    def load_config(self, config_path: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型（可选）
            
        Returns:
            配置数据
        """
        pass
    
    @abstractmethod
    def load_config_with_module(self, config_path: str, module_type: str) -> Dict[str, Any]:
        """加载模块特定配置
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型
            
        Returns:
            配置数据
        """
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], config_path: str) -> None:
        """保存配置文件
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
        """
        pass
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def register_module_validator(self, module_type: str, validator: 'IConfigValidator') -> None:
        """注册模块特定验证器
        
        Args:
            module_type: 模块类型
            validator: 验证器
        """
        pass
    
    @abstractmethod
    def get_module_config(self, module_type: str) -> Dict[str, Any]:
        """获取模块配置
        
        Args:
            module_type: 模块类型
            
        Returns:
            模块配置
        """
        pass
    
    @abstractmethod
    def reload_module_configs(self, module_type: str) -> None:
        """重新加载模块配置
        
        Args:
            module_type: 模块类型
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
    
    @abstractmethod
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径，如果为None则清除所有缓存
        """
        pass

    @abstractmethod
    def list_config_files(self, config_directory: str) -> List[str]:
        """列出指定目录下的配置文件
        
        Args:
            config_directory: 配置目录路径
            
        Returns:
            配置文件路径列表
        """
        pass


class IConfigManagerFactory(ABC):
    """配置管理器工厂接口"""
    
    @abstractmethod
    def get_manager(self, module_type: str) -> IConfigManager:
        """获取模块特定的配置管理器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置管理器实例
        """
        pass
    
    @abstractmethod
    def register_manager_decorator(self, module_type: str, decorator_class: type) -> None:
        """注册管理器装饰器
        
        Args:
            module_type: 模块类型
            decorator_class: 装饰器类
        """
        pass