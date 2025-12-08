"""LLM模块数据模型定义"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    # 避免运行时循环依赖
    from src.interfaces.messages import IBaseMessage

class MessageRole(Enum):
    """消息角色枚举"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class TokenUsage:
    """Token使用情况"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    # 缓存相关token统计
    cached_tokens: int = 0
    cached_prompt_tokens: int = 0
    cached_completion_tokens: int = 0
    
    # 音频相关token
    prompt_audio_tokens: int = 0
    completion_audio_tokens: int = 0
    
    # 推理相关token
    reasoning_tokens: int = 0
    
    # 预测相关token
    accepted_prediction_tokens: int = 0
    rejected_prediction_tokens: int = 0
    
    # 思考相关token（Gemini）
    thoughts_tokens: int = 0
    
    # 工具调用相关token
    tool_call_tokens: int = 0
    
    # 元数据（保持向后兼容）
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """合并Token使用情况"""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
            cached_prompt_tokens=self.cached_prompt_tokens + other.cached_prompt_tokens,
            cached_completion_tokens=self.cached_completion_tokens + other.cached_completion_tokens,
            prompt_audio_tokens=self.prompt_audio_tokens + other.prompt_audio_tokens,
            completion_audio_tokens=self.completion_audio_tokens + other.completion_audio_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            accepted_prediction_tokens=self.accepted_prediction_tokens + other.accepted_prediction_tokens,
            rejected_prediction_tokens=self.rejected_prediction_tokens + other.rejected_prediction_tokens,
            thoughts_tokens=self.thoughts_tokens + other.thoughts_tokens,
            tool_call_tokens=self.tool_call_tokens + other.tool_call_tokens,
            metadata={**self.metadata, **other.metadata},
        )
    
    def get_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        if self.total_tokens == 0:
            return 0.0
        return (self.cached_tokens / self.total_tokens) * 100
    
    def get_effective_tokens(self) -> int:
        """获取有效token数量（总token - 缓存token）"""
        return self.total_tokens - self.cached_tokens
    
    def get_audio_tokens(self) -> int:
        """获取音频token总数"""
        return self.prompt_audio_tokens + self.completion_audio_tokens
    
    def get_prediction_tokens(self) -> int:
        """获取预测token总数"""
        return self.accepted_prediction_tokens + self.rejected_prediction_tokens


@dataclass
class LLMMessage:
    """LLM消息模型"""

    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result: Dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.name:
            result["name"] = self.name

        if self.function_call:
            result["function_call"] = self.function_call

        if self.tool_calls:
            result["tool_calls"] = self.tool_calls

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @classmethod
    def from_base_message(cls, message: "IBaseMessage") -> "LLMMessage":
        """从基础消息创建LLMMessage"""
        try:
            # 尝试使用新的消息系统
            from ...infrastructure.messages.types import (
                HumanMessage as InfraHumanMessage,
                AIMessage as InfraAIMessage,
                SystemMessage as InfraSystemMessage
            )
            
            if isinstance(message, InfraHumanMessage):
                role = MessageRole.USER
            elif isinstance(message, InfraAIMessage):
                role = MessageRole.ASSISTANT
            elif isinstance(message, InfraSystemMessage):
                role = MessageRole.SYSTEM
            else:
                # 回退到类型检查
                if hasattr(message, 'type'):
                    if message.type == "human":
                        role = MessageRole.USER
                    elif message.type == "ai":
                        role = MessageRole.ASSISTANT
                    elif message.type == "system":
                        role = MessageRole.SYSTEM
                    else:
                        role = MessageRole.USER
                else:
                    role = MessageRole.USER  # 默认为用户角色

            # 提取函数调用信息
            function_call = None
            if (
                hasattr(message, "additional_kwargs")
                and "function_call" in message.additional_kwargs
            ):
                function_call = message.additional_kwargs["function_call"]

            # 处理内容类型 - 消息内容可以是字符串或列表
            content = message.content
            if isinstance(content, list):
                # 如果是列表，提取文本内容
                content = " ".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                    if isinstance(item, (dict, str))
                )
            elif not isinstance(content, str):
                content = str(content)

            # 提取工具调用信息
            tool_calls = None
            # AIMessage有tool_calls属性
            from ...infrastructure.messages.types import AIMessage as InfraAIMessage
            if isinstance(message, InfraAIMessage) and message.tool_calls:
                tool_calls = message.tool_calls
            elif hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
                tool_calls = message.additional_kwargs["tool_calls"]

            return cls(
                role=role,
                content=content,
                name=getattr(message, "name", None),
                function_call=function_call,
                tool_calls=tool_calls,
                metadata=getattr(message, "additional_kwargs", {}),
            )
        except ImportError:
            # 如果无法导入新消息系统，使用默认值
            role = MessageRole.USER
            content = str(getattr(message, "content", ""))
            return cls(
                role=role,
                content=content,
                name=getattr(message, "name", None),
                function_call=None,
                tool_calls=None,
                metadata=getattr(message, "additional_kwargs", {}),
            )


@dataclass
class LLMResponse:
    """LLM响应模型"""

    content: str
    message: Any  # 接受任何消息类型（BaseMessage或IBaseMessage）
    token_usage: TokenUsage
    model: str
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_time: Optional[float] = None  # 响应时间（秒）
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result: Dict[str, Any] = {
            "content": self.content,
            "model": self.model,
            "token_usage": {
                "prompt_tokens": self.token_usage.prompt_tokens,
                "completion_tokens": self.token_usage.completion_tokens,
                "total_tokens": self.token_usage.total_tokens,
            },
            "timestamp": self.timestamp.isoformat(),
        }

        if self.finish_reason:
            result["finish_reason"] = self.finish_reason

        if self.function_call:
            result["function_call"] = self.function_call

        if self.metadata:
            result["metadata"] = self.metadata

        if self.response_time is not None:
            result["response_time"] = self.response_time

        return result


@dataclass
class LLMError:
    """LLM错误模型"""

    error_type: str
    error_message: str
    error_code: Optional[str] = None
    retry_after: Optional[int] = None  # 重试等待时间（秒）
    is_retryable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result: Dict[str, Any] = {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "is_retryable": self.is_retryable,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.error_code:
            result["error_code"] = self.error_code

        if self.retry_after is not None:
            result["retry_after"] = self.retry_after

        if self.metadata:
            result["metadata"] = self.metadata

        return result


@dataclass
class LLMRequest:
    """LLM请求模型"""

    messages: List["IBaseMessage"]
    parameters: Dict[str, Any] = field(default_factory=dict)
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value

    def merge_parameters(self, other_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """合并参数"""
        result = self.parameters.copy()
        result.update(other_parameters)
        return result


@dataclass
class ModelInfo:
    """模型信息"""

    name: str
    type: str  # openai, gemini, anthropic等
    max_tokens: Optional[int] = None
    context_length: Optional[int] = None
    supports_function_calling: bool = False
    supports_streaming: bool = True
    pricing: Optional[Dict[str, float]] = None  # 每千token价格
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "supports_function_calling": self.supports_function_calling,
            "supports_streaming": self.supports_streaming,
        }

        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens

        if self.context_length is not None:
            result["context_length"] = self.context_length

        if self.pricing:
            result["pricing"] = self.pricing

        if self.metadata:
            result["metadata"] = self.metadata

        return result


@dataclass
class FallbackConfig:
    """降级配置"""

    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0  # 重试延迟（秒）
    backoff_factor: float = 2.0  # 退避因子
    fallback_models: List[str] = field(default_factory=list)  # 降级模型列表
    retry_on_errors: List[str] = field(
        default_factory=lambda: [
            "rate_limit_exceeded",
            "temporary_error",
            "service_unavailable",
        ]
    )

    def should_retry(self, error_type: str, attempt: int) -> bool:
        """判断是否应该重试"""
        return (
            self.enabled
            and attempt < self.max_retries
            and error_type in self.retry_on_errors
        )

    def get_retry_delay(self, attempt: int) -> float:
        """获取重试延迟"""
        return self.retry_delay * (self.backoff_factor ** (attempt - 1))
