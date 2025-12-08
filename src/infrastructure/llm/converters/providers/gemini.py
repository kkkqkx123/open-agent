"""
Gemini提供商实现

提供Gemini API的格式转换功能。
"""

from typing import Dict, Any, List, Optional
from ..provider import ProviderBase
from ..base import ConversionContext


class GeminiProvider(ProviderBase):
    """Gemini提供商实现"""
    
    def __init__(self):
        super().__init__("gemini")
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return "gemini-1.5-pro"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-pro-vision"
        ]
    
    def _get_system_role(self) -> str:
        """获取系统角色"""
        return "user"  # Gemini使用user角色发送系统消息
    
    def _get_user_role(self) -> str:
        """获取用户角色"""
        return "user"
    
    def _get_assistant_role(self) -> str:
        """获取助手角色"""
        return "model"
    
    def _convert_system_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换系统消息"""
        # Gemini将系统消息作为第一个用户消息处理
        content = self._process_content(message.content, context)
        
        return {
            "role": "user",
            "parts": content
        }
    
    def _convert_human_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换人类消息"""
        content = self._process_content(message.content, context)
        
        return {
            "role": "user",
            "parts": content
        }
    
    def _convert_ai_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换AI消息"""
        content = self._process_content(message.content, context)
        
        provider_message = {
            "role": "model",
            "parts": content
        }
        
        # 添加工具调用
        if hasattr(message, 'tool_calls') and message.tool_calls:
            provider_message = self._add_tool_calls_to_message(provider_message, message.tool_calls, context)
        
        return provider_message
    
    def _convert_tool_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换工具消息"""
        # 确保工具结果是字符串格式
        content = self._process_content(message.content, context)
        
        provider_message = {
            "role": "function",
            "parts": content
        }
        
        # 添加工具调用ID
        if hasattr(message, 'tool_call_id') and message.tool_call_id:
            provider_message["function_call_id"] = message.tool_call_id
        
        # 添加名称
        if message.name:
            provider_message["name"] = message.name
        
        return provider_message
    
    def _process_content(self, content: Any, context: Optional[ConversionContext]) -> List[Dict[str, Any]]:  # type: ignore
        """处理内容为Gemini格式"""
        processed_content = []
        
        if isinstance(content, str):
            processed_content.append({"text": content})
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    processed_content.append({"text": item})
                elif isinstance(item, dict):
                    if item.get("type") == "text":
                        processed_content.append({"text": item.get("text", "")})
                    elif item.get("type") == "image":
                        processed_image = self._process_image_content(item, context)
                        if processed_image:
                            processed_content.append(processed_image)
        else:
            processed_content.append({"text": str(content)})
        
        return processed_content
    
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
            "inline_data": {
                "mime_type": media_type,
                "data": image_data
            }
        }
    
    def _is_supported_image_format(self, media_type: str) -> bool:
        """检查是否为支持的图像格式"""
        supported_formats = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/heic",
            "image/heif"
        }
        return media_type in supported_formats
    
    def _add_tool_calls_to_message(self, message: Dict[str, Any], tool_calls: List[Dict[str, Any]], context: ConversionContext) -> Dict[str, Any]:
        """添加工具调用到消息"""
        # Gemini使用functionCall格式
        function_calls = []
        
        for tool_call in tool_calls:
            if tool_call.get("type") == "function":
                function = tool_call.get("function", {})
                function_call = {
                    "name": function.get("name", ""),
                    "args": function.get("arguments", {})
                }
                function_calls.append(function_call)
        
        if function_calls:
            message["function_calls"] = function_calls
        
        return message
    
    def _build_request(self, messages: List[Dict[str, Any]], parameters: Dict[str, Any], context: ConversionContext) -> Dict[str, Any]:
        """构建请求数据"""
        # Gemini使用不同的请求结构
        request_data = {
            "contents": messages,
            "generationConfig": {
                "temperature": parameters.get("temperature", 0.7),
                "topP": parameters.get("top_p", 0.8),
                "topK": parameters.get("top_k", 40),
                "maxOutputTokens": parameters.get("max_tokens", 1024),
                "stopSequences": parameters.get("stop", [])
            }
        }
        
        # 添加模型
        if "model" in parameters:
            request_data["model"] = f"models/{parameters['model']}"
        
        # 添加系统指令
        if "system_instruction" in parameters:
            request_data["systemInstruction"] = parameters["system_instruction"]
        
        # 处理工具配置
        self._handle_tools_configuration(request_data, parameters, context)
        
        return request_data
    
    def _handle_tools_configuration(self, request_data: Dict[str, Any], parameters: Dict[str, Any], context: ConversionContext) -> None:
        """处理工具配置"""
        if "tools" in parameters:
            tools = parameters["tools"]
            
            # 转换为Gemini工具格式
            gemini_tools = self._convert_tools(tools, context)
            if gemini_tools:
                request_data["tools"] = gemini_tools
                
                # 处理工具选择策略
                if "tool_choice" in parameters:
                    request_data["tool_config"] = self._process_tool_choice(parameters["tool_choice"], context)
    
    def _convert_tools(self, tools: List[Dict[str, Any]], context: ConversionContext) -> List[Dict[str, Any]]:
        """转换工具格式"""
        gemini_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                gemini_tool = {
                    "functionDeclarations": [{
                        "name": function.get("name", ""),
                        "description": function.get("description", ""),
                        "parameters": function.get("parameters", {})
                    }]
                }
                gemini_tools.append(gemini_tool)
        
        return gemini_tools
    
    def _process_tool_choice(self, tool_choice: Any, context: ConversionContext) -> Dict[str, Any]:
        """处理工具选择策略"""
        if tool_choice == "auto":
            return {"mode": "AUTO"}
        elif tool_choice == "any":
            return {"mode": "ANY"}
        elif tool_choice == "none":
            return {"mode": "NONE"}
        elif isinstance(tool_choice, dict) and "name" in tool_choice:
            return {
                "mode": "ANY",
                "allowed_function_names": [tool_choice["name"]]
            }
        else:
            return {"mode": "AUTO"}
    
    def _extract_tool_calls(self, response: Dict[str, Any], context: ConversionContext) -> List[Dict[str, Any]]:
        """提取工具调用"""
        candidates = response.get("candidates", [])
        tool_calls = []
        
        for candidate in candidates:
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            for part in parts:
                if "functionCall" in part:
                    function_call = part["functionCall"]
                    tool_call = {
                        "id": f"call_{function_call.get('name', '')}_{len(tool_calls)}",
                        "type": "function",
                        "function": {
                            "name": function_call.get("name", ""),
                            "arguments": function_call.get("args", {})
                        }
                    }
                    tool_calls.append(tool_call)
        
        return tool_calls
    
    def _build_response(self, response: Dict[str, Any], context: ConversionContext):
        """构建响应消息"""
        from ..message import AIMessage
        
        candidates = response.get("candidates", [])
        if not candidates:
            raise ValueError("响应中没有candidates字段")
        
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        # 处理内容
        text_content = ""
        tool_calls = []
        
        for part in parts:
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                function_call = part["functionCall"]
                tool_call = {
                    "id": f"call_{function_call.get('name', '')}_{len(tool_calls)}",
                    "type": "function",
                    "function": {
                        "name": function_call.get("name", ""),
                        "arguments": function_call.get("args", {})
                    }
                }
                tool_calls.append(tool_call)
        
        # 构建额外参数
        additional_kwargs = {
            "model": response.get("model", ""),
            "usage": response.get("usageMetadata", {}),
            "finish_reason": candidate.get("finishReason"),
            "index": candidate.get("index", 0)
        }
        
        # 添加工具调用信息
        if tool_calls:
            additional_kwargs["tool_calls"] = tool_calls
        
        return AIMessage(
            content=text_content,
            tool_calls=tool_calls if tool_calls else None,
            additional_kwargs=additional_kwargs
        )