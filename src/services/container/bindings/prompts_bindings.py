"""
提示词服务绑定
"""

from typing import Dict, Any
from src.interfaces.prompts import IPromptLoader
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class PromptsServiceBindings:
    """提示词服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册提示词服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册提示词注册表（先注册，因为加载器依赖它）
        def prompt_registry_factory():
            from src.services.prompts.registry import PromptRegistry
            from src.interfaces.prompts.models import PromptConfig
            from src.interfaces.prompts import IPromptLoader
            
            # 创建一个简单的加载器占位符，用于初始化
            class PlaceholderLoader(IPromptLoader):
                def __init__(self):
                    pass
                
                def load_prompt(self, category: str, name: str) -> str:
                    return f"Placeholder prompt for {category}.{name}"
                
                async def load_prompt_async(self, category: str, name: str) -> str:
                    return self.load_prompt(category, name)
                
                async def load_simple_prompt_async(self, file_path):
                    return "Placeholder content"
                
                async def load_composite_prompt_async(self, dir_path):
                    return "Placeholder content"
                
                async def load_prompts_async(self, category):
                    return {}
                
                async def load_all(self, registry):
                    pass
                
                def clear_cache(self):
                    pass
                
                async def list_prompts_async(self, category=None):
                    return []
                
                def list_prompts(self, category=None):
                    return []
                
                def exists(self, category, name):
                    return True
            
            config = PromptConfig(
                system_prompt=None,
                user_command=None,
                context=None,
                examples=None,
                constraints=None,
                format=None
            )
            
            registry = PromptRegistry(loader=PlaceholderLoader(), config=config)
            
            # 稍后会被真正的加载器替换
            return registry
        
        from src.interfaces.prompts import IPromptRegistry
        container.register_factory(
            IPromptRegistry,
            prompt_registry_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册提示词加载器
        def prompt_loader_factory():
            from src.services.prompts.loader import PromptLoader
            from src.interfaces.prompts import IPromptRegistry
            
            registry = container.get(IPromptRegistry)
            loader = PromptLoader(registry=registry)
            
            return loader
        
        container.register_factory(
            IPromptLoader,
            prompt_loader_factory,
            lifetime=ServiceLifetime.SINGLETON
        )