"""
LLM服务绑定
"""

from typing import Dict, Any
from src.interfaces.llm import ILLMService
from src.interfaces.container.core import ServiceLifetime

class LLMServiceBindings:
    """LLM服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册LLM服务"""
        # 注册LLM服务
        def llm_service():
            from src.infrastructure.llm.llm_service import LLMService
            return LLMService(config)
        
        container.register_factory(
            ILLMService,
            llm_service,
            lifetime=ServiceLifetime.SINGLETON
        )