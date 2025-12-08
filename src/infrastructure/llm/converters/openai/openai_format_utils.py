"""OpenAI格式转换工具类

提供OpenAI API的格式转换功能，使用新的核心架构。
"""

from typing import Dict, Any, List, Union, Sequence, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

from src.infrastructure.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from src.infrastructure.llm.converters.core.provider_base import BaseProvider
from src.infrastructure.llm.converters.core.adapters import (
    BaseMultimodalAdapter,
    BaseStreamAdapter,
    BaseToolsAdapter,
    BaseValidationAdapter
)
from src.infrastructure.llm.converters.core.conversion_context import ConversionContext
from src.interfaces.llm.converters import IConversionContext


class OpenAIMultimodalAdapter(BaseMultimodalAdapter):
    """OpenAI多模态适配器"""
    
    def process_content_to_provider_format(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """将内容转换为OpenAI格式"""
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        
        processed_content = []
        for item in content:
            if isinstance(item, str):
                processed_content.append({"type": "text", "text": item})
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    processed_content.append(item)
                elif item.get("type") == "image":
                    processed_content.append(self._process_image_content(item))
                else:
                    # 转换为文本
                    processed_content.append({"type": "text", "text": str(item)})
        
        return processed_content
    
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从OpenAI格式内容中提取文本"""
        text_parts = []
        for item in content:
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif item.get("type") == "image":
                text_parts.append("[图像内容]")
        return " ".join(text_parts)
    
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证OpenAI格式内容"""
        return self._validate_content_structure(content)


class OpenAIStreamAdapter(BaseStreamAdapter):
    """OpenAI流式适配器"""
    
    def parse_stream_event(self, event_line: str, context: Optional[IConversionContext] = None) -> Optional[Dict[str, Any]]:
        """解析OpenAI流式事件行"""
        return self._parse_sse_event(event_line)
    
    def process_stream_events(self, events: List[Dict[str, Any]], context: Optional[IConversionContext] = None) -> Dict[str, Any]:
        """处理OpenAI流式事件列表"""
        merged_response = {}
        choices = []
        
        for event in events:
            if event.get("type") == "done":
                continue
                
            # 处理choices
            if "choices" in event:
                for choice in event["choices"]:
                    if "delta" in choice:
                        # 合并delta内容
                        existing_choice = self._find_or_create_choice(choices, choice)
                        self._merge_delta_to_choice(existing_choice, choice["delta"])
            
            # 合并其他字段
            for key, value in event.items():
                if key not in ["choices", "type"]:
                    merged_response[key] = value
        
        if choices:
            merged_response["choices"] = choices
        
        return merged_response
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]], context: Optional[IConversionContext] = None) -> str:
        """从OpenAI流式事件中提取文本"""
        text_parts = []
        
        for event in events:
            if "choices" in event:
                for choice in event["choices"]:
                    if "delta" in choice and "content" in choice["delta"]:
                        text_parts.append(choice["delta"]["content"])
        
        return "".join(text_parts)
    
    def _find_or_create_choice(self, choices: List[Dict[str, Any]], choice: Dict[str, Any]) -> Dict[str, Any]:
        """查找或创建choice"""
        index = choice.get("index", 0)
        while len(choices) <= index:
            choices.append({
                "index": len(choices),
                "message": {"content": "", "role": "assistant"},
                "finish_reason": None
            })
        return choices[index]
    
    def _merge_delta_to_choice(self, choice: Dict[str, Any], delta: Dict[str, Any]) -> None:
        """合并delta到choice"""
        if "content" in delta:
            choice["message"]["content"] += delta["content"]
        
        if "role" in delta:
            choice["message"]["role"] = delta["role"]
        
        if "tool_calls" in delta:
            if "tool_calls" not in choice["message"]:
                choice["message"]["tool_calls"] = []
            # 处理工具调用增量
            self._merge_tool_calls_delta(choice["message"]["tool_calls"], delta["tool_calls"])
        
        if "finish_reason" in delta:
            choice["finish_reason"] = delta["finish_reason"]
    
    def _merge_tool_calls_delta(self, existing_calls: List[Dict[str, Any]], delta_calls: List[Dict[str, Any]]) -> None:
        """合并工具调用增量"""
        for delta_call in delta_calls:
            index = delta_call.get("index", 0)
            while len(existing_calls) <= index:
                existing_calls.append({
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""}
                })
            
            existing_call = existing_calls[index]
            
            if "id" in delta_call:
                existing_call["id"] += delta_call["id"]
            
            if "function" in delta_call:
                if "name" in delta_call["function"]:
                    existing_call["function"]["name"] += delta_call["function"]["name"]
                if "arguments" in delta_call["function"]:
                    existing_call["function"]["arguments"] += delta_call["function"]["arguments"]


class OpenAIToolsAdapter(BaseToolsAdapter):
    """OpenAI工具适配器"""
    
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]], context: Optional[IConversionContext] = None) -> List[Dict[str, Any]]:
        """转换工具格式为OpenAI格式"""
        openai_tools = []
        
        for tool in tools:
            function_dict = {
                "name": tool["name"],
                "description": tool.get("description", ""),
            }
            
            if "parameters" in tool:
                function_dict["parameters"] = tool["parameters"]
            
            openai_tool = {
                "type": "function",
                "function": function_dict
            }
            
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    def process_tool_choice(self, tool_choice: Any, context: Optional[IConversionContext] = None) -> Any:
        """处理工具选择策略"""
        if isinstance(tool_choice, str):
            if tool_choice == "none":
                return None
            elif tool_choice == "auto":
                return "auto"
            elif tool_choice == "required":
                return "required"
            else:
                return "auto"
        elif isinstance(tool_choice, dict):
            return self._process_tool_choice_dict(tool_choice)
        else:
            return "auto"
    
    def extract_tool_calls_from_response(self, response: Dict[str, Any], context: Optional[IConversionContext] = None) -> List[Dict[str, Any]]:
        """从OpenAI响应中提取工具调用"""
        tool_calls = []
        
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls", [])
        
        return tool_calls


class OpenAIValidationAdapter(BaseValidationAdapter):
    """OpenAI验证适配器"""
    
    def validate_request_parameters(self, parameters: Dict[str, Any], context: Optional[IConversionContext] = None) -> List[str]:
        """验证OpenAI请求参数"""
        errors = super().validate_request_parameters(parameters)
        
        # OpenAI特定验证
        if "model" in parameters:
            model = parameters["model"]
            if not isinstance(model, str) or not model.strip():
                errors.append("model参数必须是非空字符串")
        
        if "temperature" in parameters:
            temp = parameters["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append("temperature参数必须是0-2之间的数字")
        
        if "max_tokens" in parameters:
            max_tokens = parameters["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens < 1:
                errors.append("max_tokens参数必须是大于0的整数")
        
        return errors
    
    def validate_response(self, response: Dict[str, Any], context: Optional[IConversionContext] = None) -> List[str]:
        """验证OpenAI响应格式"""
        errors = super().validate_response(response)
        
        # OpenAI特定验证
        if "choices" not in response:
            errors.append("响应缺少choices字段")
        elif not isinstance(response["choices"], list):
            errors.append("choices字段必须是列表")
        elif not response["choices"]:
            errors.append("choices列表不能为空")
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any], context: Optional[IConversionContext] = None) -> str:
        """处理OpenAI API错误响应"""
        error = error_response.get("error", {})
        error_type = error.get("type", "unknown")
        error_message = error.get("message", "未知错误")
        error_code = error.get("code", "unknown")
        
        # OpenAI特定错误映射
        error_mapping = {
            "invalid_request_error": "请求参数无效",
            "invalid_api_key": "API密钥无效",
            "insufficient_quota": "配额不足",
            "model_not_found": "模型不存在",
            "rate_limit_exceeded": "请求频率过高",
            "api_error": "API内部错误",
            "content_policy_violation": "内容违反政策"
        }
        
        friendly_message = error_mapping.get(error_type, f"未知错误类型: {error_type}")
        
        return f"{friendly_message} ({error_code}): {error_message}"


class OpenAIFormatUtils(BaseProvider):
    """OpenAI格式转换工具类"""
    
    def __init__(self) -> None:
        """初始化OpenAI格式工具"""
        super().__init__("openai")
    
    def _create_multimodal_adapter(self) -> BaseMultimodalAdapter:
        """创建OpenAI多模态适配器"""
        return OpenAIMultimodalAdapter()
    
    def _create_stream_adapter(self) -> BaseStreamAdapter:
        """创建OpenAI流式适配器"""
        return OpenAIStreamAdapter()
    
    def _create_tools_adapter(self) -> BaseToolsAdapter:
        """创建OpenAI工具适配器"""
        return OpenAIToolsAdapter()
    
    def _create_validation_adapter(self) -> BaseValidationAdapter:
        """创建OpenAI验证适配器"""
        return OpenAIValidationAdapter()
    
    def _do_convert_request(self, messages: List[Any], parameters: Dict[str, Any], context: IConversionContext) -> Dict[str, Any]:
        """执行OpenAI请求转换"""
        # 转换消息格式
        openai_messages = []
        for message in messages:
            openai_message = self._convert_message_to_openai_format(message, context)
            if openai_message:
                openai_messages.append(openai_message)
        
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
        
        # 处理特殊参数
        self._handle_special_parameters(request_data, parameters, context)
        
        # 处理工具配置
        self._handle_tools_configuration(request_data, parameters, context)
        
        return request_data
    
    def _do_convert_response(self, response: Dict[str, Any], context: IConversionContext) -> Any:
        """执行OpenAI响应转换"""
        # 提取choices
        choices = response.get("choices", [])
        if not choices:
            raise ValueError("响应中没有choices字段")
        
        choice = choices[0]
        message = choice.get("message", {})
        
        # 提取基本信息
        role = message.get("role", "assistant")
        content = message.get("content", "")
        
        # 提取工具调用
        tool_calls = self.extract_tool_calls(response)
        
        # 构建额外参数
        additional_kwargs = self._build_response_metadata(response, choice)
        
        # 添加工具调用信息
        if tool_calls:
            additional_kwargs["tool_calls"] = tool_calls
        
        # 根据角色创建消息
        return self._create_message_from_role(role, content, tool_calls, additional_kwargs)
    
    def _do_convert_stream_response(self, events: List[Dict[str, Any]], context: IConversionContext) -> Any:
        """执行OpenAI流式响应转换"""
        # 使用流式适配器处理事件
        response = self.stream_adapter.process_stream_events(events, context)
        return self._do_convert_response(response, context)
    
    def _convert_message_to_openai_format(self, message: Any, context: IConversionContext) -> Optional[Dict[str, Any]]:
        """转换消息为OpenAI格式"""
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
    
    def _convert_system_message(self, message: SystemMessage, context: IConversionContext) -> Dict[str, Any]:
        """转换系统消息"""
        return self._build_base_message(message, "system", context)
    
    def _convert_human_message(self, message: HumanMessage, context: IConversionContext) -> Dict[str, Any]:
        """转换人类消息"""
        return self._build_base_message(message, "user", context)
    
    def _convert_ai_message(self, message: AIMessage, context: IConversionContext) -> Dict[str, Any]:
        """转换AI消息"""
        openai_message = self._build_base_message(message, "assistant", context)
        
        # 添加工具调用
        tool_calls = getattr(message, 'tool_calls', None)
        if tool_calls:
            openai_message["tool_calls"] = tool_calls
        
        return openai_message
    
    def _convert_tool_message(self, message: ToolMessage, context: IConversionContext) -> Dict[str, Any]:
        """转换工具消息"""
        # 确保工具结果是字符串格式
        tool_result_content = message.content
        if isinstance(tool_result_content, list):
            # 如果是列表，提取文本内容
            text_parts = []
            for item in tool_result_content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
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
    
    def _build_base_message(self, message: Any, role: str, context: IConversionContext) -> Dict[str, Any]:
        """构建基础消息"""
        # 处理多模态内容
        content = self.process_multimodal_content(message.content)
        
        # 如果是纯文本，直接使用字符串
        if len(content) == 1 and content[0].get("type") == "text":
            text_content = content[0].get("text", "")
            openai_message = {
                "role": role,
                "content": text_content
            }
        else:
            # 多模态内容使用列表格式
            openai_message = {
                "role": role,
                "content": content
            }
        
        # 添加名称（如果有）
        if hasattr(message, 'name') and message.name:
            openai_message["name"] = message.name
        
        return openai_message
    
    def _handle_special_parameters(self, request_data: Dict[str, Any], parameters: Dict[str, Any], context: IConversionContext) -> None:
        """处理特殊参数"""
        # 处理response_format
        if "response_format" in parameters:
            request_data["response_format"] = parameters["response_format"]
        
        # 处理reasoning_effort (GPT-5特有)
        if "reasoning_effort" in parameters:
            request_data["reasoning_effort"] = parameters["reasoning_effort"]
        
        # 处理stream_options
        if "stream_options" in parameters:
            request_data["stream_options"] = parameters["stream_options"]
    
    def _handle_tools_configuration(self, request_data: Dict[str, Any], parameters: Dict[str, Any], context: IConversionContext) -> None:
        """处理工具配置"""
        if "tools" in parameters:
            tools = parameters["tools"]
            # 验证工具
            tool_errors = self.tools_adapter.validate_tools(tools, context)
            if tool_errors:
                self.logger.warning(f"工具验证失败: {tool_errors}")
            else:
                request_data["tools"] = self.convert_tools(tools)
                
                # 处理工具选择策略
                if "tool_choice" in parameters:
                    request_data["tool_choice"] = self.process_tool_choice(parameters["tool_choice"])
    
    def _build_response_metadata(self, response: Dict[str, Any], choice: Dict[str, Any]) -> Dict[str, Any]:
        """构建响应元数据"""
        return {
            "finish_reason": choice.get("finish_reason"),
            "usage": response.get("usage", {}),
            "model": response.get("model", ""),
            "id": response.get("id", ""),
            "created": response.get("created"),
            "system_fingerprint": response.get("system_fingerprint"),
            "service_tier": response.get("service_tier")
        }
    
    def _create_message_from_role(self, role: str, content: str, tool_calls: List[Dict[str, Any]], additional_kwargs: Dict[str, Any]) -> Any:
        """根据角色创建消息"""
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
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return "gpt-3.5-turbo"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-vision-preview",
            "o1-preview",
            "o1-mini"
        ]