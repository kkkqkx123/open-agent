"""配置服务工厂

提供配置系统服务的创建和依赖注入管理。
"""

from typing import Optional
from pathlib import Path

from ...core.config.config_manager import ConfigManager


class ConfigServiceFactory:
    """配置服务工厂
    
    负责创建和配置配置系统的各种服务组件。
    """
    
    @staticmethod
    def create_config_manager(
        base_path: str = "configs",
        use_cache: bool = True,
        auto_reload: bool = False,
        enable_error_recovery: bool = True,
        enable_callback_manager: bool = True
    ) -> ConfigManager:
        """创建配置管理器实例
        
        Args:
            base_path: 配置文件基础路径
            use_cache: 是否使用缓存
            auto_reload: 是否自动重载
            enable_error_recovery: 是否启用错误恢复
            enable_callback_manager: 是否启用回调管理器
            
        Returns:
            配置管理器实例
        """
        return ConfigManager(
            base_path=Path(base_path),
            use_cache=use_cache,
            auto_reload=auto_reload,
            enable_error_recovery=enable_error_recovery,
            enable_callback_manager=enable_callback_manager
        )
    
    @staticmethod
    def create_config_with_recovery(
        base_path: str = "configs"
    ) -> ConfigManager:
        """创建带错误恢复的配置管理器
        
        Args:
            base_path: 配置文件基础路径
            
        Returns:
            配置管理器实例
        """
        return ConfigServiceFactory.create_config_manager(
            base_path=base_path,
            use_cache=True,
            auto_reload=False,
            enable_error_recovery=True,
            enable_callback_manager=True
        )
    
    @staticmethod
    def create_minimal_config_manager(
        base_path: str = "configs"
    ) -> ConfigManager:
        """创建最小配置管理器（仅包含核心功能）
        
        Args:
            base_path: 配置文件基础路径
            
        Returns:
            配置管理器实例
        """
        return ConfigServiceFactory.create_config_manager(
            base_path=base_path,
            use_cache=False,
            auto_reload=False,
            enable_error_recovery=False,
            enable_callback_manager=False
        )


# 便捷函数
def create_config_manager(base_path: str = "configs") -> ConfigManager:
    """创建配置管理器的便捷函数
    
    Args:
        base_path: 配置文件基础路径
        
    Returns:
        配置管理器实例
    """
    return ConfigServiceFactory.create_config_manager(base_path)


def create_minimal_config_manager(base_path: str = "configs") -> ConfigManager:
    """创建最小配置管理器（仅包含核心功能）
    
    Args:
        base_path: 配置文件基础路径
        
    Returns:
        配置管理器实例
    """
    return ConfigServiceFactory.create_minimal_config_manager(base_path)


# 为了兼容性，保留ConfigFactory类
class ConfigFactory:
    """配置工厂 - 保持向后兼容性"""
    
    @staticmethod
    def create_config_system(base_path: str = "configs") -> ConfigManager:
        """创建配置系统"""
        return create_config_manager(base_path)
    
    @staticmethod
    def create_minimal_config_system(base_path: str = "configs") -> ConfigManager:
        """创建最小配置系统（仅核心功能）"""
        return create_minimal_config_manager(base_path)


# 为了兼容性，保留便捷函数
def create_config_system_legacy(base_path: str = "configs") -> ConfigManager:
    """创建配置系统的便捷函数（已弃用，请使用config_service_factory中的版本）"""
    return ConfigFactory.create_config_system(base_path)