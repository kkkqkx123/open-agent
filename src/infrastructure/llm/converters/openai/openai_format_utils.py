"""OpenAI格式转换工具类

提供OpenAI API的格式转换功能。
"""

from typing import Dict, Any, List, Union, Sequence, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage
    from src.infrastructure.llm.converters.base.base_multimodal_utils import BaseMultimodalUtils
    from src.infrastructure.llm.converters.base.base_tools_utils import BaseToolsUtils
    from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils
    from src.infrastructure.llm.converters.base.base_validation_utils import BaseValidationUtils

from src.infrastructure.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from src.infrastructure.llm.converters.base.base_provider_utils import BaseProviderUtils
from src.infrastructure.llm.converters.openai.openai_multimodal_utils import OpenAIMultimodalUtils
from src.infrastructure.llm.converters.openai.openai_tools_utils import OpenAIToolsUtils
from src.infrastructure.llm.converters.openai.openai_stream_utils import OpenAIStreamUtils
from src.infrastructure.llm.converters.openai.openai_validation_utils import (
    OpenAIValidationUtils, 
    OpenAIValidationError, 
    OpenAIFormatError
)


class OpenAIFormatUtils(BaseProviderUtils):
    """OpenAI格式转换工具类"""
    
    def __init__(self) -> None:
        """初始化OpenAI格式工具"""
        super().__init__()
        self.multimodal_utils: "OpenAIMultimodalUtils" = OpenAIMultimodalUtils()
        self.tools_utils: "OpenAIToolsUtils" = OpenAIToolsUtils()
        self.stream_utils: "OpenAIStreamUtils" = OpenAIStreamUtils()
        self.validation_utils: "OpenAIValidationUtils" = OpenAIValidationUtils()
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "openai"
    
    def convert_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为OpenAI API请求格式"""
        try:
            # 验证请求参数
            validation_errors = self.validation_utils.validate_request_parameters(parameters)
            if validation_errors:
                raise OpenAIValidationError(f"请求参数验证失败: {'; '.join(validation_errors)}")
            
            # 转换消息格式
            openai_messages = self._convert_messages_to_openai_format(messages)
            
            # 构建请求数据
            request_data = {
                "model": parameters.get("model", "gpt-3.5-turbo"),
                "messages": openai_messages
            }
            
            # 添加可选参数
            optional_params = [
                "temperature", "top_p", "n", "stream", "stop", 
                "max_tokens", "presence_penalty", "frequency_penalty",
                "logit_bias", "user", "service_tier", "seed"
            ]
            
            for param in optional_params:
                if param in parameters:
                    request_data[param] = parameters[param]
            
            # 处理response_format
            if "response_format" in parameters:
                request_data["response_format"] = parameters["response_format"]
            
            # 处理reasoning_effort (GPT-5特有)
            if "reasoning_effort" in parameters:
                request_data["reasoning_effort"] = parameters["reasoning_effort"]
            
            # 处理stream_options
            if "stream_options" in parameters:
                request_data["stream_options"] = parameters["stream_options"]
            
            # 处理工具配置
            if "tools" in parameters:
                tools = parameters["tools"]
                # 验证工具
                tool_errors = self.tools_utils.validate_tools(tools)
                if tool_errors:
                    self.logger.warning(f"工具验证失败: {tool_errors}")
                else:
                    request_data["tools"] = self.tools_utils.convert_tools_to_provider_format(tools)
                    
                    # 处理工具选择策略
                    if "tool_choice" in parameters:
                        request_data["tool_choice"] = self.tools_utils.process_tool_choice(
                            parameters["tool_choice"]
                        )
            
            return request_data
        except OpenAIValidationError:
            raise
        except Exception as e:
            raise OpenAIFormatError(f"转换OpenAI请求失败: {e}")
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从OpenAI API响应转换"""
        try:
            # 验证响应格式
            validation_errors = self.validation_utils.validate_response(response)
            if validation_errors:
                self.logger.warning(f"响应格式验证失败: {'; '.join(validation_errors)}")
            
            # 提取choices
            choices = response.get("choices", [])
            if not choices:
                raise OpenAIFormatError("响应中没有choices字段")
            
            choice = choices[0]
            message = choice.get("message", {})
            
            # 提取基本信息
            role = message.get("role", "assistant")
            content = message.get("content", "")
            
            # 提取工具调用
            tool_calls = self.tools_utils.extract_tool_calls_from_response(response)
            
            # 构建额外参数
            additional_kwargs = {
                "finish_reason": choice.get("finish_reason"),
                "usage": response.get("usage", {}),
                "model": response.get("model", ""),
                "id": response.get("id", ""),
                "created": response.get("created"),
                "system_fingerprint": response.get("system_fingerprint"),
                "service_tier": response.get("service_tier")
            }
            
            # 添加工具调用信息
            if tool_calls:
                additional_kwargs["tool_calls"] = tool_calls
            
            # 根据角色创建消息
            if role == "assistant":
                return AIMessage(
                    content=content or "",
                    tool_calls=tool_calls if tool_calls else None,
                    additional_kwargs=additional_kwargs
                )
            else:
                # 其他角色（如system）使用HumanMessage作为回退
                return HumanMessage(
                    content=content or "",
                    additional_kwargs=additional_kwargs
                )
        except Exception as e:
            raise OpenAIFormatError(f"转换OpenAI响应失败: {e}")
    
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """从OpenAI流式响应转换"""
        try:
            # 验证流式事件
            validation_errors = self.stream_utils.validate_stream_events(events)
            if validation_errors:
                self.logger.warning(f"流式事件验证失败: {'; '.join(validation_errors)}")
            
            # 使用流式工具处理事件
            response = self.stream_utils.process_stream_events(events)
            return self.convert_response(response)
        except Exception as e:
            raise OpenAIFormatError(f"转换OpenAI流式响应失败: {e}")
    
    def _convert_messages_to_openai_format(self, messages: Sequence["IBaseMessage"]) -> List[Dict[str, Any]]:
        """将消息转换为OpenAI格式"""
        openai_messages = []
        
        for message in messages:
            openai_message = self._convert_single_message_to_openai_format(message)
            if openai_message:
                openai_messages.append(openai_message)
        
        return openai_messages
    
    def _convert_single_message_to_openai_format(self, message: "IBaseMessage") -> Optional[Dict[str, Any]]:
        """转换单个消息为OpenAI格式"""
        if isinstance(message, SystemMessage):
            return self._convert_system_message(message)
        elif isinstance(message, HumanMessage):
            return self._convert_human_message(message)
        elif isinstance(message, AIMessage):
            return self._convert_ai_message(message)
        elif isinstance(message, ToolMessage):
            return self._convert_tool_message(message)
        else:
            self.logger.warning(f"不支持的消息类型: {type(message)}")
            return None
    
    def _convert_system_message(self, message: SystemMessage) -> Dict[str, Any]:
        """转换系统消息"""
        # 处理多模态内容
        content = self.multimodal_utils.process_content_to_provider_format(message.content)
        
        # 如果是纯文本，直接使用字符串
        if len(content) == 1 and content[0].get("type") == "text":
            text_content = content[0].get("text", "")
            openai_message = {
                "role": "system",
                "content": text_content
            }
        else:
            # 多模态内容使用列表格式
            openai_message = {
                "role": "system",
                "content": content
            }
        
        # 添加名称（如果有）
        if message.name:
            openai_message["name"] = message.name
        
        return openai_message
    
    def _convert_human_message(self, message: HumanMessage) -> Dict[str, Any]:
        """转换人类消息"""
        # 处理多模态内容
        content = self.multimodal_utils.process_content_to_provider_format(message.content)
        
        # 如果是纯文本，直接使用字符串
        if len(content) == 1 and content[0].get("type") == "text":
            text_content = content[0].get("text", "")
            openai_message = {
                "role": "user",
                "content": text_content
            }
        else:
            # 多模态内容使用列表格式
            openai_message = {
                "role": "user",
                "content": content
            }
        
        # 添加名称（如果有）
        if message.name:
            openai_message["name"] = message.name
        
        return openai_message
    
    def _convert_ai_message(self, message: AIMessage) -> Dict[str, Any]:
        """转换AI消息"""
        # 处理多模态内容
        content = self.multimodal_utils.process_content_to_provider_format(message.content)
        
        # 如果是纯文本，直接使用字符串
        if len(content) == 1 and content[0].get("type") == "text":
            text_content = content[0].get("text", "")
            openai_message = {
                "role": "assistant",
                "content": text_content
            }
        else:
            # 多模态内容使用列表格式
            openai_message = {
                "role": "assistant",
                "content": content
            }
        
        # 添加工具调用
        tool_calls = message.get_tool_calls()
        if tool_calls:
            openai_message["tool_calls"] = tool_calls
        
        # 添加名称（如果有）
        if message.name:
            openai_message["name"] = message.name
        
        return openai_message
    
    def _convert_tool_message(self, message: ToolMessage) -> Dict[str, Any]:
        """转换工具消息"""
        # 确保工具结果是字符串格式
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
        elif not isinstance(tool_result_content, str):
            tool_result_content = str(tool_result_content)
        
        openai_message = {
            "role": "tool",
            "tool_call_id": message.tool_call_id,
            "content": tool_result_content
        }
        
        # 添加名称（如果有）
        if message.name:
            openai_message["name"] = message.name
        
        return openai_message
    
    def validate_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
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
        """处理API错误响应"""
        return self.validation_utils.handle_api_error(error_response)
    
    def _validate_message_content(self, message: "IBaseMessage", index: int) -> List[str]:
        """验证消息内容"""
        errors = []
        
        if isinstance(message.content, list):
            # 将内容转换为提供商格式后验证
            processed_content = self.multimodal_utils.process_content_to_provider_format(message.content)
            content_errors = self.multimodal_utils.validate_provider_content(processed_content)
            for error in content_errors:
                errors.append(f"消息 {index}: {error}")
        
        return errors
    
    def create_chat_completion_request(
        self,
        messages: Sequence["IBaseMessage"],
        model: str = "gpt-3.5-turbo",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建聊天完成请求的便捷方法"""
        parameters = {"model": model, **kwargs}
        return self.convert_request(messages, parameters)
    
    def extract_usage_from_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从响应中提取使用信息"""
        return response.get("usage")
    
    def extract_finish_reason_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """从响应中提取完成原因"""
        choices = response.get("choices", [])
        if choices:
            reason = choices[0].get("finish_reason")
            return reason if isinstance(reason, str) else None
        return None
    
    def extract_model_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """从响应中提取模型信息"""
        return response.get("model")
    
    def is_streaming_response(self, response: Dict[str, Any]) -> bool:
        """检查是否为流式响应"""
        return response.get("object") == "chat.completion.chunk"
    
    def should_continue_stream(self, event: Dict[str, Any]) -> bool:
        """检查是否应该继续流式处理"""
        return not self.stream_utils._is_complete_event(event)
    
    def format_error_for_user(self, error_response: Dict[str, Any]) -> str:
        """格式化错误信息给用户"""
        return self.handle_api_error(error_response)