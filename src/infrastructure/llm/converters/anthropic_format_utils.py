"""Anthropic格式转换工具类

提供Anthropic API的格式转换功能。
"""

from typing import Dict, Any, List, Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

from src.infrastructure.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from src.infrastructure.llm.converters.provider_format_utils import BaseProviderFormatUtils


class AnthropicFormatUtils(BaseProviderFormatUtils):
    """Anthropic格式转换工具类"""
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "anthropic"
    
    def convert_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为Anthropic API请求格式"""
        messages_list = []
        system_message = None
        
        for message in messages:
            if isinstance(message, SystemMessage):
                system_message = message.content
                continue
            
            role = "user" if isinstance(message, (HumanMessage, ToolMessage)) else "assistant"
            
            # 处理内容
            if isinstance(message.content, str):
                content: List[Dict[str, Any]] = [{"type": "text", "text": message.content}]
            elif isinstance(message.content, list):
                content = message.content  # type: ignore
            else:
                content = [{"type": "text", "text": str(message.content)}]
            
            message_dict = {
                "role": role,
                "content": content
            }
            
            messages_list.append(message_dict)
        
        request_data = {
            "model": parameters.get("model", "claude-3-sonnet-20240229"),
            "messages": messages_list,
            "max_tokens": parameters.get("max_tokens", 1024)
        }
        
        if system_message:
            request_data["system"] = system_message
        
        # 添加可选参数
        optional_params = [
            "temperature", "top_p", "top_k", "stop_sequences",
            "stream", "metadata"
        ]
        
        for param in optional_params:
            if param in parameters:
                request_data[param] = parameters[param]
        
        # 处理工具配置
        if "tools" in parameters:
            request_data["tools"] = self._convert_tools_to_anthropic_format(parameters["tools"])
        
        return request_data
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从Anthropic API响应转换"""
        content = response.get("content", [])
        
        # 提取文本内容
        text_parts = []
        tool_use_blocks = []
        
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "tool_use":
                    tool_use_blocks.append(item)
        
        content_text = " ".join(text_parts)
        
        additional_kwargs = {
            "stop_reason": response.get("stop_reason"),
            "stop_sequence": response.get("stop_sequence"),
            "usage": response.get("usage", {})
        }
        
        if tool_use_blocks:
            additional_kwargs["tool_use_blocks"] = tool_use_blocks
        
        return AIMessage(
            content=content_text,
            additional_kwargs=additional_kwargs
        )
    
    def _convert_tools_to_anthropic_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为Anthropic格式"""
        anthropic_tools = []
        
        for tool in tools:
            anthropic_tool = {
                "name": tool["name"],
                "description": tool.get("description", "")
            }
            
            if "parameters" in tool:
                anthropic_tool["input_schema"] = tool["parameters"]
            
            anthropic_tools.append(anthropic_tool)
        
        return anthropic_tools