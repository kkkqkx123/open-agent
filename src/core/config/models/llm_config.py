"""LLM配置模型"""

from typing import Dict, Any, Optional, List
from pydantic import Field, field_validator

from .base import BaseConfig


class LLMConfig(BaseConfig):
    """LLM配置模型"""

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