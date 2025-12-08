"""Gemini格式转换工具类

提供Gemini API的格式转换功能。
"""

from typing import Dict, Any, List, Union, Sequence, Optional, TYPE_CHECKING, cast

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
from src.infrastructure.llm.converters.gemini.gemini_multimodal_utils import GeminiMultimodalUtils
from src.infrastructure.llm.converters.gemini.gemini_tools_utils import GeminiToolsUtils
from src.infrastructure.llm.converters.gemini.gemini_validation_utils import GeminiValidationUtils, GeminiValidationError, GeminiFormatError
from src.infrastructure.llm.converters.gemini.gemini_stream_utils import GeminiStreamUtils


class GeminiFormatUtils(BaseProviderUtils):
    """Gemini格式转换工具类"""
    
    multimodal_utils: GeminiMultimodalUtils
    tools_utils: GeminiToolsUtils
    validation_utils: GeminiValidationUtils
    stream_utils: GeminiStreamUtils
    
    def __init__(self, name: str = "gemini") -> None:
         """初始化Gemini格式工具"""
         super().__init__()
         self.multimodal_utils = GeminiMultimodalUtils()
         self.tools_utils = GeminiToolsUtils()
         self.validation_utils = GeminiValidationUtils()
         self.stream_utils = GeminiStreamUtils()
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "gemini"
    
    def convert_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为Gemini API请求格式"""
        try:
            # 验证请求参数
            validation_errors = self.validation_utils.validate_request_parameters(parameters)
            if validation_errors:
                raise GeminiValidationError(f"请求参数验证失败: {'; '.join(validation_errors)}")
            
            contents = []
            system_instruction = None
            
            # 处理消息
            for message in messages:
                if isinstance(message, SystemMessage):
                    system_instruction = self._extract_system_message_content(message)
                    continue
                
                role = "user" if isinstance(message, (HumanMessage, ToolMessage)) else "model"
                
                # 使用多模态工具处理内容
                parts = self.multimodal_utils.process_content_to_provider_format(message.content)
                
                # 处理工具消息的特殊情况
                if isinstance(message, ToolMessage):
                    parts = self._process_tool_message_content(message, parts)
                
                content_dict = {
                    "role": role,
                    "parts": parts
                }
                
                contents.append(content_dict)
            
            # 构建请求数据
            request_data = {
                "contents": contents
            }
            
            # 添加系统消息
            if system_instruction:
                request_data["systemInstruction"] = {  # type: ignore
                    "parts": [{"text": system_instruction}]
                }
            
            # 添加生成配置
            generation_config = self._build_generation_config(parameters)
            if generation_config:
                request_data["generationConfig"] = generation_config  # type: ignore
            
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
                    tool_config = self.tools_utils.process_tool_config(parameters)
                    if tool_config:
                        request_data["tool_config"] = tool_config  # type: ignore
            
            # 处理额外配置（思考配置、缓存等）
            extra_config = self._process_extra_config(parameters)
            if extra_config:
                request_data.update(extra_config)
            
            return request_data
        except GeminiValidationError:
            raise
        except Exception as e:
            raise GeminiFormatError(f"转换Gemini请求失败: {e}")
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从Gemini API响应转换"""
        try:
            # 验证响应格式
            validation_errors = self.validation_utils.validate_response(response)
            if validation_errors:
                self.logger.warning(f"响应格式验证失败: {'; '.join(validation_errors)}")
            
            if "candidates" not in response or not response["candidates"]:
                raise GeminiFormatError("响应中没有候选内容")
            
            candidate = response["candidates"][0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            # 提取文本内容和工具调用
            text_parts = []
            tool_calls = []
            thoughts = []
            
            for part in parts:
                if isinstance(part, dict):
                    if "text" in part:
                        text_parts.append(part["text"])
                    elif "functionCall" in part:
                        tool_call = self.tools_utils._extract_single_tool_call(part)
                        if tool_call:
                            tool_calls.append(tool_call)
                    elif "thought" in part:
                        thoughts.append(part["thought"])
            
            content_text = " ".join(text_parts)
            
            # 构建额外参数
            additional_kwargs = {
                "finishReason": candidate.get("finishReason"),
                "index": candidate.get("index"),
                "safetyRatings": candidate.get("safetyRatings", []),
                "usageMetadata": response.get("usageMetadata", {})
            }
            
            # 添加工具调用信息
            if tool_calls:
                additional_kwargs["tool_calls"] = tool_calls
            
            # 添加思考过程
            if thoughts:
                additional_kwargs["thoughts"] = thoughts
            
            return AIMessage(
                content=content_text,
                tool_calls=tool_calls if tool_calls else None,
                additional_kwargs=additional_kwargs
            )
        except Exception as e:
            raise GeminiFormatError(f"转换Gemini响应失败: {e}")
    
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """从Gemini流式响应转换"""
        try:
            # 验证流式事件
            validation_errors = self.stream_utils.validate_stream_events(events)
            if validation_errors:
                self.logger.warning(f"流式事件验证失败: {'; '.join(validation_errors)}")
            
            # 使用流式工具处理事件
            response = self.stream_utils.process_stream_events(events)
            return self.convert_response(response)
        except Exception as e:
            raise GeminiFormatError(f"转换Gemini流式响应失败: {e}")
    
    def _extract_system_message_content(self, message: SystemMessage) -> str:
        """提取系统消息内容"""
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, list):
            # 转换为正确的格式
            gemini_content = []
            for item in message.content:
                if isinstance(item, dict):
                    gemini_content.append(item)
                else:
                    gemini_content.append({"text": str(item)})
            return self.multimodal_utils.extract_text_from_provider_content(gemini_content)
        else:
            return str(message.content)
    
    def _process_tool_message_content(
        self,
        message: ToolMessage,
        parts: List[Dict[str, Any]]
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
                elif isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                else:
                    text_parts.append(str(item))
            tool_result_content = " ".join(text_parts)
        elif not isinstance(tool_result_content, (str, dict)):
            tool_result_content = str(tool_result_content)
        
        # 创建工具响应内容
        tool_response = self.tools_utils.create_tool_response_content(
            message.tool_call_id,
            tool_result_content
        )
        
        # 如果有其他内容，合并
        if len(parts) == 1 and "text" in parts[0]:
            # 只有文本内容，替换为工具响应
            return [tool_response]
        else:
            # 有多模态内容，添加工具响应
            parts.append(tool_response)
            return parts
    
    def _build_generation_config(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """构建生成配置"""
        config = {}
        
        # 基础参数映射
        param_mapping = {
            "temperature": "temperature",
            "max_tokens": "maxOutputTokens",
            "top_p": "topP",
            "top_k": "topK",
            "candidate_count": "candidateCount",
            "stop_sequences": "stopSequences",
            "response_mime_type": "responseMimeType",
            "presence_penalty": "presencePenalty",
            "frequency_penalty": "frequencyPenalty",
            "seed": "seed"
        }
        
        for param_name, gemini_name in param_mapping.items():
            if param_name in parameters:
                config[gemini_name] = parameters[param_name]
        
        return config
    
    def _process_extra_config(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理额外配置"""
        extra_config: Dict[str, Any] = {}
        
        # 处理OpenAI兼容的reasoning_effort
        if "reasoning_effort" in parameters:
            reasoning_effort = parameters["reasoning_effort"]
            thinking_budget = self._map_reasoning_effort_to_thinking_budget(reasoning_effort)
            
            if "extra_body" not in extra_config:
                extra_config["extra_body"] = {}
            if "google" not in extra_config["extra_body"]:
                extra_config["extra_body"]["google"] = {}
            
            extra_config["extra_body"]["google"]["thinking_config"] = {
                "thinking_budget": thinking_budget,
                "include_thoughts": True
            }
        
        # 处理现有的extra_body配置
        if "extra_body" in parameters:
            if "extra_body" not in extra_config:
                extra_config["extra_body"] = {}
            extra_config["extra_body"].update(parameters["extra_body"])
        
        return extra_config
    
    def _map_reasoning_effort_to_thinking_budget(self, reasoning_effort: str) -> str:
        """将OpenAI的reasoning_effort映射到Gemini的thinking_budget"""
        mapping = {
            "minimal": "low",
            "low": "low",
            "medium": "high",
            "high": "high"
        }
        return mapping.get(reasoning_effort, "medium")
    
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
            # 转换为正确的格式
            gemini_content = []
            for item in message.content:
                if isinstance(item, dict):
                    gemini_content.append(item)
                else:
                    gemini_content.append({"text": str(item)})
            # 确保列表中的元素都是字典格式
            content_errors = self.multimodal_utils.validate_provider_content(gemini_content)
            for error in content_errors:
                errors.append(f"消息 {index}: {error}")
        
        return errors
    
    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为Gemini格式（兼容性方法）"""
        return self.tools_utils.convert_tools_to_provider_format(tools)