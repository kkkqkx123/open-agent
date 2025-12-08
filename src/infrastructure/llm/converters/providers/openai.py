"""
OpenAI提供商实现

提供OpenAI API的格式转换功能。
"""

from typing import Dict, Any, List
from ..provider import ProviderBase
from ..base import ConversionContext


class OpenAIProvider(ProviderBase):
    """OpenAI提供商实现"""
    
    def __init__(self):
        super().__init__("openai")
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return "gpt-3.5-turbo"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-vision-preview",
            "o1-preview",
            "o1-mini"
        ]
    
    def _get_optional_parameters(self) -> List[str]:
        """获取可选参数列表"""
        return [
            "temperature", "top_p", "n", "stream", "stop",
            "max_tokens", "presence_penalty", "frequency_penalty",
            "logit_bias", "user", "service_tier", "seed"
        ]
    
    def _handle_special_parameters(self, request_data: Dict[str, Any], parameters: Dict[str, Any], context: ConversionContext) -> None:
        """处理特殊参数"""
        # 处理response_format
        if "response_format" in parameters:
            request_data["response_format"] = parameters["response_format"]
        
        # 处理reasoning_effort (GPT-5特有)
        if "reasoning_effort" in parameters:
            request_data["reasoning_effort"] = parameters["reasoning_effort"]
        
        # 处理stream_options
        if "stream_options" in parameters:
            request_data["stream_options"] = parameters["stream_options"]
    
    def _convert_tools(self, tools: List[Dict[str, Any]], context: ConversionContext) -> List[Dict[str, Any]]:
        """转换工具格式"""
        # OpenAI工具格式已经是标准格式，直接返回
        return tools
    
    def _process_tool_choice(self, tool_choice: Any, context: ConversionContext) -> Any:
        """处理工具选择策略"""
        # OpenAI支持的工具选择策略
        if tool_choice == "required":
            return "required"
        elif tool_choice == "auto":
            return "auto"
        elif tool_choice == "none":
            return "none"
        elif isinstance(tool_choice, dict):
            return tool_choice
        else:
            return "auto"
    
    def _build_response_metadata(self, response: Dict[str, Any], choice: Dict[str, Any], context: ConversionContext) -> Dict[str, Any]:
        """构建响应元数据"""
        metadata = super()._build_response_metadata(response, choice, context)
        
        # 添加OpenAI特有的元数据
        metadata.update({
            "system_fingerprint": response.get("system_fingerprint"),
            "service_tier": response.get("service_tier")
        })
        
        return metadata