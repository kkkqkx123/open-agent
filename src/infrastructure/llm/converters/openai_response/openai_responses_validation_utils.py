"""OpenAI Responses API验证工具类

提供OpenAI Responses API的验证和错误处理功能。
"""

from typing import Dict, Any, List, Optional, Union, Set
from src.services.logger.injection import get_logger
from src.infrastructure.llm.converters.base.base_validation_utils import (
    BaseValidationUtils,
    BaseValidationError,
    BaseFormatError
)


class OpenAIResponsesValidationError(BaseValidationError):
    """OpenAI Responses API验证错误"""
    pass


class OpenAIResponsesFormatError(BaseFormatError):
    """OpenAI Responses API格式错误"""
    pass


class OpenAIResponsesValidationUtils(BaseValidationUtils):
    """OpenAI Responses API验证工具类
    
    提供OpenAI Responses API特定的验证和错误处理功能。
    """
    
    def __init__(self) -> None:
        """初始化OpenAI Responses API验证工具"""
        super().__init__()
        self._supported_models = self._get_supported_models()
    
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
        errors = []
        
        # 验证必需参数
        required_fields = ["model", "input"]
        required_errors = self._validate_required_parameters(parameters, required_fields)
        errors.extend(required_errors)
        
        if required_errors:
            return errors  # 如果缺少必需参数，直接返回
        
        # 验证模型
        model_errors = self._validate_model_parameter(parameters.get("model") or "")
        errors.extend(model_errors)
        
        # 验证输入
        input_errors = self._validate_input_parameter(parameters.get("input") or "")
        errors.extend(input_errors)
        
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
        
        # 验证reasoning字段（如果存在）
        if "reasoning" in response:
            reasoning_errors = self._validate_reasoning(response["reasoning"])
            errors.extend(reasoning_errors)
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应"""
        error = error_response.get("error", {})
        error_type = error.get("type", "unknown")
        error_message = error.get("message", "未知错误")
        error_code = error.get("code", "")
        
        # OpenAI Responses API特定错误映射
        error_mapping = {
            "invalid_request_error": "请求参数无效",
            "invalid_api_key": "API密钥无效",
            "insufficient_quota": "API配额不足",
            "model_not_found": "模型不存在",
            "rate_limit_exceeded": "请求频率超限",
            "content_policy_violation": "内容违反政策",
            "context_length_exceeded": "上下文长度超限",
            "server_error": "服务器内部错误",
            "overloaded_error": "服务过载",
            "parameter_conflict_error": "参数冲突",
            "invalid_parameter_error": "参数无效"
        }
        
        friendly_message = error_mapping.get(error_type, f"未知错误类型: {error_type}")
        
        if error_code:
            return f"{friendly_message} ({error_code}): {error_message}"
        else:
            return f"{friendly_message}: {error_message}"
    
    def _validate_model_parameter(self, model: str) -> List[str]:
        """验证模型参数"""
        errors = []
        
        if not isinstance(model, str):
            errors.append("model参数必须是字符串")
            return errors
        
        if not model.strip():
            errors.append("model参数不能为空")
            return errors
        
        # 检查是否为支持的模型（Responses API只支持GPT-5系列）
        if model not in self._supported_models:
            errors.append(f"Responses API不支持的模型: {model}，支持的模型: {', '.join(sorted(self._supported_models))}")
        
        return errors
    
    def _validate_input_parameter(self, input_text: str) -> List[str]:
        """验证输入参数"""
        errors = []
        
        if not isinstance(input_text, str):
            errors.append("input参数必须是字符串")
            return errors
        
        if not input_text.strip():
            errors.append("input参数不能为空")
            return errors
        
        # 检查输入长度（假设的最大限制）
        max_length = 100000  # 100K字符
        if len(input_text) > max_length:
            errors.append(f"input参数长度不能超过{max_length}个字符")
        
        return errors
    
    def _validate_optional_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证可选参数"""
        errors = []
        
        # 验证reasoning配置
        if "reasoning" in parameters:
            reasoning_errors = self._validate_reasoning_parameter(parameters["reasoning"])
            errors.extend(reasoning_errors)
        
        # 验证text配置
        if "text" in parameters:
            text_errors = self._validate_text_parameter(parameters["text"])
            errors.extend(text_errors)
        
        # 验证tools
        if "tools" in parameters:
            tools_errors = self._validate_tools_parameter(parameters["tools"])
            errors.extend(tools_errors)
        
        # 验证previous_response_id
        if "previous_response_id" in parameters:
            prev_id_errors = self._validate_previous_response_id_parameter(parameters["previous_response_id"])
            errors.extend(prev_id_errors)
        
        return errors
    
    def _validate_reasoning_parameter(self, reasoning: Dict[str, Any]) -> List[str]:
        """验证reasoning参数"""
        errors = []
        
        if not isinstance(reasoning, dict):
            errors.append("reasoning参数必须是字典")
            return errors
        
        # 验证effort字段
        effort = reasoning.get("effort")
        if effort is not None:
            if not isinstance(effort, str):
                errors.append("reasoning.effort必须是字符串")
            else:
                valid_efforts = ["none", "low", "medium", "high"]
                if effort not in valid_efforts:
                    errors.append(f"reasoning.effort必须是以下值之一: {', '.join(valid_efforts)}")
        
        # 验证其他字段（如果有）
        for key in reasoning.keys():
            if key != "effort":
                errors.append(f"reasoning参数不支持字段: {key}")
        
        return errors
    
    def _validate_text_parameter(self, text: Dict[str, Any]) -> List[str]:
        """验证text参数"""
        errors = []
        
        if not isinstance(text, dict):
            errors.append("text参数必须是字典")
            return errors
        
        # 验证verbosity字段
        verbosity = text.get("verbosity")
        if verbosity is not None:
            if not isinstance(verbosity, str):
                errors.append("text.verbosity必须是字符串")
            else:
                valid_verbosities = ["low", "medium", "high"]
                if verbosity not in valid_verbosities:
                    errors.append(f"text.verbosity必须是以下值之一: {', '.join(valid_verbosities)}")
        
        # 验证其他字段（如果有）
        for key in text.keys():
            if key != "verbosity":
                errors.append(f"text参数不支持字段: {key}")
        
        return errors
    
    def _validate_tools_parameter(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证tools参数"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("tools参数必须是列表")
            return errors
        
        if len(tools) > 128:  # 假设的限制
            errors.append("tools列表最多包含128个工具")
        
        tool_names: Set[str] = set()
        for i, tool in enumerate(tools):
            tool_errors = self._validate_single_responses_tool(tool, i, tool_names)
            errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_responses_tool(self, tool: Dict[str, Any], index: int, existing_names: Set[str]) -> List[str]:
        """验证单个Responses API工具"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"tools[{index}]必须是字典")
            return errors
        
        # 验证type字段
        tool_type = tool.get("type")
        if tool_type != "custom":
            errors.append(f"tools[{index}].type必须是'custom'")
        
        # 验证name字段
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"tools[{index}].name必须是非空字符串")
        elif name in existing_names:
            errors.append(f"tools[{index}].name '{name}' 已存在")
        else:
            existing_names.add(name)
        
        # 验证description字段
        description = tool.get("description")
        if description is not None and not isinstance(description, str):
            errors.append(f"tools[{index}].description必须是字符串")
        
        # 验证其他字段（如果有）
        for key in tool.keys():
            if key not in ["type", "name", "description"]:
                errors.append(f"tools[{index}]不支持字段: {key}")
        
        return errors
    
    def _validate_previous_response_id_parameter(self, previous_response_id: str) -> List[str]:
        """验证previous_response_id参数"""
        errors = []
        
        if not isinstance(previous_response_id, str):
            errors.append("previous_response_id参数必须是字符串")
        elif not previous_response_id.strip():
            errors.append("previous_response_id参数不能为空")
        elif not previous_response_id.startswith("resp_"):
            errors.append("previous_response_id必须以'resp_'开头")
        
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
        
        # 验证message字段
        message = choice.get("message")
        if message is not None:
            if not isinstance(message, dict):
                errors.append(f"choices[{index}].message必须是字典")
            else:
                message_errors = self._validate_choice_message(message, index)
                errors.extend(message_errors)
        
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
                    tool_call_errors = self._validate_responses_tool_call(tool_call, choice_index, i)
                    errors.extend(tool_call_errors)
        
        return errors
    
    def _validate_responses_tool_call(self, tool_call: Dict[str, Any], choice_index: int, call_index: int) -> List[str]:
        """验证Responses API工具调用"""
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
        
        # 验证reasoning_tokens字段（Responses API特有）
        if "reasoning_tokens" in usage and not isinstance(usage["reasoning_tokens"], int):
            errors.append("usage.reasoning_tokens必须是整数")
        
        return errors
    
    def _validate_reasoning(self, reasoning: Dict[str, Any]) -> List[str]:
        """验证reasoning字段"""
        errors = []
        
        if not isinstance(reasoning, dict):
            errors.append("reasoning必须是字典")
            return errors
        
        # 验证chain_of_thought字段
        chain_of_thought = reasoning.get("chain_of_thought")
        if chain_of_thought is not None and not isinstance(chain_of_thought, str):
            errors.append("reasoning.chain_of_thought必须是字符串")
        
        # 验证effort_used字段
        effort_used = reasoning.get("effort_used")
        if effort_used is not None:
            valid_efforts = ["none", "low", "medium", "high"]
            if effort_used not in valid_efforts:
                errors.append(f"reasoning.effort_used必须是以下值之一: {', '.join(valid_efforts)}")
        
        # 验证steps字段
        steps = reasoning.get("steps")
        if steps is not None:
            if not isinstance(steps, list):
                errors.append("reasoning.steps必须是列表")
            else:
                for i, step in enumerate(steps):
                    if not isinstance(step, str):
                        errors.append(f"reasoning.steps[{i}]必须是字符串")
        
        return errors
    
    def _get_supported_models(self) -> Set[str]:
        """获取支持的模型列表（Responses API只支持GPT-5系列）"""
        return {
            "gpt-5", "gpt-5.1", "gpt-5-pro", "gpt-5-mini", "gpt-5-nano"
        }