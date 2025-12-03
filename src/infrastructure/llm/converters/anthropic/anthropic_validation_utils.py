"""Anthropic验证和错误处理工具

专门处理Anthropic API的验证和错误处理逻辑。
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger
from src.infrastructure.llm.converters.base.base_validation_utils import BaseValidationUtils, BaseValidationError, BaseFormatError


class AnthropicValidationError(BaseValidationError):
    """Anthropic验证错误"""
    pass


class AnthropicFormatError(BaseFormatError):
    """Anthropic格式错误"""
    pass


class AnthropicValidationUtils(BaseValidationUtils):
    """Anthropic验证工具类"""
    
    # 支持的模型列表
    SUPPORTED_MODELS = {
        "claude-sonnet-4-5",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2"
    }
    
    # 最大token限制
    MAX_TOKENS_LIMITS = {
        "claude-sonnet-4-5": 8192,
        "claude-3-opus": 4096,
        "claude-3-sonnet": 4096,
        "claude-3-haiku": 4096,
        "claude-2.1": 4096,
        "claude-2.0": 4096,
        "claude-instant-1.2": 4096
    }
    
    def __init__(self) -> None:
        """初始化验证工具"""
        super().__init__()
    
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
        errors = []
        
        # 验证必需参数
        if "model" not in parameters:
            errors.append("缺少必需的model参数")
        else:
            model_errors = self._validate_model(parameters["model"])
            errors.extend(model_errors)
        
        if "max_tokens" not in parameters:
            errors.append("缺少必需的max_tokens参数")
        else:
            max_tokens_errors = self._validate_max_tokens(
                parameters["max_tokens"], 
                parameters.get("model")
            )
            errors.extend(max_tokens_errors)
        
        # 验证可选参数
        optional_params = {
            "temperature": self._validate_temperature,
            "top_p": self._validate_top_p,
            "top_k": self._validate_top_k,
            "stop_sequences": self._validate_stop_sequences,
            "stream": self._validate_stream,
            "metadata": self._validate_metadata,
            "tools": self._validate_tools,
            "tool_choice": self._validate_tool_choice,
            "system": self._validate_system
        }
        
        for param, validator in optional_params.items():
            if param in parameters:
                param_errors = validator(parameters[param])
                errors.extend(param_errors)
        
        return errors
    
    def _validate_model(self, model: str) -> List[str]:
        """验证模型参数"""
        return self._validate_model(model, self.SUPPORTED_MODELS)
    
    def _validate_max_tokens(self, max_tokens: int, model: Optional[str]) -> List[str]:
        """验证max_tokens参数"""
        errors = []
        
        if not isinstance(max_tokens, int):
            errors.append("max_tokens参数必须是整数")
        elif max_tokens <= 0:
            errors.append("max_tokens参数必须大于0")
        elif max_tokens > 8192:
            errors.append("max_tokens参数不能超过8192")
        elif model and model in self.MAX_TOKENS_LIMITS:
            limit = self.MAX_TOKENS_LIMITS[model]
            if max_tokens > limit:
                errors.append(f"模型 {model} 的max_tokens不能超过 {limit}")
        
        return errors
    
    def _validate_temperature(self, temperature: Union[int, float]) -> List[str]:
        """验证temperature参数"""
        return self._validate_temperature(temperature, 0.0, 1.0)
    
    def _validate_top_p(self, top_p: Union[int, float]) -> List[str]:
        """验证top_p参数"""
        return self._validate_top_p(top_p, 0.0, 1.0)
    
    def _validate_top_k(self, top_k: int) -> List[str]:
        """验证top_k参数"""
        errors = []
        
        if not isinstance(top_k, int):
            errors.append("top_k参数必须是整数")
        elif top_k < 0:
            errors.append("top_k参数必须大于等于0")
        elif top_k > 500:
            errors.append("top_k参数不能超过500")
        
        return errors
    
    def _validate_stop_sequences(self, stop_sequences: List[str]) -> List[str]:
        """验证stop_sequences参数"""
        errors = []
        
        if not isinstance(stop_sequences, list):
            errors.append("stop_sequences参数必须是列表")
        elif len(stop_sequences) > 4:
            errors.append("stop_sequences最多支持4个序列")
        else:
            for i, sequence in enumerate(stop_sequences):
                if not isinstance(sequence, str):
                    errors.append(f"stop_sequences[{i}]必须是字符串")
                elif not sequence.strip():
                    errors.append(f"stop_sequences[{i}]不能为空")
        
        return errors
    
    def _validate_stream(self, stream: bool) -> List[str]:
        """验证stream参数"""
        if not isinstance(stream, bool):
            return ["stream参数必须是布尔值"]
        return []
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """验证metadata参数"""
        errors = []
        
        if not isinstance(metadata, dict):
            errors.append("metadata参数必须是字典")
        elif len(metadata) > 10:
            errors.append("metadata参数不能超过10个键值对")
        else:
            for key, value in metadata.items():
                if not isinstance(key, str):
                    errors.append(f"metadata的键必须是字符串: {key}")
                elif not isinstance(value, (str, int, float, bool)):
                    errors.append(f"metadata的值必须是基本类型: {key}")
        
        return errors
    
    def _validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证tools参数"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("tools参数必须是列表")
        elif len(tools) > 100:
            errors.append("tools参数不能超过100个工具")
        else:
            tool_names = set()
            for i, tool in enumerate(tools):
                tool_errors = self._validate_single_tool(tool, i, tool_names)
                errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_tool(
        self, 
        tool: Dict[str, Any], 
        index: int, 
        existing_names: set
    ) -> List[str]:
        """验证单个工具"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"tools[{index}]必须是字典")
            return errors
        
        # 验证名称
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"tools[{index}]缺少有效的名称")
        elif name in existing_names:
            errors.append(f"tools[{index}]的名称'{name}'已存在")
        else:
            existing_names.add(name)
        
        # 验证描述
        description = tool.get("description", "")
        if not isinstance(description, str):
            errors.append(f"tools[{index}]的描述必须是字符串")
        
        # 验证参数
        if "input_schema" in tool:
            parameters = tool["input_schema"]
            if not isinstance(parameters, dict):
                errors.append(f"tools[{index}]的input_schema必须是字典")
            else:
                param_errors = self._validate_tool_parameters(parameters, index)
                errors.extend(param_errors)
        
        return errors
    
    def _validate_tool_parameters(self, parameters: Dict[str, Any], tool_index: int) -> List[str]:
        """验证工具参数"""
        errors = []
        
        # 验证类型
        param_type = parameters.get("type")
        if param_type != "object":
            errors.append(f"tools[{tool_index}].input_schema.type必须是object")
        
        # 验证properties
        properties = parameters.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"tools[{tool_index}].input_schema.properties必须是字典")
        else:
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    errors.append(f"tools[{tool_index}].input_schema.properties.{prop_name}必须是字典")
                    continue
                
                if "type" not in prop_schema:
                    errors.append(f"tools[{tool_index}].input_schema.properties.{prop_name}缺少type字段")
        
        # 验证required
        required = parameters.get("required", [])
        if not isinstance(required, list):
            errors.append(f"tools[{tool_index}].input_schema.required必须是列表")
        else:
            for req_name in required:
                if req_name not in properties:
                    errors.append(f"tools[{tool_index}].input_schema.required中的'{req_name}'不在properties中")
        
        return errors
    
    def _validate_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> List[str]:
        """验证tool_choice参数"""
        errors = []
        
        if isinstance(tool_choice, str):
            if tool_choice not in {"auto", "none"}:
                errors.append("tool_choice字符串必须是'auto'或'none'")
        elif isinstance(tool_choice, dict):
            choice_type = tool_choice.get("type")
            if choice_type == "any":
                # 无需额外验证
                pass
            elif choice_type == "tool":
                tool_name = tool_choice.get("name")
                if not isinstance(tool_name, str) or not tool_name.strip():
                    errors.append("tool_choice.tool类型必须提供有效的name")
            else:
                errors.append("tool_choice字典的type必须是'any'或'tool'")
        else:
            errors.append("tool_choice必须是字符串或字典")
        
        return errors
    
    def _validate_system(self, system: Union[str, List[Dict[str, Any]]]) -> List[str]:
        """验证system参数"""
        errors = []
        
        if isinstance(system, str):
            if len(system) > 200000:
                errors.append("system消息长度不能超过200000个字符")
        elif isinstance(system, list):
            if len(system) > 10:
                errors.append("system消息列表不能超过10个元素")
            
            for i, item in enumerate(system):
                if not isinstance(item, dict):
                    errors.append(f"system消息[{i}]必须是字典")
                elif item.get("type") == "text":
                    if not isinstance(item.get("text"), str):
                        errors.append(f"system消息[{i}]的text字段必须是字符串")
                else:
                    errors.append(f"system消息[{i}]的type必须是'text'")
        else:
            errors.append("system参数必须是字符串或列表")
        
        return errors
    
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证响应格式"""
        errors = []
        
        # 验证必需字段
        required_fields = ["id", "type", "role", "content"]
        for field in required_fields:
            if field not in response:
                errors.append(f"响应缺少必需字段: {field}")
        
        # 验证字段类型
        if "id" in response and not isinstance(response["id"], str):
            errors.append("响应的id字段必须是字符串")
        
        if "type" in response and response["type"] != "message":
            errors.append("响应的type字段必须是'message'")
        
        if "role" in response and response["role"] != "assistant":
            errors.append("响应的role字段必须是'assistant'")
        
        if "content" in response:
            content_errors = self._validate_response_content(response["content"])
            errors.extend(content_errors)
        
        # 验证可选字段
        if "model" in response and not isinstance(response["model"], str):
            errors.append("响应的model字段必须是字符串")
        
        if "stop_reason" in response:
            valid_stop_reasons = {"end_turn", "max_tokens", "stop_sequence", "tool_use"}
            if response["stop_reason"] not in valid_stop_reasons:
                errors.append(f"响应的stop_reason无效: {response['stop_reason']}")
        
        if "usage" in response:
            usage_errors = self._validate_usage(response["usage"])
            errors.extend(usage_errors)
        
        return errors
    
    def _validate_response_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证响应内容"""
        errors = []
        
        if not isinstance(content, list):
            errors.append("响应的content字段必须是列表")
            return errors
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"content[{i}]必须是字典")
                continue
            
            item_type = item.get("type")
            if not item_type:
                errors.append(f"content[{i}]缺少type字段")
                continue
            
            if item_type == "text":
                if "text" not in item:
                    errors.append(f"content[{i}]的text类型缺少text字段")
                elif not isinstance(item["text"], str):
                    errors.append(f"content[{i}]的text字段必须是字符串")
            elif item_type == "tool_use":
                required_tool_fields = ["id", "name", "input"]
                for field in required_tool_fields:
                    if field not in item:
                        errors.append(f"content[{i}]的tool_use类型缺少{field}字段")
            elif item_type == "tool_result":
                required_result_fields = ["tool_use_id"]
                for field in required_result_fields:
                    if field not in item:
                        errors.append(f"content[{i}]的tool_result类型缺少{field}字段")
            else:
                errors.append(f"content[{i}]有未知类型: {item_type}")
        
        return errors
    
    def _validate_usage(self, usage: Dict[str, Any]) -> List[str]:
        """验证使用统计"""
        errors = []
        
        if not isinstance(usage, dict):
            errors.append("usage字段必须是字典")
            return errors
        
        required_fields = ["input_tokens", "output_tokens"]
        for field in required_fields:
            if field not in usage:
                errors.append(f"usage缺少{field}字段")
            elif not isinstance(usage[field], int) or usage[field] < 0:
                errors.append(f"usage的{field}字段必须是非负整数")
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应"""
        error_type = error_response.get("error", {}).get("type", "unknown")
        error_message = error_response.get("error", {}).get("message", "未知错误")
        
        # 根据错误类型提供友好的错误消息
        error_mappings = {
            "invalid_request_error": "请求参数无效",
            "authentication_error": "认证失败，请检查API密钥",
            "permission_error": "权限不足",
            "not_found_error": "请求的资源不存在",
            "rate_limit_error": "请求频率过高，请稍后重试",
            "api_error": "API内部错误",
            "overloaded_error": "服务过载，请稍后重试"
        }
        
        friendly_message = error_mappings.get(error_type, f"未知错误类型: {error_type}")
        return f"{friendly_message}: {error_message}"