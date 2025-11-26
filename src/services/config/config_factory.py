"""配置服务工厂

提供配置系统服务的创建和依赖注入管理。
"""

from typing import Optional, Dict, Any
from pathlib import Path

from ...core.config.config_manager import ConfigManager
from ..prompts.registry import PromptRegistry
from ..prompts.loader import PromptLoader
from ..prompts.injector import PromptInjector
from ..prompts.config import get_global_config_manager
from .discovery import ConfigDiscoverer


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
    
    @staticmethod
    async def create_prompt_system(
        config_manager: Optional[ConfigManager] = None,
        prompts_directory: str = "configs/prompts",
        auto_discover: bool = True
    ) -> Dict[str, Any]:
        """创建提示词系统
        
        Args:
            config_manager: 配置管理器实例
            prompts_directory: 提示词目录路径
            auto_discover: 是否自动发现提示词文件
            
        Returns:
            Dict[str, Any]: 包含 registry, loader, injector 的字典
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 1. 准备配置管理器
            if config_manager is None:
                config_manager = ConfigServiceFactory.create_config_manager()
            
            # 2. 创建提示词配置管理器
            prompt_config_manager = get_global_config_manager()
            
            # 3. 创建提示词注册表
            registry = PromptRegistry(
                loader=None,
                config=prompt_config_manager.create_config()
            )
            
            # 4. 创建提示词加载器
            loader = PromptLoader(registry=registry)
            
            # 5. 设置注册表的加载器
            registry._loader = loader
            
            # 6. 创建提示词注入器
            injector = PromptInjector(loader=loader)
            
            # 7. 自动发现并加载提示词
            if auto_discover:
                try:
                    discoverer = ConfigDiscoverer(str(Path(prompts_directory).parent))
                    discovery_result = discoverer.discover_configs(
                        scan_directories=["prompts"],
                        file_patterns=[r".*\.md$"]
                    )
                    logger.info(f"发现 {len(discovery_result.prompts)} 个提示词文件")
                    
                    # 加载发现的提示词
                    await loader.load_all(registry)
                    
                except Exception as e:
                    logger.warning(f"自动发现提示词失败，继续使用空注册表: {e}")
            
            # 8. 记录统计信息
            try:
                stats = await registry.get_stats()
                logger.info(f"提示词系统创建完成，共加载 {stats['total_prompts']} 个提示词")
            except Exception as e:
                logger.warning(f"获取提示词统计信息失败: {e}")
            
            return {
                "registry": registry,
                "loader": loader,
                "injector": injector,
                "config_manager": prompt_config_manager
            }
            
        except Exception as e:
            logger.error(f"创建提示词系统失败: {e}")
            raise


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


async def create_prompt_system(
    config_manager: Optional[ConfigManager] = None,
    prompts_directory: str = "configs/prompts",
    auto_discover: bool = True
) -> Dict[str, Any]:
    """创建提示词系统的便捷函数
    
    Args:
        config_manager: 配置管理器实例
        prompts_directory: 提示词目录路径
        auto_discover: 是否自动发现提示词文件
        
    Returns:
        Dict[str, Any]: 包含 registry, loader, injector 的字典
    """
    return await ConfigServiceFactory.create_prompt_system(
        config_manager=config_manager,
        prompts_directory=prompts_directory,
        auto_discover=auto_discover
    )


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