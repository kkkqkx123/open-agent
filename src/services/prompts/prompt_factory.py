"""提示词系统工厂

专门负责提示词系统的创建和管理。
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from src.interfaces.dependency_injection import get_logger

from ...core.config.config_facade import ConfigFacade
from .registry import PromptRegistry
from .loader import PromptLoader
from .injector import PromptInjector
from .config import get_global_config_manager
from ..config.discovery import ConfigDiscoverer
from ...interfaces.prompts.models import PromptConfig as PromptConfigModel

logger = get_logger(__name__)


class PromptSystemFactory:
    """提示词系统工厂
    
    专门负责创建和配置提示词系统的各种服务组件。
    """
    
    @staticmethod
    async def create_prompt_system(
        config_facade: Optional[ConfigFacade] = None,
        prompts_directory: str = "configs/prompts",
        auto_discover: bool = True
    ) -> Dict[str, Any]:
        """创建提示词系统
        
        Args:
            config_facade: 配置门面实例
            prompts_directory: 提示词目录路径
            auto_discover: 是否自动发现提示词文件
            
        Returns:
            Dict[str, Any]: 包含 registry, loader, injector 的字典
        """
        try:
            # 1. 准备配置门面
            if config_facade is None:
                from ...core.config.config_facade import initialize_config_facade
                from ...infrastructure.config import ConfigLoader
                config_loader = ConfigLoader()
                config_facade = initialize_config_facade(config_loader)
            
            # 2. 创建提示词配置管理器
            prompt_config_manager = get_global_config_manager()
            
            # 3. 创建提示词注册表和加载器（处理循环依赖）
            # 使用延迟初始化模式：先创建注册表，再创建加载器，最后建立双向引用
            from ...interfaces.prompts import IPromptLoader
            
            # 创建一个临时的加载器占位符
            class PlaceholderLoader(IPromptLoader):
                def __init__(self) -> None:
                    self._real_loader: Optional[PromptLoader] = None
                    
                def _set_real_loader(self, real_loader: PromptLoader) -> None:
                    self._real_loader = real_loader
                    
                def load_prompt(self, category: str, name: str) -> str:
                    if self._real_loader:
                        return self._real_loader.load_prompt(category, name)
                    raise NotImplementedError("加载器尚未初始化")
                
                async def load_prompt_async(self, category: str, name: str) -> str:
                    if self._real_loader:
                        return await self._real_loader.load_prompt_async(category, name)
                    raise NotImplementedError("加载器尚未初始化")
                
                def list_prompts(self, category: Optional[str] = None) -> List[str]:
                    if self._real_loader:
                        return self._real_loader.list_prompts(category)
                    return []
                
                def exists(self, category: str, name: str) -> bool:
                    if self._real_loader:
                        return self._real_loader.exists(category, name)
                    return False
            
            # 创建占位符加载器和注册表
            placeholder_loader = PlaceholderLoader()
            registry = PromptRegistry(
                loader=placeholder_loader,
                config=PromptConfigModel(
                    system_prompt=None,
                    rules=[],
                    user_command=None,
                    context=None,
                    examples=None,
                    constraints=None,
                    format=None
                )
            )
            
            # 4. 创建真正的提示词加载器
            loader = PromptLoader(registry=registry)
            
            # 5. 建立双向引用
            placeholder_loader._set_real_loader(loader)
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
    
    @staticmethod
    def create_prompt_registry(
        config: Optional[PromptConfigModel] = None,
        loader: Optional[Any] = None
    ) -> PromptRegistry:
        """创建提示词注册表
        
        Args:
            config: 提示词配置
            loader: 提示词加载器
            
        Returns:
            PromptRegistry: 提示词注册表实例
        """
        from .config import get_global_config_manager
        from ...interfaces.prompts import IPromptLoader
        
        if config is None:
            config = PromptConfigModel(
                system_prompt=None,
                rules=[],
                user_command=None,
                context=None,
                examples=None,
                constraints=None,
                format=None
            )
        
        if loader is None:
            # 创建一个占位符加载器
            class PlaceholderLoader(IPromptLoader):
                def __init__(self) -> None:
                    self._real_loader: Optional[PromptLoader] = None
                    
                def _set_real_loader(self, real_loader: PromptLoader) -> None:
                    self._real_loader = real_loader
                    
                def load_prompt(self, category: str, name: str) -> str:
                    if self._real_loader:
                        return self._real_loader.load_prompt(category, name)
                    raise NotImplementedError("加载器尚未初始化")
                
                async def load_prompt_async(self, category: str, name: str) -> str:
                    if self._real_loader:
                        return await self._real_loader.load_prompt_async(category, name)
                    raise NotImplementedError("加载器尚未初始化")
                
                def list_prompts(self, category: Optional[str] = None) -> List[str]:
                    if self._real_loader:
                        return self._real_loader.list_prompts(category)
                    return []
                
                def exists(self, category: str, name: str) -> bool:
                    if self._real_loader:
                        return self._real_loader.exists(category, name)
                    return False
            
            loader = PlaceholderLoader()
        
        return PromptRegistry(loader=loader, config=config)
    
    @staticmethod
    def create_prompt_loader(registry: PromptRegistry) -> PromptLoader:
        """创建提示词加载器
        
        Args:
            registry: 提示词注册表
            
        Returns:
            PromptLoader: 提示词加载器实例
        """
        return PromptLoader(registry=registry)
    
    @staticmethod
    def create_prompt_injector(
        loader: PromptLoader,
        cache: Optional[Any] = None
    ) -> PromptInjector:
        """创建提示词注入器
        
        Args:
            loader: 提示词加载器
            cache: 可选的缓存实例
            
        Returns:
            PromptInjector: 提示词注入器实例
        """
        return PromptInjector(loader=loader, cache=cache)


# 便捷函数
async def create_prompt_system(
    config_facade: Optional[ConfigFacade] = None,
    prompts_directory: str = "configs/prompts",
    auto_discover: bool = True
) -> Dict[str, Any]:
    """创建提示词系统的便捷函数
    
    Args:
        config_facade: 配置门面实例
        prompts_directory: 提示词目录路径
        auto_discover: 是否自动发现提示词文件
        
    Returns:
        Dict[str, Any]: 包含 registry, loader, injector 的字典
    """
    return await PromptSystemFactory.create_prompt_system(
        config_facade=config_facade,
        prompts_directory=prompts_directory,
        auto_discover=auto_discover
    )


def create_prompt_registry(
    config: Optional[Any] = None,
    loader: Optional[Any] = None
) -> PromptRegistry:
    """创建提示词注册表的便捷函数
    
    Args:
        config: 提示词配置
        loader: 提示词加载器
        
    Returns:
        PromptRegistry: 提示词注册表实例
    """
    return PromptSystemFactory.create_prompt_registry(config, loader)


def create_prompt_loader(registry: PromptRegistry) -> PromptLoader:
    """创建提示词加载器的便捷函数
    
    Args:
        registry: 提示词注册表
        
    Returns:
        PromptLoader: 提示词加载器实例
    """
    return PromptSystemFactory.create_prompt_loader(registry)


def create_prompt_injector(
    loader: PromptLoader,
    cache: Optional[Any] = None
) -> PromptInjector:
    """创建提示词注入器的便捷函数
    
    Args:
        loader: 提示词加载器
        cache: 可选的缓存实例
        
    Returns:
        PromptInjector: 提示词注入器实例
    """
    return PromptSystemFactory.create_prompt_injector(loader, cache)