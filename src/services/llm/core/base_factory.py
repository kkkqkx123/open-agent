"""抽象工厂基类

提供统一的工厂模式实现，支持单例模式和工厂注册。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class BaseFactory(ABC):
    """抽象工厂基类
    
    提供统一的工厂模式实现，包括：
    1. 单例模式支持
    2. 工厂注册机制
    3. 生命周期管理
    4. 工厂发现和自动注册
    """
    
    _instances: Dict[str, 'BaseFactory'] = {}
    _registry: Dict[str, Type['BaseFactory']] = {}
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        # 使用类名作为键来确保每个工厂类型只有一个实例
        factory_key = cls.__name__
        
        if factory_key not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[factory_key] = instance
            logger.debug(f"创建工厂实例: {factory_key}")
        
        return cls._instances[factory_key]
    
    @abstractmethod
    def create(self, *args, **kwargs) -> Any:
        """
        创建实例的抽象方法
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            创建的实例
        """
        pass
    
    @classmethod
    def register(cls, name: str, factory_class: Type['BaseFactory']) -> None:
        """
        注册工厂类
        
        Args:
            name: 工厂名称
            factory_class: 工厂类
        """
        cls._registry[name] = factory_class
        logger.debug(f"注册工厂: {name} -> {factory_class.__name__}")
    
    @classmethod
    def get_factory(cls, name: str) -> Optional['BaseFactory']:
        """
        获取工厂实例
        
        Args:
            name: 工厂名称
            
        Returns:
            工厂实例，如果不存在则返回None
        """
        factory_class = cls._registry.get(name)
        if factory_class:
            return factory_class()
        return None
    
    @classmethod
    def list_factories(cls) -> list[str]:
        """
        列出所有已注册的工厂名称
        
        Returns:
            工厂名称列表
        """
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        检查工厂是否已注册
        
        Args:
            name: 工厂名称
            
        Returns:
            是否已注册
        """
        return name in cls._registry
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        注销工厂
        
        Args:
            name: 工厂名称
            
        Returns:
            是否成功注销
        """
        if name in cls._registry:
            del cls._registry[name]
            # 同时清理实例
            factory_key = cls._registry.get(name).__name__ if name in cls._registry else name
            if factory_key in cls._instances:
                del cls._instances[factory_key]
            logger.debug(f"注销工厂: {name}")
            return True
        return False
    
    def reset_instance(self) -> None:
        """重置工厂实例（主要用于测试）"""
        factory_key = self.__class__.__name__
        if factory_key in self._instances:
            del self._instances[factory_key]
            logger.debug(f"重置工厂实例: {factory_key}")
    
    @classmethod
    def reset_all_instances(cls) -> None:
        """重置所有工厂实例（主要用于测试）"""
        cls._instances.clear()
        logger.debug("重置所有工厂实例")
    
    def get_factory_info(self) -> Dict[str, Any]:
        """
        获取工厂信息
        
        Returns:
            工厂信息字典
        """
        return {
            "name": self.__class__.__name__,
            "module": self.__class__.__module__,
            "is_singleton": True,
            "registry_size": len(self._registry),
            "registered_factories": list(self._registry.keys())
        }
    
    @classmethod
    def get_registry_info(cls) -> Dict[str, Any]:
        """
        获取注册表信息
        
        Returns:
            注册表信息字典
        """
        return {
            "total_factories": len(cls._registry),
            "active_instances": len(cls._instances),
            "factories": {
                name: {
                    "class": factory_class.__name__,
                    "module": factory_class.__module__,
                    "has_instance": factory_class.__name__ in cls._instances
                }
                for name, factory_class in cls._registry.items()
            }
        }


class FactoryManager:
    """工厂管理器
    
    负责管理所有工厂的注册、创建和生命周期。
    """
    
    def __init__(self):
        """初始化工厂管理器"""
        self._factories: Dict[str, BaseFactory] = {}
        self._initialized = False
    
    def register_factory(self, name: str, factory_class: Type[BaseFactory]) -> None:
        """
        注册工厂类
        
        Args:
            name: 工厂名称
            factory_class: 工厂类
        """
        BaseFactory.register(name, factory_class)
        logger.info(f"工厂管理器注册工厂: {name}")
    
    def get_factory(self, name: str) -> Optional[BaseFactory]:
        """
        获取工厂实例
        
        Args:
            name: 工厂名称
            
        Returns:
            工厂实例
        """
        if name not in self._factories:
            factory = BaseFactory.get_factory(name)
            if factory:
                self._factories[name] = factory
        
        return self._factories.get(name)
    
    def create(self, factory_name: str, *args, **kwargs) -> Any:
        """
        使用指定工厂创建实例
        
        Args:
            factory_name: 工厂名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            创建的实例
            
        Raises:
            ValueError: 工厂不存在
        """
        factory = self.get_factory(factory_name)
        if not factory:
            raise ValueError(f"工厂不存在: {factory_name}")
        
        return factory.create(*args, **kwargs)
    
    def list_factories(self) -> list[str]:
        """
        列出所有已注册的工厂名称
        
        Returns:
            工厂名称列表
        """
        return BaseFactory.list_factories()
    
    def get_manager_info(self) -> Dict[str, Any]:
        """
        获取工厂管理器信息
        
        Returns:
            工厂管理器信息字典
        """
        return {
            "initialized": self._initialized,
            "loaded_factories": len(self._factories),
            "available_factories": len(BaseFactory._registry),
            "factories": list(self._factories.keys()),
            "registry_info": BaseFactory.get_registry_info()
        }
    
    def initialize(self) -> None:
        """初始化工厂管理器"""
        if self._initialized:
            return
        
        # 预加载常用工厂
        common_factories = BaseFactory.list_factories()
        for factory_name in common_factories:
            self.get_factory(factory_name)
        
        self._initialized = True
        logger.info(f"工厂管理器初始化完成，加载了 {len(self._factories)} 个工厂")
    
    def reset(self) -> None:
        """重置工厂管理器"""
        self._factories.clear()
        self._initialized = False
        BaseFactory.reset_all_instances()
        logger.info("工厂管理器已重置")


# 全局工厂管理器实例
factory_manager = FactoryManager()