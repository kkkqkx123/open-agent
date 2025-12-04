"""LLM客户端工厂实现 - 重构版本

简化为直接使用 Core 层的 LLMFactory。
"""

from typing import List, Dict, Any, Optional

from src.interfaces.llm import IClientFactory, ILLMClient
from src.core.llm.factory import LLMFactory


class ClientFactory(IClientFactory):
    """客户端工厂实现 - 重构版本
    
    简化为直接使用 Core 层的 LLMFactory，减少不必要的抽象层。
    """
    
    def __init__(self, llm_factory: Optional[LLMFactory] = None):
        """
        初始化客户端工厂
        
        Args:
            llm_factory: LLM工厂实例
        """
        self.llm_factory = llm_factory or LLMFactory()
    
    def create_client(self, model_name: str) -> ILLMClient:
        """
        创建客户端实例
        
        Args:
            model_name: 模型名称
            
        Returns:
            ILLMClient: 客户端实例
        """
        # 使用LLMFactory创建客户端
        config = {"model_name": model_name}
        return self.llm_factory.create_client(config)
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            List[str]: 模型名称列表
        """
        # 从LLMFactory获取可用模型
        return self.llm_factory.list_supported_types()