"""通用基础设施层接口定义

提供基础设施层的通用接口，包括配置加载、存储、日志、依赖注入等技术组件。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING, TypeVar, Generic
from pathlib import Path
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from ..adapters.logger.handlers.base_handler import BaseHandler
    from ..core.logger.redactor import LogRedactor

# 泛型类型变量
T = TypeVar('T')


'''
基础设施层枚举定义
'''

class ServiceLifetime(str, Enum):
    """
    服务生命周期枚举
    
    定义依赖注入容器中服务的生命周期类型。
    """
    SINGLETON = "singleton"  # 单例模式，整个应用生命周期内只有一个实例
    TRANSIENT = "transient"  # 瞬态模式，每次请求都创建新实例
    SCOPED = "scoped"       # 作用域模式，在特定作用域内是单例


# LogLevel 枚举定义 - 从基础设施层导入
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.logger.core.log_level import LogLevel

'''
配置管理接口
'''

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


'''
存储接口
'''

class IStorage(ABC):
    """
    统一存储接口
    
    提供统一的数据存储抽象，支持多种存储后端。
    """
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> bool:
        """
        保存数据
        
        Args:
            data: 要保存的数据
            
        Returns:
            bool: 是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """
        加载数据
        
        Args:
            id: 数据ID
            
        Returns:
            Optional[Dict[str, Any]]: 加载的数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        列出数据
        
        Args:
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 符合条件的数据列表
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            bool: 是否删除成功
        """
        pass


'''
依赖注入接口
'''

class IDependencyContainer(ABC):
    """
    依赖注入容器接口
    
    提供服务注册、解析和生命周期管理功能。
    """
    
    @abstractmethod
    def register(
        self,
        interface: type,
        implementation: type,
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """
        注册服务实现
        
        Args:
            interface: 接口类型
            implementation: 实现类型
            environment: 环境名称
            lifetime: 生命周期类型
        """
        pass
    
    @abstractmethod
    def register_factory(
        self,
        interface: type,
        factory: Callable[[], Any],
        environment: str = "default",
        lifetime: str = ServiceLifetime.SINGLETON,
    ) -> None:
        """
        注册服务工厂
        
        Args:
            interface: 接口类型
            factory: 工厂函数
            environment: 环境名称
            lifetime: 生命周期类型
        """
        pass
    
    @abstractmethod
    def register_instance(
        self, interface: type, instance: Any, environment: str = "default"
    ) -> None:
        """
        注册服务实例
        
        Args:
            interface: 接口类型
            instance: 服务实例
            environment: 环境名称
        """
        pass
    
    @abstractmethod
    def get(self, service_type: type[T]) -> T:
        """
        获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            T: 服务实例
            
        Raises:
            ServiceNotFoundError: 服务未找到时抛出
        """
        pass
    
    @abstractmethod
    def get_environment(self) -> str:
        """
        获取当前环境
        
        Returns:
            str: 当前环境名称
        """
        pass
    
    @abstractmethod
    def set_environment(self, env: str) -> None:
        """
        设置当前环境
        
        Args:
            env: 环境名称
        """
        pass
    
    @abstractmethod
    def has_service(self, service_type: type) -> bool:
        """
        检查服务是否已注册
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否已注册
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        清除所有服务和缓存
        """
        pass



