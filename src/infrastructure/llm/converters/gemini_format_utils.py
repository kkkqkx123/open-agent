"""Gemini格式转换工具类

提供Gemini API的格式转换功能。
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


class GeminiFormatUtils(BaseProviderFormatUtils):
    """Gemini格式转换工具类"""
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "gemini"
    
    def convert_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为Gemini API请求格式"""
        contents = []
        system_instruction = None
        
        for message in messages:
            if isinstance(message, SystemMessage):
                system_instruction = message.content
                continue
            
            role = "user" if isinstance(message, HumanMessage) else "model"
            
            # 处理内容
            if isinstance(message.content, str):
                parts: List[Dict[str, Any]] = [{"text": message.content}]
            elif isinstance(message.content, list):
                parts = message.content  # type: ignore
            else:
                parts = [{"text": str(message.content)}]
            
            content_dict = {
                "role": role,
                "parts": parts
            }
            
            contents.append(content_dict)
        
        request_data = {
            "contents": contents
        }
        
        if system_instruction:
            request_data["systemInstruction"] = {  # type: ignore
                "parts": [{"text": system_instruction}]
            }
        
        # 添加可选参数
        optional_params = [
            "temperature", "maxOutputTokens", "topP", "topK",
            "candidateCount", "stopSequences"
        ]
        
        generation_config = {}
        for param in optional_params:
            if param in parameters:
                generation_config[param] = parameters[param]
        
        if generation_config:
            request_data["generationConfig"] = generation_config  # type: ignore
        
        # 处理工具配置
        if "tools" in parameters:
            request_data["tools"] = self._convert_tools_to_gemini_format(parameters["tools"])
        
        return request_data
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从Gemini API响应转换"""
        candidate = response["candidates"][0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        # 提取文本内容
        text_parts = []
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        
        content_text = " ".join(text_parts)
        
        return AIMessage(
            content=content_text,
            additional_kwargs={
                "finishReason": candidate.get("finishReason"),
                "index": candidate.get("index"),
                "safetyRatings": candidate.get("safetyRatings", [])
            }
        )
    
    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为Gemini格式"""
        gemini_tools = []
        
        for tool in tools:
            function_declaration = {
                "name": tool["name"],
                "description": tool.get("description", "")
            }
            
            if "parameters" in tool:
                function_declaration["parameters"] = tool["parameters"]
            
            gemini_tools.append({
                "functionDeclarations": [function_declaration]
            })
        
        return gemini_tools