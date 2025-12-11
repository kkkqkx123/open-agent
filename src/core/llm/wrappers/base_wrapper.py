"""LLM包装器基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Sequence
from src.interfaces.dependency_injection import get_logger

from abc import ABC
from src.interfaces.llm import LLMResponse
from src.infrastructure.llm.models import TokenUsage
from src.interfaces.llm.exceptions import LLMError
from src.infrastructure.messages.types import HumanMessage

logger = get_logger(__name__)


class BaseLLMWrapper(ABC):
    """LLM包装器基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化包装器
        
        Args:
            name: 包装器名称
            config: 包装器配置
        """
        self.name = name
        self.config = config or {}
        self._metadata = {}
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0
        }
    
    @abstractmethod
    async def generate_async(
        self,
        messages: Sequence,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """异步生成"""
        pass
    
    @abstractmethod
    def generate(
        self,
        messages: Sequence,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """同步生成"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    async def stream_generate(
        self,
        messages: Sequence,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """流式生成（默认实现）"""
        # 默认实现：使用generate_async方法并模拟流式输出
        response = await self.generate_async(messages, parameters, **kwargs)
        content = response.content
        
        # 简单的分块输出
        chunk_size = 10
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]
    
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用（默认实现）"""
        return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取包装器元数据"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "config": self.config,
            "stats": self._stats.copy(),
            **self._metadata
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0
        }
    
    def _update_stats(self, success: bool, response_time: float) -> None:
        """更新统计信息"""
        self._stats["total_requests"] += 1
        self._stats["total_response_time"] += response_time
        
        if success:
            self._stats["successful_requests"] += 1
        else:
            self._stats["failed_requests"] += 1
        
        # 更新平均响应时间
        if self._stats["total_requests"] > 0:
            self._stats["avg_response_time"] = (
                self._stats["total_response_time"] / self._stats["total_requests"]
            )
    
    def _messages_to_prompt(self, messages: Sequence) -> str:
        """将消息列表转换为提示词"""
        if not messages:
            return ""
        
        prompt_parts = []
        for message in messages:
            if hasattr(message, 'content'):
                prompt_parts.append(str(message.content))
            else:
                prompt_parts.append(str(message))
        
        return "\n".join(prompt_parts)
    
    def _create_llm_response(
        self,
        content: str,
        model: str,
        token_usage: Optional[TokenUsage] = None,
        message: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """创建LLM响应"""
        return LLMResponse(
            content=content,
            model=model,
            tokens_used=token_usage.total_tokens if token_usage else 0,
            metadata=metadata or {}
        )