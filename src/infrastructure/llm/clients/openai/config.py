"""OpenAI 客户端简化配置"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from ...config import LLMClientConfig


@dataclass
class OpenAIConfig(LLMClientConfig):
    """简化的 OpenAI 配置"""
    
    # API 格式选择 - 添加到基础配置中
    api_format: str = "chat_completion" # chat_completion | responses
    
    # Chat Completions 特定参数
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[Union[List[str], str]] = None
    
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
            if self.api_format == "responses":
                self.base_url = "https://api.openai.com/v1"
            else:
                self.base_url = "https://api.openai.com/v1"
        
        # 设置模型类型
        if not hasattr(self, 'model_type') or self.model_type == "":
            self.model_type = "openai"
    
    def is_chat_completion(self) -> bool:
        """检查是否使用 Chat Completions API"""
        return self.api_format == "chat_completion"
    
    def is_responses_api(self) -> bool:
        """检查是否使用 Responses API"""
        return self.api_format == "responses"
    
    def get_chat_completion_params(self) -> Dict[str, Any]:
        """获取 Chat Completions API 参数"""
        params: Dict[str, Any] = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        if self.stop:
            params["stop"] = self.stop
        
        return params
    
    def get_responses_params(self) -> Dict[str, Any]:
        """获取 Responses API 参数"""
        params: Dict[str, Any] = {
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            params["max_output_tokens"] = self.max_tokens
        
        if self.max_output_tokens:
            params["max_output_tokens"] = self.max_output_tokens
        
        if self.reasoning:
            params["reasoning"] = self.reasoning
        
        if self.store:
            params["store"] = self.store
        
        return params