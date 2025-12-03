"""Anthropic格式转换工具类

提供Anthropic API的格式转换功能。
"""

from typing import Dict, Any, List, Union, Optional, Sequence
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
from .anthropic_multimodal_utils import AnthropicMultimodalUtils
from .anthropic_tools_utils import AnthropicToolsUtils
from .anthropic_stream_utils import AnthropicStreamUtils
from .anthropic_validation_utils import AnthropicValidationUtils, AnthropicValidationError, AnthropicFormatError


class AnthropicFormatUtils(BaseProviderFormatUtils):
    """Anthropic格式转换工具类"""
    
    def __init__(self) -> None:
        """初始化Anthropic格式工具"""
        super().__init__()
        self.multimodal_utils = AnthropicMultimodalUtils()
        self.tools_utils = AnthropicToolsUtils()
        self.stream_utils = AnthropicStreamUtils()
        self.validation_utils = AnthropicValidationUtils()
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "anthropic"
    
    def convert_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为Anthropic API请求格式"""
        try:
            # 验证请求参数
            validation_errors = self.validation_utils.validate_request_parameters(parameters)
            if validation_errors:
                raise AnthropicValidationError(f"请求参数验证失败: {'; '.join(validation_errors)}")
            
            messages_list = []
            system_message = None
            
            # 处理消息
            for message in messages:
                if isinstance(message, SystemMessage):
                    system_message = self._extract_system_message_content(message)
                    continue
                
                role = "user" if isinstance(message, (HumanMessage, ToolMessage)) else "assistant"
                
                # 使用多模态工具处理内容
                content = self.multimodal_utils.process_content_to_anthropic_format(message.content)
                
                # 处理工具消息的特殊情况
                if isinstance(message, ToolMessage):
                    content = self._process_tool_message_content(message, content)
                
                message_dict = {
                    "role": role,
                    "content": content
                }
                
                # 添加消息名称（如果有）
                if message.name:
                    message_dict["name"] = message.name
                
                messages_list.append(message_dict)
            
            # 构建请求数据
            request_data = {
                "model": parameters.get("model", "claude-sonnet-4-5"),
                "messages": messages_list,
                "max_tokens": parameters.get("max_tokens", 1024)
            }
            
            # 添加系统消息
            if system_message:
                request_data["system"] = system_message
            
            # 添加可选参数
            optional_params = [
                "temperature", "top_p", "top_k", "stop_sequences", "stream"
            ]
            
            for param in optional_params:
                if param in parameters:
                    request_data[param] = parameters[param]
            
            # 处理元数据
            if "metadata" in parameters:
                request_data["metadata"] = parameters["metadata"]
            
            # 处理工具配置
            if "tools" in parameters:
                tools = parameters["tools"]
                # 验证工具
                tool_errors = self.tools_utils.validate_tools(tools)
                if tool_errors:
                    self.logger.warning(f"工具验证失败: {tool_errors}")
                else:
                    request_data["tools"] = self.tools_utils.convert_tools_to_anthropic_format(tools)
                    
                    # 处理工具选择策略
                    if "tool_choice" in parameters:
                        request_data["tool_choice"] = self.tools_utils.process_tool_choice(
                            parameters["tool_choice"]
                        )
            
            return request_data
        except AnthropicValidationError:
            raise
        except Exception as e:
            raise AnthropicFormatError(f"转换Anthropic请求失败: {e}")
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从Anthropic API响应转换"""
        try:
            # 验证响应格式
            validation_errors = self.validation_utils.validate_response(response)
            if validation_errors:
                self.logger.warning(f"响应格式验证失败: {'; '.join(validation_errors)}")
            
            content = response.get("content", [])
            
            # 提取文本内容和工具调用
            text_parts = []
            tool_calls = []
            
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "tool_use":
                        tool_call = self.tools_utils._extract_single_tool_call(item)
                        if tool_call:
                            tool_calls.append(tool_call)
            
            content_text = " ".join(text_parts)
            
            # 构建额外参数
            additional_kwargs = {
                "stop_reason": response.get("stop_reason"),
                "stop_sequence": response.get("stop_sequence"),
                "usage": response.get("usage", {}),
                "model": response.get("model", ""),
                "id": response.get("id", "")
            }
            
            # 添加工具调用信息
            if tool_calls:
                additional_kwargs["tool_calls"] = tool_calls
            
            # 添加原始工具使用块（用于调试）
            tool_use_blocks = [item for item in content if isinstance(item, dict) and item.get("type") == "tool_use"]
            if tool_use_blocks:
                additional_kwargs["tool_use_blocks"] = tool_use_blocks
            
            return AIMessage(
                content=content_text,
                tool_calls=tool_calls if tool_calls else None,
                additional_kwargs=additional_kwargs
            )
        except Exception as e:
            raise AnthropicFormatError(f"转换Anthropic响应失败: {e}")
    
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """从Anthropic流式响应转换"""
        try:
            # 验证流式事件
            validation_errors = self.stream_utils.validate_stream_events(events)
            if validation_errors:
                self.logger.warning(f"流式事件验证失败: {'; '.join(validation_errors)}")
            
            # 使用流式工具处理事件
            response = self.stream_utils.process_stream_events(events)
            return self.convert_response(response)
        except Exception as e:
            raise AnthropicFormatError(f"转换Anthropic流式响应失败: {e}")
    
    def _extract_system_message_content(self, message: SystemMessage) -> str:
        """提取系统消息内容"""
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, list):
            # 确保列表中的元素都是字典格式
            content_list = []
            for item in message.content:
                if isinstance(item, dict):
                    content_list.append(item)
                else:
                    content_list.append({"type": "text", "text": str(item)})
            return self.multimodal_utils.extract_text_from_anthropic_content(content_list)
        else:
            return str(message.content)
    
    def _process_tool_message_content(
        self,
        message: ToolMessage,
        content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """处理工具消息内容"""
        # 确保工具结果是字符串或字典格式
        tool_result_content = message.content
        if isinstance(tool_result_content, list):
            # 如果是列表，手动提取文本内容
            text_parts = []
            for item in tool_result_content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                else:
                    text_parts.append(str(item))
            tool_result_content = " ".join(text_parts)
        elif not isinstance(tool_result_content, (str, dict)):
            tool_result_content = str(tool_result_content)
        
        # 创建工具结果内容
        tool_result = self.tools_utils.create_tool_result_content(
            message.tool_call_id,
            tool_result_content
        )
        
        # 如果有其他内容，合并
        if len(content) == 1 and content[0].get("type") == "text":
            # 只有文本内容，替换为工具结果
            return [tool_result]
        else:
            # 有多模态内容，添加工具结果
            content.append(tool_result)
            return content
    
    def validate_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            messages: 消息列表
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证消息列表
        if not messages:
            errors.append("消息列表不能为空")
        
        # 使用验证工具验证参数
        param_errors = self.validation_utils.validate_request_parameters(parameters)
        errors.extend(param_errors)
        
        # 验证消息内容
        for i, message in enumerate(messages):
            content_errors = self._validate_message_content(message, i)
            errors.extend(content_errors)
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应
        
        Args:
            error_response: 错误响应
            
        Returns:
            str: 用户友好的错误消息
        """
        return self.validation_utils.handle_api_error(error_response)
    
    def _validate_message_content(self, message: "IBaseMessage", index: int) -> List[str]:
        """验证消息内容"""
        errors = []
        
        if isinstance(message.content, list):
            # 确保列表中的元素都是字典格式
            content_list = []
            for item in message.content:
                if isinstance(item, dict):
                    content_list.append(item)
                else:
                    content_list.append({"type": "text", "text": str(item)})
            
            content_errors = self.multimodal_utils.validate_anthropic_content(content_list)
            for error in content_errors:
                errors.append(f"消息 {index}: {error}")
        
        return errors