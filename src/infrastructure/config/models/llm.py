"""LLM配置模型

提供LLM客户端所需的基础配置数据结构，位于基础设施层。
不包含业务逻辑，仅作为数据容器。
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field


class LLMClientConfig(BaseModel):
    """LLM客户端配置数据模型
    
    包含LLM客户端所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """
    
    # 基础配置
    model_type: str = Field(..., description="模型类型：openai, gemini, anthropic等")
    model_name: str = Field(..., description="模型名称")
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


class OpenAIConfig(LLMClientConfig):
    """OpenAI客户端配置数据模型"""
    
    # API 格式选择
    api_format: str = Field("chat_completion", description="API格式: chat_completion | responses")
    
    # Chat Completions 特定参数
    stop: Optional[Union[List[str], str]] = Field(None, description="停止序列")
    
    # 高级参数
    top_logprobs: Optional[int] = Field(None, description="Top logprobs")
    service_tier: Optional[str] = Field(None, description="服务层级")
    safety_identifier: Optional[str] = Field(None, description="安全标识符")
    seed: Optional[int] = Field(None, description="随机种子")
    verbosity: Optional[str] = Field(None, description="详细级别")
    web_search_options: Optional[Dict[str, Any]] = Field(None, description="网页搜索选项")
    
    # Responses API 特定参数
    max_output_tokens: Optional[int] = Field(None, description="最大输出Token数")
    reasoning: Optional[Dict[str, Any]] = Field(None, description="推理配置")
    store: bool = Field(False, description="是否存储")


class MockConfig(LLMClientConfig):
    """Mock模型配置数据模型"""
    
    response_delay: float = Field(0.1, description="响应延迟")
    response_text: str = Field("This is a mock response.", description="响应文本")
    error_rate: float = Field(0.0, description="错误率")
    error_message: str = Field("Mock error", description="错误消息")
    error_types: List[str] = Field(default_factory=lambda: ["timeout", "rate_limit"], description="错误类型")


class GeminiConfig(LLMClientConfig):
    """Gemini客户端配置数据模型"""
    
    # Gemini特定参数
    candidate_count: int = Field(1, description="候选数量")
    stop_sequences: Optional[List[str]] = Field(None, description="停止序列")
    max_output_tokens: Optional[int] = Field(None, description="最大输出Token数")
    top_k: int = Field(40, description="Top-k采样")
    response_mime_type: Optional[str] = Field(None, description="响应MIME类型")
    thinking_config: Optional[Dict[str, Any]] = Field(None, description="思考配置")
    safety_settings: Optional[List[Dict[str, Any]]] = Field(None, description="安全设置")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="工具列表")
    tool_choice: Optional[Dict[str, Any]] = Field(None, description="工具选择")
    content_cache_enabled: Optional[bool] = Field(None, description="是否启用内容缓存")
    content_cache_display_name: Optional[str] = Field(None, description="内容缓存显示名称")


class AnthropicConfig(LLMClientConfig):
    """Anthropic客户端配置数据模型"""
    
    # Anthropic特定参数
    anthropic_max_tokens: int = Field(1000, description="最大Token数")
    stop_sequences: Optional[List[str]] = Field(None, description="停止序列")
    thinking_config: Optional[Dict[str, Any]] = Field(None, description="思考配置")
    response_format: Optional[Dict[str, Any]] = Field(None, description="响应格式")
    user: Optional[str] = Field(None, description="用户标识")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="工具列表")
    tool_choice: Optional[Dict[str, Any]] = Field(None, description="工具选择")


class HumanRelayConfig(LLMClientConfig):
    """Human Relay客户端配置数据模型"""
    
    # Human Relay特定参数
    mode: str = Field("single", description="模式：single | multi")
    max_history_length: int = Field(10, description="最大历史长度")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    incremental_prompt_template: Optional[str] = Field(None, description="增量提示词模板")
    metadata_config: Dict[str, Any] = Field(default_factory=dict, description="元数据配置")


__all__ = [
    "LLMClientConfig",
    "OpenAIConfig",
    "MockConfig",
    "GeminiConfig",
    "AnthropicConfig",
    "HumanRelayConfig"
]