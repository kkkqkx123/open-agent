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
        
        # 基础参数
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        if self.stop:
            params["stop"] = self.stop
        
        # 高级参数
        if self.top_logprobs is not None:
            params["top_logprobs"] = self.top_logprobs
        
        if self.service_tier:
            params["service_tier"] = self.service_tier
        
        if self.safety_identifier:
            params["safety_identifier"] = self.safety_identifier
        
        if self.seed is not None:
            params["seed"] = self.seed
        
        if self.verbosity:
            params["verbosity"] = self.verbosity
        
        if self.web_search_options:
            params["web_search_options"] = self.web_search_options
        
        # 工具调用参数
        if self.tool_choice:
            params["tool_choice"] = self.tool_choice
        
        if self.tools:
            params["tools"] = self.tools
        
        # 响应格式参数
        if self.response_format:
            params["response_format"] = self.response_format
        
        # 流式选项
        if self.stream_options:
            params["stream_options"] = self.stream_options
        
        # 用户标识
        if self.user:
            params["user"] = self.user
        
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