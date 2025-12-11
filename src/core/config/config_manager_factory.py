"""Core层配置管理工厂

提供统一的配置管理器创建和管理功能，优化配置系统的架构设计。
"""

from typing import Dict, Any, Optional, Type
from pathlib import Path
import logging

from src.interfaces.config import (
    IConfigLoader, IConfigProcessor, IConfigValidator, IConfigInheritanceHandler,
    IConfigManager, IConfigManagerFactory
)
from src.infrastructure.validation.result import ValidationResult
from .config_manager import ConfigManager
from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
from src.infrastructure.config.validation import BaseConfigValidator

logger = logging.getLogger(__name__)


class CoreConfigManagerFactory(IConfigManagerFactory):
    """Core层配置管理器工厂
    
    负责创建和管理不同模块的配置管理器，确保配置系统的一致性和可维护性。
    """
    
    def __init__(self, 
                 config_loader: IConfigLoader,
                 inheritance_handler: Optional[IConfigInheritanceHandler] = None,
                 base_path: Optional[Path] = None):
        """初始化配置管理器工厂
        
        Args:
            config_loader: 基础配置加载器
            inheritance_handler: 继承处理器（可选）
            base_path: 配置文件基础路径（可选）
        """
        self.config_loader = config_loader
        self.inheritance_handler = inheritance_handler
        self.base_path = base_path or Path("configs")
        
        # 缓存已创建的配置管理器
        self._manager_cache: Dict[str, IConfigManager] = {}
        
        # 模块特定配置
        self._module_configs: Dict[str, Dict[str, Any]] = {
            "workflow": {
                "requires_inheritance": True,
                "requires_reference": True,
                "custom_validators": [],
                "description": "工作流模块配置管理器"
            },
            "llm": {
                "requires_inheritance": True,
                "requires_reference": False,
                "custom_validators": [],
                "description": "LLM模块配置管理器"
            },
            "tools": {
                "requires_inheritance": True,
                "requires_reference": True,
                "custom_validators": [],
                "description": "工具模块配置管理器"
            },
            "state": {
                "requires_inheritance": False,
                "requires_reference": False,
                "custom_validators": [],
                "description": "状态管理模块配置管理器"
            }
        }
        
        logger.info("Core层配置管理器工厂初始化完成")
    
    def get_manager(self, module_type: str) -> IConfigManager:
        """获取模块特定的配置管理器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置管理器实例
        """
        if module_type in self._manager_cache:
            return self._manager_cache[module_type]
        
        manager = self._create_manager(module_type)
        self._manager_cache[module_type] = manager
        return manager
    
    def _create_manager(self, module_type: str) -> IConfigManager:
        """创建模块特定的配置管理器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置管理器实例
        """
        module_config = self._module_configs.get(module_type, {})
        
        # 创建处理器链
        processor_chain = self._create_processor_chain(module_config)
        
        # 创建配置管理器
        manager = ConfigManager(
            config_loader=self.config_loader,
            processor_chain=processor_chain,
            base_path=self.base_path,
            inheritance_handler=self.inheritance_handler
        )
        
        # 注册模块特定验证器
        self._register_module_validators(manager, module_type, module_config)
        
        logger.info(f"创建{module_type}模块配置管理器完成")
        return manager
    
    def _create_processor_chain(self, module_config: Dict[str, Any]) -> ConfigProcessorChain:
        """创建处理器链
        
        Args:
            module_config: 模块配置
            
        Returns:
            配置处理器链
        """
        processor_chain = ConfigProcessorChain()
        
        # 根据模块配置添加处理器
        if module_config.get("requires_inheritance", False) and self.inheritance_handler:
            processor_chain.add_processor(self.inheritance_handler)
        
        if module_config.get("requires_reference", False):
            from src.infrastructure.config.processor import ReferenceProcessor
            processor_chain.add_processor(ReferenceProcessor())
        
        return processor_chain
    
    def _register_module_validators(self,
                                  manager: ConfigManager,
                                  module_type: str,
                                  module_config: Dict[str, Any]) -> None:
        """注册模块特定验证器
        
        Args:
            manager: 配置管理器
            module_type: 模块类型
            module_config: 模块配置
        """
        # 注册配置验证器
        try:
            from src.infrastructure.config.validation import ConfigValidator
            config_validator = ConfigValidator()
            manager.register_module_validator(module_type, config_validator)
            logger.debug(f"注册{module_type}模块配置验证器")
        except Exception as e:
            logger.error(f"注册配置验证器失败: {e}")
        
        # 注册自定义验证器
        custom_validators = module_config.get("custom_validators", [])
        
        for validator_class in custom_validators:
            try:
                validator = validator_class()
                manager.register_module_validator(module_type, validator)
                logger.debug(f"注册{module_type}模块验证器: {validator_class.__name__}")
            except Exception as e:
                logger.error(f"注册验证器失败 {validator_class.__name__}: {e}")
    
    def register_manager_decorator(self, module_type: str, decorator_class: Type) -> None:
        """注册管理器装饰器
        
        Args:
            module_type: 模块类型
            decorator_class: 装饰器类
        """
        # 清除缓存，强制重新创建
        if module_type in self._manager_cache:
            del self._manager_cache[module_type]
        
        # 更新模块配置
        if module_type not in self._module_configs:
            self._module_configs[module_type] = {}
        
        if "decorators" not in self._module_configs[module_type]:
            self._module_configs[module_type]["decorators"] = []
        
        self._module_configs[module_type]["decorators"].append(decorator_class)
        
        logger.info(f"注册{module_type}模块装饰器: {decorator_class.__name__}")
    
    def unregister_manager_decorator(self, module_type: str, decorator_class: Type) -> bool:
        """注销管理器装饰器
        
        Args:
            module_type: 模块类型
            decorator_class: 装饰器类
            
        Returns:
            是否成功注销
        """
        if module_type not in self._module_configs:
            return False
        
        decorators = self._module_configs[module_type].get("decorators", [])
        if decorator_class in decorators:
            decorators.remove(decorator_class)
            # 清除缓存，强制重新创建
            if module_type in self._manager_cache:
                del self._manager_cache[module_type]
            
            logger.info(f"注销{module_type}模块装饰器: {decorator_class.__name__}")
            return True
        
        return False
    
    def clear_manager_cache(self, module_type: Optional[str] = None) -> None:
        """清除管理器缓存
        
        Args:
            module_type: 模块类型，如果为None则清除所有缓存
        """
        if module_type:
            if module_type in self._manager_cache:
                del self._manager_cache[module_type]
                logger.debug(f"清除{module_type}模块管理器缓存")
        else:
            self._manager_cache.clear()
            logger.debug("清除所有管理器缓存")
    
    def get_registered_modules(self) -> list:
        """获取已注册的模块列表
        
        Returns:
            模块类型列表
        """
        return list(self._module_configs.keys())
    
    def get_active_managers(self) -> list:
        """获取活跃的管理器列表
        
        Returns:
            活跃管理器列表
        """
        return list(self._manager_cache.keys())
    
    def get_factory_status(self) -> Dict[str, Any]:
        """获取工厂状态信息
        
        Returns:
            工厂状态信息
        """
        return {
            "registered_modules": self.get_registered_modules(),
            "active_managers": self.get_active_managers(),
            "cache_size": len(self._manager_cache),
            "base_path": str(self.base_path),
            "has_inheritance_handler": self.inheritance_handler is not None
        }
    
    def register_module_config(self, module_type: str, config: Dict[str, Any]) -> None:
        """注册模块配置
        
        Args:
            module_type: 模块类型
            config: 模块配置
        """
        self._module_configs[module_type] = config
        # 清除缓存，强制重新创建
        if module_type in self._manager_cache:
            del self._manager_cache[module_type]
        
        logger.info(f"注册{module_type}模块配置")
    
    def get_module_config(self, module_type: str) -> Dict[str, Any]:
        """获取模块配置
        
        Args:
            module_type: 模块类型
            
        Returns:
            模块配置
        """
        return self._module_configs.get(module_type, {})


# 全局工厂实例
_global_factory: Optional[CoreConfigManagerFactory] = None


def set_global_factory(factory: CoreConfigManagerFactory) -> None:
    """设置全局配置管理器工厂
    
    Args:
        factory: 配置管理器工厂
    """
    global _global_factory
    _global_factory = factory


def get_global_factory() -> Optional[CoreConfigManagerFactory]:
    """获取全局配置管理器工厂
    
    Returns:
        配置管理器工厂实例
    """
    return _global_factory


def get_module_manager(module_type: str) -> Optional[IConfigManager]:
    """获取模块配置管理器（便捷函数）
    
    Args:
        module_type: 模块类型
        
    Returns:
        配置管理器实例
    """
    factory = get_global_factory()
    if factory:
        return factory.get_manager(module_type)
    return None


def register_module_decorator(module_type: str, decorator_class: Type) -> bool:
    """注册模块装饰器（便捷函数）
    
    Args:
        module_type: 模块类型
        decorator_class: 装饰器类
        
    Returns:
        是否成功注册
    """
    factory = get_global_factory()
    if factory:
        factory.register_manager_decorator(module_type, decorator_class)
        return True
    return False