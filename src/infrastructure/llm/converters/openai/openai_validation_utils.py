"""OpenAI验证工具类

提供OpenAI API的验证和错误处理功能。
"""

from typing import Dict, Any, List, Optional, Union, Set
from src.services.logger.injection import get_logger
from src.infrastructure.llm.converters.base.base_validation_utils import (
    BaseValidationUtils,
    BaseValidationError,
    BaseFormatError
)


class OpenAIValidationError(BaseValidationError):
    """OpenAI验证错误"""
    pass


class OpenAIFormatError(BaseFormatError):
    """OpenAI格式错误"""
    pass


class OpenAIValidationUtils(BaseValidationUtils):
    """OpenAI验证工具类
    
    提供OpenAI API特定的验证和错误处理功能。
    """
    
    def __init__(self) -> None:
        """初始化OpenAI验证工具"""
        super().__init__()
    
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
        errors = []
        
        # 验证必需参数
        required_fields = ["model", "messages"]
        required_errors = self._validate_required_parameters(parameters, required_fields)
        errors.extend(required_errors)
        
        if required_errors:
            return errors  # 如果缺少必需参数，直接返回
        
        # 验证模型
        model = parameters.get("model")
        if model is not None:
            model_errors = self._validate_model_parameter(model)
            errors.extend(model_errors)
        
        # 验证消息
        messages = parameters.get("messages")
        if messages is not None:
            messages_errors = self._validate_messages_parameter(messages)
            errors.extend(messages_errors)
        
        # 验证可选参数
        optional_errors = self._validate_optional_parameters(parameters)
        errors.extend(optional_errors)
        
        return errors
    
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证响应格式"""
        errors = []
        
        if not isinstance(response, dict):
            errors.append("响应必须是字典格式")
            return errors
        
        # 验证必需字段
        required_fields = ["id", "object", "created", "model", "choices"]
        for field in required_fields:
            if field not in response:
                errors.append(f"响应缺少必需字段: {field}")
        
        # 验证choices字段
        if "choices" in response:
            choices_errors = self._validate_choices(response["choices"])
            errors.extend(choices_errors)
        
        # 验证usage字段（如果存在）
        if "usage" in response:
            usage_errors = self._validate_usage(response["usage"])
            errors.extend(usage_errors)
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应"""
        error = error_response.get("error", {})
        error_type = error.get("type", "unknown")
        error_message = error.get("message", "未知错误")
        error_code = error.get("code", "")
        
        # OpenAI特定错误映射
        error_mapping = {
            "invalid_request_error": "请求参数无效",
            "invalid_api_key": "API密钥无效",
            "insufficient_quota": "API配额不足",
            "model_not_found": "模型不存在",
            "rate_limit_exceeded": "请求频率超限",
            "content_policy_violation": "内容违反政策",
            "context_length_exceeded": "上下文长度超限",
            "server_error": "服务器内部错误",
            "overloaded_error": "服务过载"
        }
        
        friendly_message = error_mapping.get(error_type, f"未知错误类型: {error_type}")
        
        if error_code:
            return f"{friendly_message} ({error_code}): {error_message}"
        else:
            return f"{friendly_message}: {error_message}"
    
    def _validate_model_parameter(self, model: str, config: Optional[Dict[str, Any]] = None) -> List[str]:
        """验证模型参数"""
        errors = []
        
        if not isinstance(model, str):
            errors.append("model参数必须是字符串")
            return errors
        
        if not model.strip():
            errors.append("model参数不能为空")
            return errors
        
        # 从配置中获取支持的模型列表
        if config and "models" in config:
            supported_models = set(config["models"])
            if isinstance(supported_models, list):
                supported_models = set(supported_models)
            # 使用基类的验证方法
            model_errors = super()._validate_model(model, supported_models)
            errors.extend(model_errors)
        else:
            errors.append(f"无法验证模型 {model}，缺少配置信息")
        
        return errors
    
    def _validate_messages_parameter(self, messages: List[Dict[str, Any]]) -> List[str]:
        """验证消息参数"""
        errors = []
        
        if not isinstance(messages, list):
            errors.append("messages参数必须是列表")
            return errors
        
        if not messages:
            errors.append("messages列表不能为空")
            return errors
        
        # 验证每个消息
        for i, message in enumerate(messages):
            message_errors = self._validate_single_message(message, i)
            errors.extend(message_errors)
        
        return errors
    
    def _validate_single_message(self, message: Dict[str, Any], index: int) -> List[str]:
        """验证单个消息"""
        errors = []
        
        if not isinstance(message, dict):
            errors.append(f"messages[{index}]必须是字典")
            return errors
        
        # 验证role字段
        role = message.get("role")
        if not isinstance(role, str):
            errors.append(f"messages[{index}].role必须是字符串")
        elif role not in ["system", "user", "assistant", "tool"]:
            errors.append(f"messages[{index}].role必须是以下值之一: system, user, assistant, tool")
        
        # 验证content字段
        content = message.get("content")
        if content is None:
            errors.append(f"messages[{index}].content不能为空")
        elif not isinstance(content, (str, list)):
            errors.append(f"messages[{index}].content必须是字符串或列表")
        elif isinstance(content, list):
            # 验证多模态内容
            content_errors = self._validate_multimodal_content(content, index)
            errors.extend(content_errors)
        
        # 验证tool消息的特殊字段
        if role == "tool":
            tool_call_id = message.get("tool_call_id")
            if not tool_call_id:
                errors.append(f"messages[{index}]的tool消息必须包含tool_call_id字段")
            elif not isinstance(tool_call_id, str):
                errors.append(f"messages[{index}].tool_call_id必须是字符串")
        
        # 验证name字段（如果存在）
        name = message.get("name")
        if name is not None and not isinstance(name, str):
            errors.append(f"messages[{index}].name必须是字符串")
        
        return errors
    
    def _validate_multimodal_content(self, content: List[Dict[str, Any]], message_index: int) -> List[str]:
        """验证多模态内容"""
        errors = []
        
        if not content:
            errors.append(f"messages[{message_index}].content列表不能为空")
            return errors
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"messages[{message_index}].content[{i}]必须是字典")
                continue
            
            item_type = item.get("type")
            if not item_type:
                errors.append(f"messages[{message_index}].content[{i}]缺少type字段")
                continue
            
            if item_type == "text":
                text = item.get("text")
                if not isinstance(text, str):
                    errors.append(f"messages[{message_index}].content[{i}].text必须是字符串")
            elif item_type == "image_url":
                image_url = item.get("image_url")
                if not isinstance(image_url, dict):
                    errors.append(f"messages[{message_index}].content[{i}].image_url必须是字典")
                else:
                    url = image_url.get("url")
                    if not isinstance(url, str):
                        errors.append(f"messages[{message_index}].content[{i}].image_url.url必须是字符串")
            else:
                errors.append(f"messages[{message_index}].content[{i}]有不支持的类型: {item_type}")
        
        return errors
    
    def _validate_optional_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证可选参数"""
        errors = []
        
        # 验证temperature
        if "temperature" in parameters:
            temp_errors = self._validate_temperature(parameters["temperature"], 0.0, 2.0)
            errors.extend(temp_errors)
        
        # 验证top_p
        if "top_p" in parameters:
            top_p_errors = self._validate_top_p(parameters["top_p"], 0.0, 1.0)
            errors.extend(top_p_errors)
        
        # 验证max_tokens
        if "max_tokens" in parameters:
            model = parameters.get("model")
            max_tokens_errors = self._validate_max_tokens(
                parameters["max_tokens"],
                model
            )
            errors.extend(max_tokens_errors)
        
        # 验证stop
        if "stop" in parameters:
            stop_errors = self._validate_stop_parameter(parameters["stop"])
            errors.extend(stop_errors)
        
        # 验证stream
        if "stream" in parameters:
            if not isinstance(parameters["stream"], bool):
                errors.append("stream参数必须是布尔值")
        
        # 验证tools
        if "tools" in parameters:
            tools_errors = self._validate_tools_parameter(parameters["tools"])
            errors.extend(tools_errors)
        
        # 验证tool_choice
        if "tool_choice" in parameters:
            tool_choice_errors = self._validate_tool_choice_parameter(parameters["tool_choice"])
            errors.extend(tool_choice_errors)
        
        # 验证response_format
        if "response_format" in parameters:
            response_format_errors = self._validate_response_format_parameter(parameters["response_format"])
            errors.extend(response_format_errors)
        
        # 验证reasoning_effort (GPT-5特有)
        if "reasoning_effort" in parameters:
            reasoning_errors = self._validate_reasoning_effort_parameter(parameters["reasoning_effort"])
            errors.extend(reasoning_errors)
        
        return errors
    
    def _validate_stop_parameter(self, stop: Union[str, List[str]]) -> List[str]:
        """验证stop参数"""
        errors = []
        
        if isinstance(stop, str):
            if not stop.strip():
                errors.append("stop字符串不能为空")
        elif isinstance(stop, list):
            if len(stop) > 4:
                errors.append("stop列表最多包含4个元素")
            for i, item in enumerate(stop):
                if not isinstance(item, str):
                    errors.append(f"stop[{i}]必须是字符串")
                elif not item.strip():
                    errors.append(f"stop[{i}]不能为空")
        else:
            errors.append("stop参数必须是字符串或字符串列表")
        
        return errors
    
    def _validate_tools_parameter(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证tools参数"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("tools参数必须是列表")
            return errors
        
        if len(tools) > 128:  # OpenAI限制
            errors.append("tools列表最多包含128个工具")
        
        tool_names = set()
        for i, tool in enumerate(tools):
            tool_errors = self._validate_single_tool(tool, i, tool_names)
            errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_tool(self, tool: Dict[str, Any], index: int, existing_names: Set[str]) -> List[str]:
        """验证单个工具"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"tools[{index}]必须是字典")
            return errors
        
        # 验证type字段
        tool_type = tool.get("type")
        if tool_type != "function":
            errors.append(f"tools[{index}].type必须是'function'")
        
        # 验证function字段
        function = tool.get("function")
        if not isinstance(function, dict):
            errors.append(f"tools[{index}].function必须是字典")
            return errors
        
        # 验证function.name
        name = function.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"tools[{index}].function.name必须是非空字符串")
        elif name in existing_names:
            errors.append(f"tools[{index}].function.name '{name}' 已存在")
        else:
            existing_names.add(name)
        
        # 验证function.description
        description = function.get("description")
        if description is not None and not isinstance(description, str):
            errors.append(f"tools[{index}].function.description必须是字符串")
        
        # 验证function.parameters
        if "parameters" in function:
            parameters = function["parameters"]
            if not isinstance(parameters, dict):
                errors.append(f"tools[{index}].function.parameters必须是字典")
            else:
                param_errors = self._validate_tool_parameters(parameters, index)
                errors.extend(param_errors)
        
        return errors
    
    def _validate_tool_choice_parameter(self, tool_choice: Union[str, Dict[str, Any]]) -> List[str]:
        """验证tool_choice参数"""
        errors = []
        
        if isinstance(tool_choice, str):
            valid_choices = ["none", "auto", "required"]
            if tool_choice not in valid_choices:
                errors.append(f"tool_choice字符串必须是以下值之一: {', '.join(valid_choices)}")
        elif isinstance(tool_choice, dict):
            if "type" not in tool_choice or tool_choice["type"] != "function":
                errors.append("tool_choice字典必须包含type字段且值为'function'")
            
            function = tool_choice.get("function")
            if not isinstance(function, dict) or "name" not in function:
                errors.append("tool_choice字典必须包含function.name字段")
        else:
            errors.append("tool_choice参数必须是字符串或字典")
        
        return errors
    
    def _validate_response_format_parameter(self, response_format: Dict[str, Any]) -> List[str]:
        """验证response_format参数"""
        errors = []
        
        if not isinstance(response_format, dict):
            errors.append("response_format参数必须是字典")
            return errors
        
        format_type = response_format.get("type")
        if format_type not in ["text", "json_object", "json_schema"]:
            errors.append("response_format.type必须是以下值之一: text, json_object, json_schema")
        
        if format_type == "json_schema":
            json_schema = response_format.get("json_schema")
            if not isinstance(json_schema, dict):
                errors.append("response_format.json_schema必须是字典")
            else:
                schema_errors = self._validate_json_schema(json_schema)
                errors.extend(schema_errors)
        
        return errors
    
    def _validate_json_schema(self, json_schema: Dict[str, Any]) -> List[str]:
        """验证JSON Schema"""
        errors = []
        
        # 验证必需字段
        if "name" not in json_schema:
            errors.append("json_schema必须包含name字段")
        elif not isinstance(json_schema["name"], str):
            errors.append("json_schema.name必须是字符串")
        
        if "schema" not in json_schema:
            errors.append("json_schema必须包含schema字段")
        elif not isinstance(json_schema["schema"], dict):
            errors.append("json_schema.schema必须是字典")
        
        return errors
    
    def _validate_reasoning_effort_parameter(self, reasoning_effort: str) -> List[str]:
        """验证reasoning_effort参数"""
        errors = []
        
        if not isinstance(reasoning_effort, str):
            errors.append("reasoning_effort参数必须是字符串")
        else:
            valid_efforts = ["none", "minimal", "low", "medium", "high"]
            if reasoning_effort not in valid_efforts:
                errors.append(f"reasoning_effort必须是以下值之一: {', '.join(valid_efforts)}")
        
        return errors
    
    def _validate_choices(self, choices: List[Dict[str, Any]]) -> List[str]:
        """验证choices字段"""
        errors = []
        
        if not isinstance(choices, list):
            errors.append("choices必须是列表")
            return errors
        
        if not choices:
            errors.append("choices列表不能为空")
            return errors
        
        for i, choice in enumerate(choices):
            choice_errors = self._validate_single_choice(choice, i)
            errors.extend(choice_errors)
        
        return errors
    
    def _validate_single_choice(self, choice: Dict[str, Any], index: int) -> List[str]:
        """验证单个choice"""
        errors = []
        
        if not isinstance(choice, dict):
            errors.append(f"choices[{index}]必须是字典")
            return errors
        
        # 验证index字段
        if "index" in choice and not isinstance(choice["index"], int):
            errors.append(f"choices[{index}].index必须是整数")
        
        # 验证message字段
        message = choice.get("message")
        if message is not None:
            if not isinstance(message, dict):
                errors.append(f"choices[{index}].message必须是字典")
            else:
                message_errors = self._validate_choice_message(message, index)
                errors.extend(message_errors)
        
        # 验证finish_reason字段
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None:
            valid_reasons = ["stop", "length", "tool_calls", "content_filter", "function_call"]
            if finish_reason not in valid_reasons:
                errors.append(f"choices[{index}].finish_reason必须是以下值之一: {', '.join(valid_reasons)}")
        
        return errors
    
    def _validate_choice_message(self, message: Dict[str, Any], choice_index: int) -> List[str]:
        """验证choice中的message"""
        errors = []
        
        # 验证role字段
        role = message.get("role")
        if role is not None and role != "assistant":
            errors.append(f"choices[{choice_index}].message.role必须是'assistant'")
        
        # 验证content字段
        content = message.get("content")
        if content is not None and not isinstance(content, str):
            errors.append(f"choices[{choice_index}].message.content必须是字符串")
        
        # 验证tool_calls字段
        tool_calls = message.get("tool_calls")
        if tool_calls is not None:
            if not isinstance(tool_calls, list):
                errors.append(f"choices[{choice_index}].message.tool_calls必须是列表")
            else:
                for i, tool_call in enumerate(tool_calls):
                    tool_call_errors = self._validate_tool_call(tool_call, choice_index, i)
                    errors.extend(tool_call_errors)
        
        return errors
    
    def _validate_tool_call(self, tool_call: Dict[str, Any], choice_index: int, call_index: int) -> List[str]:
        """验证工具调用"""
        errors = []
        
        if not isinstance(tool_call, dict):
            errors.append(f"choices[{choice_index}].message.tool_calls[{call_index}]必须是字典")
            return errors
        
        # 验证id字段
        if "id" in tool_call and not isinstance(tool_call["id"], str):
            errors.append(f"choices[{choice_index}].message.tool_calls[{call_index}].id必须是字符串")
        
        # 验证type字段
        call_type = tool_call.get("type")
        if call_type is not None and call_type != "function":
            errors.append(f"choices[{choice_index}].message.tool_calls[{call_index}].type必须是'function'")
        
        # 验证function字段
        function = tool_call.get("function")
        if function is not None:
            if not isinstance(function, dict):
                errors.append(f"choices[{choice_index}].message.tool_calls[{call_index}].function必须是字典")
            else:
                if "name" in function and not isinstance(function["name"], str):
                    errors.append(f"choices[{choice_index}].message.tool_calls[{call_index}].function.name必须是字符串")
                
                if "arguments" in function and not isinstance(function["arguments"], str):
                    errors.append(f"choices[{choice_index}].message.tool_calls[{call_index}].function.arguments必须是字符串")
        
        return errors
    
    def _validate_usage(self, usage: Dict[str, Any]) -> List[str]:
        """验证usage字段"""
        errors = []
        
        if not isinstance(usage, dict):
            errors.append("usage必须是字典")
            return errors
        
        # 验证token计数字段
        token_fields = ["prompt_tokens", "completion_tokens", "total_tokens"]
        for field in token_fields:
            if field in usage and not isinstance(usage[field], int):
                errors.append(f"usage.{field}必须是整数")
        
        return errors
    