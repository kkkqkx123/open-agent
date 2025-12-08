"""
提供商基类

提供所有提供商的通用实现。
"""

from typing import Dict, Any, List, Optional, Sequence, Union
from .base import BaseProvider, ConversionContext
from .message import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from src.interfaces.messages import IBaseMessage
from .utils import (
    process_content_to_list,
    extract_text_from_content,
    validate_tools,
    validate_stream_events,
    process_stream_events,
    safe_get
)


class ProviderBase(BaseProvider):
    """提供商基类"""
    
    def __init__(self, name: str):
        super().__init__(name)
    
    def convert_request(self, messages: Sequence[Union[BaseMessage, IBaseMessage]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换请求格式"""
        context = self._create_context("request", parameters)
        
        # 验证请求
        errors = self.validate_request(messages, parameters)
        if errors:
            context.add_error(f"请求验证失败: {', '.join(errors)}")
            raise ValueError(f"请求验证失败: {', '.join(errors)}")
        
        # 处理消息（转换为List并进行类型转换）
        processed_messages = self._process_messages(list(messages) if not isinstance(messages, list) else messages, context)  # type: ignore
        
        # 构建请求
        request_data = self._build_request(processed_messages, parameters, context)
        
        return request_data
    
    def convert_response(self, response: Dict[str, Any]) -> BaseMessage:
        """转换响应格式"""
        context = self._create_context("response", {"response": response})
        
        # 验证响应
        errors = self._validate_response(response, context)
        if errors:
            context.add_warning(f"响应验证警告: {', '.join(errors)}")
        
        # 构建消息
        return self._build_response(response, context)
    
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> BaseMessage:
        """转换流式响应格式"""
        context = self._create_context("stream", {"events": events})
        
        # 验证流式事件
        errors = validate_stream_events(events)
        if errors:
            context.add_warning(f"流式事件验证警告: {', '.join(errors)}")
        
        # 处理流式事件
        response = process_stream_events(events)
        return self._build_response(response, context)
    
    def _process_messages(self, messages: List[BaseMessage], context: ConversionContext) -> List[Dict[str, Any]]:
        """处理消息列表"""
        processed_messages = []
        
        for message in messages:
            processed_message = self._convert_message(message, context)
            if processed_message:
                processed_messages.append(processed_message)
        
        return processed_messages
    
    def _convert_message(self, message: BaseMessage, context: ConversionContext) -> Optional[Dict[str, Any]]:
        """转换单个消息"""
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
    
    def _convert_system_message(self, message: SystemMessage, context: ConversionContext) -> Dict[str, Any]:
        """转换系统消息"""
        return self._build_base_message(message, self._get_system_role(), context)
    
    def _convert_human_message(self, message: HumanMessage, context: ConversionContext) -> Dict[str, Any]:
        """转换人类消息"""
        return self._build_base_message(message, self._get_user_role(), context)
    
    def _convert_ai_message(self, message: AIMessage, context: ConversionContext) -> Dict[str, Any]:
        """转换AI消息"""
        provider_message = self._build_base_message(message, self._get_assistant_role(), context)
        
        # 添加工具调用
        if hasattr(message, 'tool_calls') and message.tool_calls:
            provider_message = self._add_tool_calls_to_message(provider_message, message.tool_calls, context)
        
        return provider_message
    
    def _convert_tool_message(self, message: ToolMessage, context: ConversionContext) -> Dict[str, Any]:
        """转换工具消息"""
        # 确保工具结果是字符串格式
        content = extract_text_from_content(process_content_to_list(message.content))
        
        provider_message = {
            "role": self._get_tool_role(),
            "content": content
        }
        
        # 添加工具调用ID
        if hasattr(message, 'tool_call_id') and message.tool_call_id:
            provider_message["tool_call_id"] = message.tool_call_id
        
        # 添加名称
        if message.name:
            provider_message["name"] = message.name
        
        return provider_message
    
    def _build_base_message(self, message: BaseMessage, role: str, context: ConversionContext) -> Dict[str, Any]:
        """构建基础消息"""
        # 处理内容
        content = self._process_content(message.content, context)
        
        # 构建消息
        provider_message = {
            "role": role,
            "content": content
        }
        
        # 添加名称
        if message.name:
            provider_message["name"] = message.name
        
        return provider_message
    
    def _process_content(self, content: Any, context: Optional[ConversionContext]) -> Any:
        """处理内容"""
        processed_content = process_content_to_list(content)
        
        # 如果是纯文本，直接返回字符串
        if len(processed_content) == 1 and processed_content[0].get("type") == "text":
            return processed_content[0].get("text", "")
        
        # 多模态内容返回列表
        return self._process_multimodal_content(processed_content, context)
    
    def _process_multimodal_content(self, content: List[Dict[str, Any]], context: Optional[ConversionContext]) -> List[Dict[str, Any]]:
        """处理多模态内容"""
        processed = []
        
        for item in content:
            if item.get("type") == "text":
                processed.append(item)
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
                "type": source.get("type", "base64"),
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
    
    def _add_tool_calls_to_message(self, message: Dict[str, Any], tool_calls: List[Dict[str, Any]], context: ConversionContext) -> Dict[str, Any]:
        """添加工具调用到消息"""
        message["tool_calls"] = tool_calls
        return message
    
    def _build_request(self, messages: List[Dict[str, Any]], parameters: Dict[str, Any], context: ConversionContext) -> Dict[str, Any]:
        """构建请求数据"""
        # 基础请求结构
        request_data = {
            "model": parameters.get("model", self.get_default_model()),
            "messages": messages
        }
        
        # 添加可选参数
        optional_params = self._get_optional_parameters()
        for param in optional_params:
            if param in parameters:
                request_data[param] = parameters[param]
        
        # 处理特殊参数
        self._handle_special_parameters(request_data, parameters, context)
        
        # 处理工具配置
        self._handle_tools_configuration(request_data, parameters, context)
        
        return request_data
    
    def _get_optional_parameters(self) -> List[str]:
        """获取可选参数列表"""
        return [
            "temperature", "top_p", "n", "stream", "stop",
            "max_tokens", "presence_penalty", "frequency_penalty"
        ]
    
    def _handle_special_parameters(self, request_data: Dict[str, Any], parameters: Dict[str, Any], context: ConversionContext) -> None:
        """处理特殊参数"""
        # 子类可以重写此方法来处理特殊参数
        pass
    
    def _handle_tools_configuration(self, request_data: Dict[str, Any], parameters: Dict[str, Any], context: ConversionContext) -> None:
        """处理工具配置"""
        if "tools" in parameters:
            tools = parameters["tools"]
            
            # 验证工具
            tool_errors = validate_tools(tools)
            if tool_errors:
                self.logger.warning(f"工具验证失败: {tool_errors}")
                return
            
            # 转换工具格式
            request_data["tools"] = self._convert_tools(tools, context)
            
            # 处理工具选择策略
            if "tool_choice" in parameters:
                request_data["tool_choice"] = self._process_tool_choice(parameters["tool_choice"], context)
    
    def _convert_tools(self, tools: List[Dict[str, Any]], context: ConversionContext) -> List[Dict[str, Any]]:
        """转换工具格式"""
        # 默认返回原格式，子类可以重写
        return tools
    
    def _process_tool_choice(self, tool_choice: Any, context: ConversionContext) -> Any:
        """处理工具选择策略"""
        # 默认返回原值，子类可以重写
        return tool_choice
    
    def _validate_response(self, response: Dict[str, Any], context: ConversionContext) -> List[str]:
        """验证响应格式"""
        errors = []
        
        if not isinstance(response, dict):
            errors.append("响应必须是字典格式")
            return errors
        
        choices = response.get("choices")
        if not choices:
            errors.append("响应缺少choices字段")
            return errors
        
        if not isinstance(choices, list) or not choices:
            errors.append("choices必须是非空列表")
            return errors
        
        return errors
    
    def _build_response(self, response: Dict[str, Any], context: ConversionContext) -> BaseMessage:
        """构建响应消息"""
        choices = response.get("choices", [])
        if not choices:
            raise ValueError("响应中没有choices字段")
        
        choice = choices[0]
        message = choice.get("message", {})
        
        # 提取基本信息
        role = message.get("role", "assistant")
        content = message.get("content", "")
        
        # 提取工具调用
        tool_calls = self._extract_tool_calls(response, context)
        
        # 构建额外参数
        additional_kwargs = self._build_response_metadata(response, choice, context)
        
        # 添加工具调用信息
        if tool_calls:
            additional_kwargs["tool_calls"] = tool_calls
        
        # 根据角色创建消息
        return self._create_message_from_role(role, content, tool_calls, additional_kwargs, context)
    
    def _extract_tool_calls(self, response: Dict[str, Any], context: ConversionContext) -> List[Dict[str, Any]]:
        """提取工具调用"""
        choices = response.get("choices", [])
        if not choices:
            return []
        
        message = choices[0].get("message", {})
        return message.get("tool_calls", [])
    
    def _build_response_metadata(self, response: Dict[str, Any], choice: Dict[str, Any], context: ConversionContext) -> Dict[str, Any]:
        """构建响应元数据"""
        return {
            "finish_reason": choice.get("finish_reason"),
            "usage": response.get("usage", {}),
            "model": response.get("model", ""),
            "id": response.get("id", ""),
            "created": response.get("created")
        }
    
    def _create_message_from_role(self, role: str, content: str, tool_calls: List[Dict[str, Any]], additional_kwargs: Dict[str, Any], context: ConversionContext) -> BaseMessage:
        """根据角色创建消息"""
        if role == self._get_assistant_role():
            return AIMessage(
                content=content or "",
                tool_calls=tool_calls if tool_calls else None,
                additional_kwargs=additional_kwargs
            )
        elif role == self._get_system_role():
            return SystemMessage(
                content=content or "",
                additional_kwargs=additional_kwargs
            )
        else:
            # 其他角色使用HumanMessage作为回退
            return HumanMessage(
                content=content or "",
                additional_kwargs=additional_kwargs
            )
    
    # 角色映射方法，子类可以重写
    def _get_system_role(self) -> str:
        """获取系统角色"""
        return "system"
    
    def _get_user_role(self) -> str:
        """获取用户角色"""
        return "user"
    
    def _get_assistant_role(self) -> str:
        """获取助手角色"""
        return "assistant"
    
    def _get_tool_role(self) -> str:
        """获取工具角色"""
        return "tool"