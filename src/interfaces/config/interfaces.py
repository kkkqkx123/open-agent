"""统一配置管理器接口定义

定义统一配置加载系统的核心接口，确保各模块使用一致的配置加载方式。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

from ..configuration import ValidationResult


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


class IConfigInheritanceHandler(ABC):
    """
    配置继承处理器接口
    
    负责处理配置文件之间的继承关系。
    """
    
    @abstractmethod
    def resolve_inheritance(self, config: Dict[str, Any], base_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        解析配置继承关系
        
        Args:
            config: 原始配置
            base_path: 基础路径
            
        Returns:
            Dict[str, Any]: 解析继承后的配置
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any], schema: Optional[object] = None) -> List[str]:
        """
        验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            List[str]: 验证错误列表
        """
        pass


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


class IUnifiedConfigManager:
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
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
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


class IConfigManagerFactory(ABC):
    """配置管理器工厂接口"""
    
    @abstractmethod
    def get_manager(self, module_type: str) -> IUnifiedConfigManager:
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


class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        pass