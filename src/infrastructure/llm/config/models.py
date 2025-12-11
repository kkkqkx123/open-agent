"""LLM客户端配置模型

提供LLM客户端所需的配置模型，位于基础设施层。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field


class LLMClientConfig(BaseModel):
    """LLM客户端配置模型
    
    包含LLM客户端所需的所有配置属性。
    """
    
    # 基础配置
    model_type: str = Field(..., description="模型类型：openai, gemini, anthropic等")
    model_name: str = Field(..., description="模型名称：gpt-4, gemini-pro等")
    provider: Optional[str] = Field(None, description="提供商名称")
    
    # API配置
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    
    # 生成参数
    temperature: float = Field(0.7, description="生成温度")
    top_p: float = Field(1.0, description="Top-p采样")
    frequency_penalty: float = Field(0.0, description="频率惩罚")
    presence_penalty: float = Field(0.0, description="存在惩罚")
    max_tokens: Optional[int] = Field(None, description="最大Token数")
    
    # 函数调用配置
    functions: Optional[List[Dict[str, Any]]] = Field(None, description="可用函数列表")
    function_call: Optional[Dict[str, Any]] = Field(None, description="函数调用配置")
    
    # 其他配置
    timeout: int = Field(30, description="请求超时时间")
    max_retries: int = Field(3, description="最大重试次数")
    stream: bool = Field(False, description="是否启用流式响应")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMClientConfig":
        """从字典创建配置"""
        return cls(**data)


@dataclass
class OpenAIConfig(LLMClientConfig):
    """OpenAI客户端配置"""
    
    # API 格式选择
    api_format: str = "chat_completion"  # chat_completion | responses
    
    # Chat Completions 特定参数
    stop: Optional[Union[List[str], str]] = None
    
    # 高级参数
    top_logprobs: Optional[int] = None
    service_tier: Optional[str] = None
    safety_identifier: Optional[str] = None
    seed: Optional[int] = None
    verbosity: Optional[str] = None
    web_search_options: Optional[Dict[str, Any]] = None
    
    # Responses API 特定参数
    max_output_tokens: Optional[int] = None
    reasoning: Optional[Dict[str, Any]] = None
    store: bool = False
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 验证 API 格式
        if self.api_format not in ["chat_completion", "responses"]:
            raise ValueError(f"不支持的 API 格式: {self.api_format}")
        
        # 设置默认的 base_url
        if self.base_url is None:
            self.base_url = "https://api.openai.com/v1"
        
        # 设置模型类型
        if self.model_type == "":
            self.model_type = "openai"
    
    def is_chat_completion(self) -> bool:
        """检查是否使用 Chat Completions API"""
        return self.api_format == "chat_completion"
    
    def is_responses_api(self) -> bool:
        """检查是否使用 Responses API"""
        return self.api_format == "responses"


@dataclass
class MockConfig(LLMClientConfig):
    """Mock模型配置"""
    
    response_delay: float = 0.1
    response_text: str = "This is a mock response."
    error_rate: float = 0.0
    error_message: str = "Mock error"
    error_types: List[str] = field(default_factory=lambda: ["timeout", "rate_limit"])
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置默认值
        if self.model_type == "":
            self.model_type = "mock"
        if self.model_name == "":
            self.model_name = "mock-model"


@dataclass
class GeminiConfig(LLMClientConfig):
    """Gemini客户端配置"""
    
    # Gemini特定参数
    candidate_count: int = 1
    stop_sequences: Optional[List[str]] = None
    max_output_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置默认值
        if self.model_type == "":
            self.model_type = "gemini"


@dataclass
class AnthropicConfig(LLMClientConfig):
    """Anthropic客户端配置"""
    
    # Anthropic特定参数
    max_tokens: int = 1000
    stop_sequences: Optional[List[str]] = None
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置默认值
        if self.model_type == "":
            self.model_type = "anthropic"


@dataclass
class HumanRelayConfig(LLMClientConfig):
    """Human Relay客户端配置"""
    
    # Human Relay特定参数
    relay_mode: str = "interactive"  # interactive | batch
    timeout_seconds: int = 300
    prompt_template: Optional[str] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置默认值
        if self.model_type == "":
            self.model_type = "human_relay"


__all__ = [
    "LLMClientConfig",
    "OpenAIConfig",
    "MockConfig",
    "GeminiConfig",
    "AnthropicConfig",
    "HumanRelayConfig",
]