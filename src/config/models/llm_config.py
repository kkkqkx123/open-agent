"""LLM配置模型"""

from typing import Dict, Any, Optional, List
from pydantic import Field, field_validator

from .base import BaseConfig


class LLMConfig(BaseConfig):
    """LLM配置模型"""
    
    # 基础配置
    model_type: str = Field(..., description="模型类型：openai, gemini, anthropic等")
    model_name: str = Field(..., description="模型名称：gpt-4, gemini-pro等")
    
    # API配置
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    
    # 参数配置
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模型参数")
    
    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")
    
    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """验证模型类型"""
        allowed_types = ['openai', 'gemini', 'anthropic', 'claude', 'local']
        if v.lower() not in allowed_types:
            raise ValueError(f'模型类型必须是以下之一: {allowed_types}')
        return v.lower()
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """验证基础URL"""
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('基础URL必须以http://或https://开头')
        return v
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = self.headers.copy()
        if self.api_key:
            # 根据模型类型设置不同的认证头
            if self.model_type == 'openai':
                headers['Authorization'] = f'Bearer {self.api_key}'
            elif self.model_type == 'gemini':
                headers['x-goog-api-key'] = self.api_key
            elif self.model_type == 'anthropic':
                headers['x-api-key'] = self.api_key
        return headers
    
    def merge_parameters(self, other_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """合并参数"""
        result = self.parameters.copy()
        result.update(other_parameters)
        return result
    
    def is_openai_compatible(self) -> bool:
        """检查是否为OpenAI兼容模型"""
        return self.model_type in ['openai', 'local']
    
    def is_gemini(self) -> bool:
        """检查是否为Gemini模型"""
        return self.model_type == 'gemini'
    
    def is_anthropic(self) -> bool:
        """检查是否为Anthropic模型"""
        return self.model_type in ['anthropic', 'claude']