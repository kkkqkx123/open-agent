"""LLM配置模型"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, field_validator

from .base import BaseConfig

class LLMConfig(BaseConfig):
    """LLM配置领域模型
    
    包含业务逻辑和验证规则的LLM配置模型。
    """

    # 基础配置
    model_type: str = Field(..., description="模型类型：openai, gemini, anthropic等")
    model_name: str = Field(..., description="模型名称：gpt-4, gemini-pro等")
    provider: Optional[str] = Field(None, description="提供商名称")

    # API配置
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")

    # 参数配置
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模型参数")
    
    # 客户端配置参数
    temperature: float = Field(0.7, description="生成温度")
    top_p: float = Field(1.0, description="Top-p采样")
    frequency_penalty: float = Field(0.0, description="频率惩罚")
    presence_penalty: float = Field(0.0, description="存在惩罚")
    max_tokens: Optional[int] = Field(None, description="最大Token数")
    timeout: int = Field(30, description="请求超时时间")
    max_retries: int = Field(3, description="最大重试次数")
    stream: bool = Field(False, description="是否启用流式响应")
    
    # 函数调用配置
    functions: Optional[List[Dict[str, Any]]] = Field(None, description="可用函数列表")
    function_call: Optional[Dict[str, Any]] = Field(None, description="函数调用配置")

    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")
    
    # Token计数器配置
    token_counter: Optional[str] = Field(None, description="Token计数器配置名称")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """验证模型类型"""
        allowed_types = ["openai", "gemini", "anthropic", "claude", "local", "mock"]
        if v.lower() not in allowed_types:
            raise ValueError(f"模型类型必须是以下之一: {allowed_types}")
        return v.lower()

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """验证基础URL"""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("基础URL必须以http://或https://开头")
        return v

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值"""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值"""
        self.metadata[key] = value

    # 业务逻辑方法
    def is_openai_compatible(self) -> bool:
        """检查是否为OpenAI兼容模型"""
        return self.model_type in ["openai", "local"]

    def is_gemini(self) -> bool:
        """检查是否为Gemini模型"""
        return self.model_type == "gemini"

    def is_anthropic(self) -> bool:
        """检查是否为Anthropic模型"""
        return self.model_type in ["anthropic", "claude"]

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return self.provider or self.model_type

    def validate_business_rules(self) -> List[str]:
        """验证业务规则
        
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证必需字段
        if not self.model_type:
            errors.append("模型类型不能为空")
        
        if not self.model_name:
            errors.append("模型名称不能为空")
        
        # 验证API配置
        if self.model_type in ["openai", "anthropic", "gemini"] and not self.api_key:
            errors.append(f"{self.model_type}模型需要提供API密钥")
        
        # 验证URL格式
        if self.base_url and not self.base_url.startswith(("http://", "https://")):
            errors.append("API基础URL必须以http://或https://开头")
        
        return errors

    def is_valid(self) -> bool:
        """检查配置是否有效
        
        Returns:
            是否有效
        """
        return len(self.validate_business_rules()) == 0



    def get_generation_params(self) -> Dict[str, Any]:
        """获取生成参数
        
        Returns:
            生成参数字典
        """
        # 基础参数
        params = {
            "model": self.model_name,
            "temperature": self.get_parameter("temperature", 0.7),
            "top_p": self.get_parameter("top_p", 1.0),
            "frequency_penalty": self.get_parameter("frequency_penalty", 0.0),
            "presence_penalty": self.get_parameter("presence_penalty", 0.0),
        }
        
        # 可选参数
        max_tokens = self.get_parameter("max_tokens")
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        stop = self.get_parameter("stop")
        if stop:
            params["stop"] = stop
        
        return params

    def get_client_config(self) -> Dict[str, Any]:
        """获取客户端配置
        
        Returns:
            客户端配置字典
        """
        config = {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "headers": self.headers,
            "timeout": self.get_parameter("timeout", 30),
            "max_retries": self.get_parameter("max_retries", 3),
            "stream": self.get_parameter("stream", False),
        }
        
        if self.provider:
            config["provider"] = self.provider
        
        return config


class MockConfig(LLMConfig):
    """Mock LLM配置模型"""
    
    # Mock特定配置
    response_delay: float = Field(0.1, description="响应延迟")
    response_text: str = Field("This is a mock response.", description="响应文本")
    error_rate: float = Field(0.0, description="错误率")
    error_message: str = Field("Mock error", description="错误消息")
    error_types: List[str] = Field(default_factory=lambda: ["timeout", "rate_limit"], description="错误类型")
    
    def get_mock_response(self) -> str:
        """获取Mock响应文本"""
        return self.response_text
    
    def should_throw_error(self) -> bool:
        """检查是否应该抛出错误"""
        import random
        return self.error_rate > 0 and random.random() < self.error_rate


class OpenAIConfig(LLMConfig):
    """OpenAI LLM配置模型"""
    
    # OpenAI特定配置
    api_format: str = Field("chat_completion", description="API格式: chat_completion | responses")
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


class GeminiConfig(LLMConfig):
    """Gemini LLM配置模型"""
    
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


class AnthropicConfig(LLMConfig):
    """Anthropic LLM配置模型"""
    
    # Anthropic特定参数
    anthropic_max_tokens: int = Field(1000, description="最大Token数")
    stop_sequences: Optional[List[str]] = Field(None, description="停止序列")
    thinking_config: Optional[Dict[str, Any]] = Field(None, description="思考配置")
    response_format: Optional[Dict[str, Any]] = Field(None, description="响应格式")
    user: Optional[str] = Field(None, description="用户标识")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="工具列表")
    tool_choice: Optional[Dict[str, Any]] = Field(None, description="工具选择")


class HumanRelayConfig(LLMConfig):
    """Human Relay LLM配置模型"""
    
    # Human Relay特定参数
    mode: str = Field("single", description="模式：single | multi")
    max_history_length: int = Field(10, description="最大历史长度")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    incremental_prompt_template: Optional[str] = Field(None, description="增量提示词模板")
    metadata_config: Dict[str, Any] = Field(default_factory=dict, description="元数据配置")