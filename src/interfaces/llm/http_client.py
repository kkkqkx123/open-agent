"""HTTP客户端接口定义

定义HTTP客户端的标准契约，用于统一不同LLM提供商的HTTP通信。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Union, Sequence, Coroutine
from httpx import Response

# 使用 TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..messages import IBaseMessage


class IHttpClient(ABC):
    """HTTP客户端接口
    
    定义HTTP通信的标准契约，支持同步和异步请求、流式响应等。
    """
    
    @abstractmethod
    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """发送POST请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            headers: 请求头
            timeout: 超时时间
            
        Returns:
            Response: HTTP响应对象
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        pass
    
    @abstractmethod
    def stream_post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """发送流式POST请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            headers: 请求头
            timeout: 超时时间
            
        Yields:
            str: 流式响应数据片段
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        pass
    
    @abstractmethod
    def set_auth_header(self, token: str) -> None:
        """设置认证头部
        
        Args:
            token: 认证令牌
        """
        pass
    
    @abstractmethod
    def set_base_url(self, url: str) -> None:
        """设置基础URL
        
        Args:
            url: 基础URL
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭客户端连接
        
        清理资源，关闭连接池等。
        """
        pass


class ILLMHttpClient(IHttpClient):
    """LLM HTTP客户端接口
    
    扩展基础HTTP客户端接口，添加LLM特定的方法。
    """
    
    @property
    @abstractmethod
    def timeout(self) -> Optional[float]:
        """获取超时时间
        
        Returns:
            Optional[float]: 超时时间（秒）
        """
        pass
    
    @property
    @abstractmethod
    def max_retries(self) -> int:
        """获取最大重试次数
        
        Returns:
            int: 最大重试次数
        """
        pass
    
    @abstractmethod
    async def chat_completions(
        self,
        messages: Sequence["IBaseMessage"],
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union["LLMResponse", AsyncGenerator[str, None]]:
        """调用Chat Completions API
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 请求参数
            stream: 是否流式响应
            
        Returns:
            Union[LLMResponse, AsyncGenerator[str, None]]: 响应对象或流式生成器
        """
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: Sequence[Dict[str, Any]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """OpenAI风格的Chat Completion API
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数（model, temperature等）
            
        Returns:
            Dict[str, Any]: 响应对象
        """
        pass
    
    @abstractmethod
    def stream_chat_completion(
        self,
        messages: Sequence[Dict[str, Any]],
        **kwargs: Any
    ) -> Coroutine[Any, Any, AsyncGenerator[Dict[str, Any], None]]:
        """OpenAI风格的流式Chat Completion API
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            Coroutine that yields Dict[str, Any]: 流式响应块
        """
        pass
    
    @abstractmethod
    def async_stream_chat_completion(
        self,
        messages: Sequence[Dict[str, Any]],
        **kwargs: Any
    ) -> Coroutine[Any, Any, AsyncGenerator[Dict[str, Any], None]]:
        """OpenAI风格的异步流式Chat Completion API
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            Coroutine that yields Dict[str, Any]: 流式响应块
        """
        pass
    
    @abstractmethod
    async def generate_content(
        self,
        contents: Sequence[Dict[str, Any]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Gemini风格的Generate Content API
        
        Args:
            contents: 内容列表
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 响应对象
        """
        pass
    
    @abstractmethod
    def stream_generate_content(
        self,
        contents: Sequence[Dict[str, Any]],
        **kwargs: Any
    ) -> Coroutine[Any, Any, AsyncGenerator[Dict[str, Any], None]]:
        """Gemini风格的流式Generate Content API
        
        Args:
            contents: 内容列表
            **kwargs: 其他参数
            
        Returns:
            Coroutine that yields Dict[str, Any]: 流式响应块
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表
        
        Returns:
            list[str]: 支持的模型名称列表
        """
        pass


# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from ...infrastructure.llm.models import LLMResponse