"""
LLM接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class ILLMService(ABC):
    """LLM服务接口"""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def generate_chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """生成聊天回复"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        pass

__all__ = ["ILLMService"]