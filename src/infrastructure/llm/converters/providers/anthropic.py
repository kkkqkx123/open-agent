"""
Anthropic提供商实现

提供Anthropic API的格式转换功能。
"""

from typing import Dict, Any, List, Optional
from ..provider import ProviderBase
from ..base import ConversionContext


class AnthropicProvider(ProviderBase):
    """Anthropic提供商实现"""
    
    def __init__(self):
        super().__init__("anthropic")
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return "claude-3-sonnet-20240229"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    def _get_system_role(self) -> str:
        """获取系统角色"""
        return "user"  # Anthropic使用user角色发送系统消息
    
    def _get_user_role(self) -> str:
        """获取用户角色"""
        return "user"
    
    def _get_assistant_role(self) -> str:
        """获取助手角色"""
        return "assistant"
    
    def _convert_system_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换系统消息"""
        # Anthropic将系统消息作为第一个用户消息处理
        content = self._process_content(message.content, context)
        
        return {
            "role": "user",
            "content": content
        }
    
    def _process_multimodal_content(self, content: List[Dict[str, Any]], context: Optional[ConversionContext]) -> List[Dict[str, Any]]:
        """处理多模态内容"""
        processed = []
        
        for item in content:
            if item.get("type") == "text":
                processed.append({
                    "type": "text",
                    "text": item.get("text", "")
                })
            elif item.get("type") == "image":
                processed_image = self._process_image_content(item, context)
                if processed_image:
                    processed.append(processed_image)
        
        return processed
    
    def _process_image_content(self, image_item: Dict[str, Any], context: Optional[ConversionContext]) -> Optional[Dict[str, Any]]:
        """处理图像内容"""
        source = image_item.get("source", {})
        
        if not source:
            self.logger.warning("图像内容缺少source字段")
            return None
        
        # 验证图像数据
        media_type = source.get("media_type", "")
        image_data = source.get("data", "")
        
        if not self._is_supported_image_format(media_type):
            self.logger.warning(f"不支持的图像格式: {media_type}")
            return None
        
        if not image_data:
            self.logger.warning("图像内容缺少数据")
            return None
        
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_data
            }
        }
    
    def _is_supported_image_format(self, media_type: str) -> bool:
        """检查是否为支持的图像格式"""
        supported_formats = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp"
        }
        return media_type in supported_formats
    
    def _build_request(self, messages: List[Dict[str, Any]], parameters: Dict[str, Any], context: ConversionContext) -> Dict[str, Any]:
        """构建请求数据"""
        # Anthropic使用不同的请求结构
        request_data = {
            "model": parameters.get("model", self.get_default_model()),
            "messages": messages,
            "max_tokens": parameters.get("max_tokens", 1024)
        }
        
        # 添加可选参数
        optional_params = [
            "temperature", "top_p", "top_k", "stop_sequences",
            "stream", "system"
        ]
        
        for param in optional_params:
            if param in parameters:
                request_data[param] = parameters[param]
        
        # 处理工具配置
        self._handle_tools_configuration(request_data, parameters, context)
        
        return request_data
    
    def _handle_tools_configuration(self, request_data: Dict[str, Any], parameters: Dict[str, Any], context: ConversionContext) -> None:
        """处理工具配置"""
        if "tools" in parameters:
            tools = parameters["tools"]
            
            # 转换为Anthropic工具格式
            anthropic_tools = self._convert_tools(tools, context)
            if anthropic_tools:
                request_data["tools"] = anthropic_tools
                
                # 处理工具选择策略
                if "tool_choice" in parameters:
                    request_data["tool_choice"] = self._process_tool_choice(parameters["tool_choice"], context)
    
    def _convert_tools(self, tools: List[Dict[str, Any]], context: ConversionContext) -> List[Dict[str, Any]]:
        """转换工具格式"""
        anthropic_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                anthropic_tool = {
                    "name": function.get("name", ""),
                    "description": function.get("description", ""),
                    "input_schema": function.get("parameters", {})
                }
                anthropic_tools.append(anthropic_tool)
        
        return anthropic_tools
    
    def _process_tool_choice(self, tool_choice: Any, context: ConversionContext) -> Any:
        """处理工具选择策略"""
        if tool_choice == "auto":
            return {"type": "auto"}
        elif tool_choice == "any":
            return {"type": "any"}
        elif isinstance(tool_choice, dict) and "name" in tool_choice:
            return {"type": "tool", "name": tool_choice["name"]}
        else:
            return {"type": "auto"}
    
    def _extract_tool_calls(self, response: Dict[str, Any], context: ConversionContext) -> List[Dict[str, Any]]:
        """提取工具调用"""
        content = response.get("content", [])
        tool_calls = []
        
        for item in content:
            if item.get("type") == "tool_use":
                tool_call = {
                    "id": item.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": item.get("input", {})
                    }
                }
                tool_calls.append(tool_call)
        
        return tool_calls
    
    def _build_response(self, response: Dict[str, Any], context: ConversionContext):
        """构建响应消息"""
        from ..message import AIMessage, HumanMessage
        
        content = response.get("content", [])
        
        # 处理内容
        text_content = ""
        tool_calls = []
        
        for item in content:
            if item.get("type") == "text":
                text_content += item.get("text", "")
            elif item.get("type") == "tool_use":
                tool_call = {
                    "id": item.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": item.get("input", {})
                    }
                }
                tool_calls.append(tool_call)
        
        # 构建额外参数
        additional_kwargs = {
            "model": response.get("model", ""),
            "id": response.get("id", ""),
            "type": response.get("type", ""),
            "usage": response.get("usage", {}),
            "stop_reason": response.get("stop_reason"),
            "stop_sequence": response.get("stop_sequence")
        }
        
        # 添加工具调用信息
        if tool_calls:
            additional_kwargs["tool_calls"] = tool_calls
        
        return AIMessage(
            content=text_content,
            tool_calls=tool_calls if tool_calls else None,
            additional_kwargs=additional_kwargs
        )