"""配置服务工厂

提供配置系统服务的创建和依赖注入管理。
"""

from typing import Optional
from pathlib import Path

from .core.interfaces import IConfigLoader, IConfigInheritanceHandler
from .core.merger import IConfigMerger, ConfigMerger
from .utils.validator import IConfigValidator, ConfigValidator
from .core.loader import YamlConfigLoader
from .utils.inheritance import ConfigInheritanceHandler
from .config_system import IConfigSystem, ConfigSystem
from .config_callback_manager import ConfigCallbackManager
from .error_recovery import ConfigErrorRecovery, ConfigValidatorWithRecovery


class ConfigServiceFactory:
    """配置服务工厂
    
    负责创建和配置配置系统的各种服务组件。
    """
    
    @staticmethod
    def create_config_system(
        base_path: str = "configs",
        enable_inheritance: bool = True,
        enable_error_recovery: bool = True,
        enable_callback_manager: bool = True
    ) -> IConfigSystem:
        """创建配置系统实例
        
        Args:
            base_path: 配置文件基础路径
            enable_inheritance: 是否启用配置继承
            enable_error_recovery: 是否启用错误恢复
            enable_callback_manager: 是否启用回调管理器
            
        Returns:
            配置系统实例
        """
        # 创建核心服务
        config_merger = ConfigMerger()
        config_validator = ConfigValidator()
        
        # 创建继承处理器（如果启用）
        inheritance_handler = None
        if enable_inheritance:
            inheritance_handler = ConfigInheritanceHandler()
        
        # 创建配置加载器
        config_loader = YamlConfigLoader(
            base_path=base_path,
            inheritance_handler=inheritance_handler
        )
        
        # 如果启用了继承，需要设置继承处理器的加载器引用
        if enable_inheritance and inheritance_handler:
            inheritance_handler.config_loader = config_loader
        
        # 创建配置系统
        config_system = ConfigSystem(
            config_loader=config_loader,
            config_merger=config_merger,
            config_validator=config_validator,
            base_path=base_path,
            enable_error_recovery=enable_error_recovery,
            enable_callback_manager=enable_callback_manager
        )
        
        return config_system
    
    @staticmethod
    def create_config_loader(
        base_path: str = "configs",
        enable_inheritance: bool = True
    ) -> IConfigLoader:
        """创建配置加载器实例
        
        Args:
            base_path: 配置文件基础路径
            enable_inheritance: 是否启用配置继承
            
        Returns:
            配置加载器实例
        """
        if enable_inheritance:
            # 创建继承处理器
            inheritance_handler = ConfigInheritanceHandler()
            loader = YamlConfigLoader(base_path, inheritance_handler)
            # 设置继承处理器的加载器引用
            inheritance_handler.config_loader = loader
            return loader
        else:
            return YamlConfigLoader(base_path, None)
    
    @staticmethod
    def create_config_validator() -> IConfigValidator:
        """创建配置验证器实例
        
        Returns:
            配置验证器实例
        """
        return ConfigValidator()
    
    @staticmethod
    def create_config_merger() -> IConfigMerger:
        """创建配置合并器实例
        
        Returns:
            配置合并器实例
        """
        return ConfigMerger()
    
    @staticmethod
    def create_config_with_recovery(
        base_path: str = "configs"
    ) -> IConfigSystem:
        """创建带错误恢复的配置系统
        
        Args:
            base_path: 配置文件基础路径
            
        Returns:
            配置系统实例
        """
        return ConfigServiceFactory.create_config_system(
            base_path=base_path,
            enable_inheritance=True,
            enable_error_recovery=True,
            enable_callback_manager=True
        )


# 便捷函数
def create_config_system(base_path: str = "configs") -> IConfigSystem:
    """创建配置系统的便捷函数
    
    Args:
        base_path: 配置文件基础路径
        
    Returns:
        配置系统实例
    """
    return ConfigServiceFactory.create_config_system(base_path)


def create_minimal_config_system(base_path: str = "configs") -> IConfigSystem:
    """创建最小配置系统（仅包含核心功能）
    
    Args:
        base_path: 配置文件基础路径
        
    Returns:
        配置系统实例
    """
    return ConfigServiceFactory.create_config_system(
        base_path=base_path,
        enable_inheritance=False,
        enable_error_recovery=False,
        enable_callback_manager=False
    )