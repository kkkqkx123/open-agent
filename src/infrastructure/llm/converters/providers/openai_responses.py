"""
OpenAI Responses提供商实现

提供OpenAI Responses API的格式转换功能。
"""

from typing import Dict, Any, List, Optional
from ..provider import ProviderBase
from ..base import ConversionContext
from ..message import SystemMessage, HumanMessage, AIMessage, ToolMessage


class OpenAIResponsesProvider(ProviderBase):
    """OpenAI Responses提供商实现"""
    
    def __init__(self):
        super().__init__("openai-responses")
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return "gpt-4o"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
    
    def _convert_message(self, message, context: ConversionContext) -> Optional[Dict[str, Any]]:
        """转换单个消息"""
        # OpenAI Responses API使用不同的消息格式
        if isinstance(message, SystemMessage):
            return self._convert_system_message(message, context)
        elif isinstance(message, HumanMessage):
            return self._convert_human_message(message, context)
        elif isinstance(message, AIMessage):
            return self._convert_ai_message(message, context)
        elif isinstance(message, ToolMessage):
            return self._convert_tool_message(message, context)
        else:
            self.logger.warning(f"不支持的消息类型: {type(message)}")
            return None
    
    def _convert_system_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换系统消息"""
        # OpenAI Responses API将系统消息作为特殊参数处理
        return {
            "role": "system",
            "content": self._process_content(message.content, context)
        }
    
    def _convert_human_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换人类消息"""
        return {
            "role": "user",
            "input": self._process_content(message.content, context)
        }
    
    def _convert_ai_message(self, message, context: ConversionContext) -> Dict[str, Any]:
        """转换AI消息"""
        provider_message = {
            "role": "assistant",
            "output": self._process_content(message.content, context)
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
            "role": "tool",
            "output": content
        }
        
        # 添加工具调用ID
        if hasattr(message, 'tool_call_id') and message.tool_call_id:
            provider_message["tool_call_id"] = message.tool_call_id
        
        # 添加名称
        if message.name:
            provider_message["name"] = message.name
        
        return provider_message
    
    def _process_content(self, content: Any, context: Optional[ConversionContext]) -> Any:  # type: ignore
        """处理内容"""
        # OpenAI Responses API主要处理文本内容
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # 提取文本内容
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return " ".join(text_parts)
        else:
            return str(content)
    
    def _add_tool_calls_to_message(self, message: Dict[str, Any], tool_calls: List[Dict[str, Any]], context: ConversionContext) -> Dict[str, Any]:
        """添加工具调用到消息"""
        # OpenAI Responses API使用不同的工具调用格式
        function_calls = []
        
        for tool_call in tool_calls:
            if tool_call.get("type") == "function":
                function = tool_call.get("function", {})
                function_call = {
                    "name": function.get("name", ""),
                    "arguments": function.get("arguments", {})
                }
                function_calls.append(function_call)
        
        if function_calls:
            message["tool_calls"] = function_calls
        
        return message
    
    def _build_request(self, messages: List[Dict[str, Any]], parameters: Dict[str, Any], context: ConversionContext) -> Dict[str, Any]:
        """构建请求数据"""
        # OpenAI Responses API使用不同的请求结构
        request_data = {
            "model": parameters.get("model", self.get_default_model()),
            "messages": []
        }
        
        # 处理消息
        system_messages = []
        conversation_messages = []
        
        for message in messages:
            if message.get("role") == "system":
                system_messages.append(message)
            else:
                conversation_messages.append(message)
        
        # 添加系统消息作为参数
        if system_messages:
            system_content = []
            for sys_msg in system_messages:
                content = sys_msg.get("content", "")
                if content:
                    system_content.append(content)
            
            if system_content:
                request_data["system"] = " ".join(system_content)
        
        # 添加对话消息
        request_data["messages"] = conversation_messages
        
        # 添加可选参数
        optional_params = [
            "temperature", "top_p", "max_tokens", "stream",
            "stop", "presence_penalty", "frequency_penalty"
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
            
            # 转换为OpenAI Responses API工具格式
            responses_tools = self._convert_tools(tools, context)
            if responses_tools:
                request_data["tools"] = responses_tools
                
                # 处理工具选择策略
                if "tool_choice" in parameters:
                    request_data["tool_choice"] = self._process_tool_choice(parameters["tool_choice"], context)
    
    def _convert_tools(self, tools: List[Dict[str, Any]], context: ConversionContext) -> List[Dict[str, Any]]:
        """转换工具格式"""
        responses_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                responses_tool = {
                    "type": "function",
                    "function": {
                        "name": function.get("name", ""),
                        "description": function.get("description", ""),
                        "parameters": function.get("parameters", {})
                    }
                }
                responses_tools.append(responses_tool)
        
        return responses_tools
    
    def _process_tool_choice(self, tool_choice: Any, context: ConversionContext) -> Any:
        """处理工具选择策略"""
        # OpenAI Responses API支持的工具选择策略
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
    
    def _extract_tool_calls(self, response: Dict[str, Any], context: ConversionContext) -> List[Dict[str, Any]]:
        """提取工具调用"""
        # OpenAI Responses API的响应格式可能不同
        output = response.get("output", "")
        tool_calls = []
        
        # 这里需要根据实际的OpenAI Responses API响应格式来实现
        # 暂时返回空列表
        return tool_calls
    
    def _build_response(self, response: Dict[str, Any], context: ConversionContext):
        """构建响应消息"""
        from ..message import AIMessage
        
        # OpenAI Responses API的响应格式
        output = response.get("output", "")
        
        # 提取工具调用
        tool_calls = self._extract_tool_calls(response, context)
        
        # 构建额外参数
        additional_kwargs = {
            "model": response.get("model", ""),
            "usage": response.get("usage", {}),
            "finish_reason": response.get("finish_reason"),
            "id": response.get("id", "")
        }
        
        # 添加工具调用信息
        if tool_calls:
            additional_kwargs["tool_calls"] = tool_calls
        
        return AIMessage(
            content=output,
            tool_calls=tool_calls if tool_calls else None,
            additional_kwargs=additional_kwargs
        )