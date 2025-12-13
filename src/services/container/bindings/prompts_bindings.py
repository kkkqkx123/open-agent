"""
提示词服务绑定
"""

from typing import Dict, Any
from src.interfaces.prompts import IPromptLoader
from src.interfaces.container.core import ServiceLifetime

class PromptsServiceBindings:
    """提示词服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册提示词服务"""
        # 注册提示词加载器
        def prompt_loader():
            from src.infrastructure.prompts.prompt_loader import PromptLoader
            return PromptLoader(config)
        
        container.register_factory(
            IPromptLoader,
            prompt_loader,
            lifetime=ServiceLifetime.SINGLETON
        )