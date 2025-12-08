"""OpenAI Responses API格式转换工具类

提供OpenAI Responses API的格式转换功能。
"""

from typing import Dict, Any, List, Union, Sequence, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage
    from src.infrastructure.llm.converters.base.base_tools_utils import BaseToolsUtils
    from src.infrastructure.llm.converters.base.base_validation_utils import BaseValidationUtils
    from src.infrastructure.llm.converters.base.base_multimodal_utils import BaseMultimodalUtils
    from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils

from src.infrastructure.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from src.infrastructure.llm.converters.base.base_provider_utils import BaseProviderUtils
from src.infrastructure.llm.converters.openai_response.openai_responses_tools_utils import OpenAIResponsesToolsUtils
from src.infrastructure.llm.converters.openai_response.openai_responses_validation_utils import (
    OpenAIResponsesValidationUtils,
    OpenAIResponsesValidationError,
    OpenAIResponsesFormatError
)
from src.infrastructure.llm.converters.openai_response.openai_responses_multimodal_utils import OpenAIResponsesMultimodalUtils
from src.infrastructure.llm.converters.openai_response.openai_responses_stream_utils import OpenAIResponsesStreamUtils


class OpenAIResponsesFormatUtils(BaseProviderUtils):
     """OpenAI Responses API格式转换工具类"""
     
     def __init__(self, name: str = "openai-responses") -> None:
         """初始化OpenAI Responses API格式工具"""
         super().__init__()
         self.tools_utils: "OpenAIResponsesToolsUtils" = OpenAIResponsesToolsUtils()
         self.validation_utils: "OpenAIResponsesValidationUtils" = OpenAIResponsesValidationUtils()
         self.multimodal_utils: "OpenAIResponsesMultimodalUtils" = OpenAIResponsesMultimodalUtils()
         self.stream_utils: "OpenAIResponsesStreamUtils" = OpenAIResponsesStreamUtils()
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "openai-responses"
    
    def convert_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为OpenAI Responses API请求格式"""
        try:
            # 验证请求参数
            validation_errors = self.validation_utils.validate_request_parameters(parameters)
            if validation_errors:
                raise OpenAIResponsesValidationError(f"请求参数验证失败: {'; '.join(validation_errors)}")
            
            # 将消息转换为Responses API格式
            input_data = self._convert_messages_to_responses_format(messages)
            
            # 构建请求数据
            request_data = {
                "model": parameters.get("model", "gpt-5.1"),
                "input": input_data
            }
            
            # 添加reasoning配置
            if "reasoning" in parameters:
                request_data["reasoning"] = parameters["reasoning"]
            
            # 添加text配置
            if "text" in parameters:
                request_data["text"] = parameters["text"]
            
            # 添加previous_response_id（用于链式思考）
            if "previous_response_id" in parameters:
                request_data["previous_response_id"] = parameters["previous_response_id"]
            
            # 处理工具配置
            if "tools" in parameters:
                tools = parameters["tools"]
                # 验证工具
                tool_errors = self.tools_utils.validate_tools(tools)
                if tool_errors:
                    self.logger.warning(f"工具验证失败: {tool_errors}")
                else:
                    request_data["tools"] = self.tools_utils.convert_tools_to_provider_format(tools)
            
            return request_data
        except OpenAIResponsesValidationError:
            raise
        except Exception as e:
            raise OpenAIResponsesFormatError(f"转换OpenAI Responses API请求失败: {e}")
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从OpenAI Responses API响应转换"""
        try:
            # 验证响应格式
            validation_errors = self.validation_utils.validate_response(response)
            if validation_errors:
                self.logger.warning(f"响应格式验证失败: {'; '.join(validation_errors)}")
            
            # 提取choices
            choices = response.get("choices", [])
            if not choices:
                raise OpenAIResponsesFormatError("响应中没有choices字段")
            
            choice = choices[0]
            message = choice.get("message", {})
            
            # 提取基本信息
            role = message.get("role", "assistant")
            content = message.get("content", "")
            
            # 提取工具调用
            tool_calls = self.tools_utils.extract_tool_calls_from_response(response)
            
            # 构建额外参数
            additional_kwargs = {
                "usage": response.get("usage", {}),
                "model": response.get("model", ""),
                "id": response.get("id", ""),
                "created": response.get("created"),
                "object": response.get("object", "response")
            }
            
            # 添加reasoning信息（Responses API特有）
            if "reasoning" in response:
                additional_kwargs["reasoning"] = response["reasoning"]
            
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
                # 其他角色使用HumanMessage作为回退
                return HumanMessage(
                    content=content or "",
                    additional_kwargs=additional_kwargs
                )
        except Exception as e:
            raise OpenAIResponsesFormatError(f"转换OpenAI Responses API响应失败: {e}")
    
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """从OpenAI Responses API流式响应转换"""
        try:
            # 验证流式事件
            validation_errors = self.stream_utils.validate_stream_events(events)
            if validation_errors:
                self.logger.warning(f"流式事件验证失败: {'; '.join(validation_errors)}")
            
            # 使用流式工具处理事件
            response = self.stream_utils.process_stream_events(events)
            return self.convert_response(response)
        except Exception as e:
            raise OpenAIResponsesFormatError(f"转换OpenAI Responses API流式响应失败: {e}")
    
    def _convert_messages_to_responses_format(self, messages: Sequence["IBaseMessage"]) -> Union[str, List[Dict[str, Any]]]:
        """将消息序列转换为OpenAI Responses API格式"""
        # 检查是否包含多模态内容
        has_multimodal = self._has_multimodal_content(messages)
        
        if has_multimodal:
            # 多模态内容使用数组格式
            return self._convert_messages_to_multimodal_format(messages)
        else:
            # 纯文本内容使用字符串格式
            return self._convert_messages_to_text_format(messages)
    
    def _has_multimodal_content(self, messages: Sequence["IBaseMessage"]) -> bool:
        """检查消息是否包含多模态内容"""
        for message in messages:
            if isinstance(message.content, list):
                for item in message.content:
                    if isinstance(item, dict) and item.get("type") in ["image", "image_url", "input_image"]:
                        return True
        return False
    
    def _convert_messages_to_multimodal_format(self, messages: Sequence["IBaseMessage"]) -> List[Dict[str, Any]]:
        """将消息序列转换为多模态格式"""
        input_items = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                # 系统消息
                content = self.multimodal_utils.process_content_to_provider_format(message.content)
                if content:
                    input_items.append({
                        "role": "system",
                        "content": content
                    })
            elif isinstance(message, HumanMessage):
                # 人类消息
                content = self.multimodal_utils.process_content_to_provider_format(message.content)
                if content:
                    input_items.append({
                        "role": "user",
                        "content": content
                    })
            elif isinstance(message, AIMessage):
                # AI消息
                content = self.multimodal_utils.process_content_to_provider_format(message.content)
                if content:
                    input_items.append({
                        "role": "assistant",
                        "content": content
                    })
            elif isinstance(message, ToolMessage):
                # 工具消息
                tool_content = self._extract_text_content(message)
                if tool_content:
                    input_items.append({
                        "role": "user",
                        "content": [{
                            "type": "input_text",
                            "text": f"Tool Result: {tool_content}"
                        }]
                    })
        
        return input_items
    
    def _convert_messages_to_text_format(self, messages: Sequence["IBaseMessage"]) -> str:
        """将消息序列转换为文本格式"""
        input_parts = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                # 系统消息作为前缀
                system_content = self._extract_text_content(message)
                if system_content:
                    input_parts.append(f"System: {system_content}")
            elif isinstance(message, HumanMessage):
                # 人类消息
                human_content = self._extract_text_content(message)
                if human_content:
                    input_parts.append(f"User: {human_content}")
            elif isinstance(message, AIMessage):
                # AI消息
                ai_content = self._extract_text_content(message)
                if ai_content:
                    input_parts.append(f"Assistant: {ai_content}")
            elif isinstance(message, ToolMessage):
                # 工具消息
                tool_content = self._extract_text_content(message)
                if tool_content:
                    input_parts.append(f"Tool Result: {tool_content}")
        
        return "\n".join(input_parts)
    
    def _extract_text_content(self, message: "IBaseMessage") -> str:
        """提取消息的文本内容"""
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, list):
            text_parts = []
            for item in message.content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                else:
                    text_parts.append(str(item))
            return " ".join(text_parts)
        else:
            return str(message.content)
    
    def _merge_responses_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并Responses API流式事件"""
        merged_response = {}
        
        # 从第一个事件获取基本信息
        if events and isinstance(events[0], dict):
            first_event = events[0]
            
            # 复制基本字段
            for field in ["id", "object", "created", "model"]:
                if field in first_event:
                    merged_response[field] = first_event[field]
        
        # 合并choices
        merged_choices: List[Dict[str, Any]] = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            choices = event.get("choices", [])
            if not choices:
                continue
            
            choice = choices[0]
            choice_index = choice.get("index", 0)
            
            # 确保有足够的choice槽位
            while len(merged_choices) <= choice_index:
                merged_choices.append({
                    "index": choice_index,
                    "message": {}
                })
            
            # 合并delta到message
            delta = choice.get("delta", {})
            if delta:
                for key, value in delta.items():
                    if key == "content":
                        # 内容需要累加
                        existing = merged_choices[choice_index]["message"].get("content", "")
                        merged_choices[choice_index]["message"]["content"] = existing + (value or "")
                    else:
                        # 其他字段直接设置
                        merged_choices[choice_index]["message"][key] = value
        
        merged_response["choices"] = merged_choices
        
        # 提取使用信息
        for event in events:
            if isinstance(event, dict) and "usage" in event:
                merged_response["usage"] = event["usage"]
                break
        
        # 提取reasoning信息
        for event in events:
            if isinstance(event, dict) and "reasoning" in event:
                merged_response["reasoning"] = event["reasoning"]
                break
        
        return merged_response
    
    def validate_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
        errors = []
        
        # 验证消息列表
        if not messages:
            errors.append("消息列表不能为空")
        
        # 使用验证工具验证参数
        param_errors = self.validation_utils.validate_request_parameters(parameters)
        errors.extend(param_errors)
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应"""
        return self.validation_utils.handle_api_error(error_response)
    
    def create_responses_request(
        self,
        input_text: str,
        model: str = "gpt-5.1",
        reasoning_effort: Optional[str] = None,
        text_verbosity: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        previous_response_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建Responses API请求的便捷方法"""
        request_data = {
            "model": model,
            "input": input_text
        }
        
        # 添加reasoning配置
        if reasoning_effort:
            request_data["reasoning"] = {"effort": reasoning_effort}  # type: ignore
        
        # 添加text配置
        if text_verbosity:
            request_data["text"] = {"verbosity": text_verbosity}  # type: ignore
        
        # 添加工具
        if tools:
            request_data["tools"] = tools  # type: ignore
        
        # 添加previous_response_id
        if previous_response_id:
            request_data["previous_response_id"] = previous_response_id
        
        # 添加其他参数
        request_data.update(kwargs)
        
        return request_data
    
    def extract_reasoning_from_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从响应中提取reasoning信息"""
        return response.get("reasoning")
    
    def extract_chain_of_thought_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """从响应中提取链式思考内容"""
        reasoning = response.get("reasoning", {})
        result = reasoning.get("chain_of_thought")
        return result if isinstance(result, str) else None
    
    def extract_reasoning_effort_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """从响应中提取推理努力程度"""
        reasoning = response.get("reasoning", {})
        result = reasoning.get("effort_used")
        return result if isinstance(result, str) else None
    
    def extract_reasoning_steps_from_response(self, response: Dict[str, Any]) -> Optional[List[str]]:
        """从响应中提取推理步骤"""
        reasoning = response.get("reasoning", {})
        result = reasoning.get("steps")
        return result if isinstance(result, list) else None
    
    def is_responses_response(self, response: Dict[str, Any]) -> bool:
        """检查是否为Responses API响应"""
        return response.get("object") == "response"
    
    def has_reasoning(self, response: Dict[str, Any]) -> bool:
        """检查响应是否包含reasoning信息"""
        return "reasoning" in response and isinstance(response["reasoning"], dict)
    
    def format_reasoning_for_display(self, response: Dict[str, Any]) -> str:
        """格式化reasoning信息用于显示"""
        reasoning = response.get("reasoning", {})
        if not reasoning:
            return ""
        
        parts = []
        
        # 添加努力程度
        effort_used = reasoning.get("effort_used")
        if effort_used:
            parts.append(f"推理努力程度: {effort_used}")
        
        # 添加链式思考
        chain_of_thought = reasoning.get("chain_of_thought")
        if chain_of_thought:
            parts.append(f"链式思考: {chain_of_thought}")
        
        # 添加推理步骤
        steps = reasoning.get("steps", [])
        if steps:
            steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
            parts.append(f"推理步骤:\n{steps_text}")
        
        return "\n".join(parts)
    
    def convert_from_chat_completions_format(self, chat_request: Dict[str, Any]) -> Dict[str, Any]:
        """从Chat Completions格式转换为Responses格式"""
        # 提取messages并转换为input
        messages = chat_request.get("messages", [])
        input_text = self._convert_chat_messages_to_input(messages)
        
        # 构建Responses格式请求
        responses_request = {
            "model": chat_request.get("model", "gpt-5.1"),
            "input": input_text
        }
        
        # 转换reasoning_effort
        if "reasoning_effort" in chat_request:
            responses_request["reasoning"] = {
                "effort": chat_request["reasoning_effort"]
            }
        
        # 转换tools
        if "tools" in chat_request:
            responses_request["tools"] = self.tools_utils.convert_from_openai_format(chat_request["tools"])
        
        # 转换tool_choice
        if "tool_choice" in chat_request:
            responses_request["tool_choice"] = chat_request["tool_choice"]
        
        return responses_request
    
    def _convert_chat_messages_to_input(self, messages: List[Dict[str, Any]]) -> Union[str, List[Dict[str, Any]]]:
        """将Chat Completions格式的messages转换为Responses API input格式"""
        # 检查是否包含多模态内容
        has_multimodal = any(
            isinstance(msg.get("content"), list) for msg in messages
        )
        
        if has_multimodal:
            # 多模态内容转换为Responses API格式
            return self._convert_chat_messages_to_multimodal_format(messages)
        else:
            # 纯文本内容转换为字符串格式
            return self._convert_chat_messages_to_text_format(messages)
    
    def _convert_chat_messages_to_multimodal_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将Chat Completions格式的messages转换为多模态格式"""
        input_items = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if isinstance(content, list):
                # 多模态内容，需要转换格式
                converted_content = self.multimodal_utils.convert_from_openai_format(content)
                input_items.append({
                    "role": role,
                    "content": converted_content
                })
            else:
                # 文本内容
                input_items.append({
                    "role": role,
                    "content": [{
                        "type": "input_text",
                        "text": content
                    }]
                })
        
        return input_items
    
    def _convert_chat_messages_to_text_format(self, messages: List[Dict[str, Any]]) -> str:
        """将Chat Completions格式的messages转换为文本格式"""
        input_parts = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                input_parts.append(f"System: {content}")
            elif role == "user":
                input_parts.append(f"User: {content}")
            elif role == "assistant":
                input_parts.append(f"Assistant: {content}")
            elif role == "tool":
                tool_call_id = message.get("tool_call_id", "")
                input_parts.append(f"Tool Result ({tool_call_id}): {content}")
        
        return "\n".join(input_parts)