"""LLM配置模型"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from pydantic import Field, field_validator

from .base import BaseConfig

if TYPE_CHECKING:
    from src.infrastructure.config.models import ConfigData
    from ..mappers.llm import LLMConfigMapper


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

    # 转换方法
    @classmethod
    def from_config_data(cls, config_data: "ConfigData") -> "LLMConfig":
        """从基础配置数据创建领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            LLM领域模型
        """
        return LLMConfigMapper.config_data_to_llm_config(config_data)

    def to_config_data(self) -> "ConfigData":
        """转换为基础配置数据
        
        Returns:
            基础配置数据
        """
        return LLMConfigMapper.llm_config_to_config_data(self)

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