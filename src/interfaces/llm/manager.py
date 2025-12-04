"""LLM管理器接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator, Sequence, TYPE_CHECKING
from .base import ILLMClient, LLMResponse

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from ..messages import IBaseMessage


class ILLMManager(ABC):
    """LLM管理器接口"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化LLM管理器"""
        pass
    
    @abstractmethod
    async def register_client(self, name: str, client: ILLMClient) -> None:
        """注册LLM客户端"""
        pass
    
    @abstractmethod
    async def unregister_client(self, name: str) -> None:
        """注销LLM客户端"""
        pass
    
    @abstractmethod
    async def get_client(self, name: Optional[str] = None) -> ILLMClient:
        """获取LLM客户端"""
        pass
    
    @abstractmethod
    async def list_clients(self) -> List[str]:
        """列出所有已注册的客户端"""
        pass
    
    @abstractmethod
    async def get_client_for_task(
        self,
        task_type: str,
        preferred_client: Optional[str] = None
    ) -> ILLMClient:
        """根据任务类型获取最适合的LLM客户端"""
        pass
    
    @abstractmethod
    async def execute_with_fallback(
        self,
        messages: Sequence["IBaseMessage"],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """使用降级机制执行LLM请求"""
        pass
    
    @abstractmethod
    def stream_with_fallback(
        self,
        messages: Sequence["IBaseMessage"],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """使用降级机制执行流式LLM请求"""
        pass
    
    @abstractmethod
    async def reload_clients(self) -> None:
        """重新加载所有LLM客户端"""
        pass