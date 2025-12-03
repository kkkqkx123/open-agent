"""Gemini验证和错误处理工具

专门处理Gemini API的验证和错误处理逻辑。
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger


class GeminiValidationError(Exception):
    """Gemini验证错误"""
    pass


class GeminiFormatError(Exception):
    """Gemini格式错误"""
    pass


class GeminiValidationUtils:
    """Gemini验证工具类"""
    
    # 支持的模型列表
    SUPPORTED_MODELS = {
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    }
    
    # 最大token限制
    MAX_TOKENS_LIMITS = {
        "gemini-2.0-flash": 8192,
        "gemini-2.5-flash": 8192,
        "gemini-2.5-pro": 8192,
        "gemini-1.5-pro": 8192,
        "gemini-1.5-flash": 8192
    }
    
    # 思考预算级别
    THINKING_BUDGET_LEVELS = {"low", "medium", "high"}
    
    # 推理努力级别
    REASONING_EFFORT_LEVELS = {"none", "low", "medium", "high"}
    
    def __init__(self) -> None:
        """初始化验证工具"""
        self.logger = get_logger(__name__)
    
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证必需参数
        if "model" not in parameters:
            errors.append("缺少必需的model参数")
        else:
            model_errors = self._validate_model(parameters["model"])
            errors.extend(model_errors)
        
        # 验证可选参数
        optional_params = {
            "temperature": self._validate_temperature,
            "top_p": self._validate_top_p,
            "top_k": self._validate_top_k,
            "max_output_tokens": self._validate_max_output_tokens,
            "candidate_count": self._validate_candidate_count,
            "stop_sequences": self._validate_stop_sequences,
            "response_mime_type": self._validate_response_mime_type,
            "presence_penalty": self._validate_presence_penalty,
            "frequency_penalty": self._validate_frequency_penalty,
            "seed": self._validate_seed,
            "tools": self._validate_tools,
            "tool_choice": self._validate_tool_choice,
            "reasoning_effort": self._validate_reasoning_effort,
            "extra_body": self._validate_extra_body
        }
        
        for param, validator in optional_params.items():
            if param in parameters:
                param_errors = validator(parameters[param])  # type: ignore
                errors.extend(param_errors)
        
        return errors
    
    def _validate_model(self, model: str) -> List[str]:
        """验证模型参数"""
        errors = []
        
        if not isinstance(model, str):
            errors.append("model参数必须是字符串")
        elif model not in self.SUPPORTED_MODELS:
            errors.append(f"不支持的模型: {model}，支持的模型: {', '.join(self.SUPPORTED_MODELS)}")
        
        return errors
    
    def _validate_temperature(self, temperature: Union[int, float]) -> List[str]:
        """验证temperature参数"""
        errors = []
        
        if not isinstance(temperature, (int, float)):
            errors.append("temperature参数必须是数字")
        elif temperature < 0.0 or temperature > 2.0:
            errors.append("temperature参数必须在0.0-2.0范围内")
        
        return errors
    
    def _validate_top_p(self, top_p: Union[int, float]) -> List[str]:
        """验证top_p参数"""
        errors = []
        
        if not isinstance(top_p, (int, float)):
            errors.append("top_p参数必须是数字")
        elif top_p <= 0.0 or top_p > 1.0:
            errors.append("top_p参数必须在0.0-1.0范围内")
        
        return errors
    
    def _validate_top_k(self, top_k: int) -> List[str]:
        """验证top_k参数"""
        errors = []
        
        if not isinstance(top_k, int):
            errors.append("top_k参数必须是整数")
        elif top_k <= 0 or top_k > 100:
            errors.append("top_k参数必须在1-100范围内")
        
        return errors
    
    def _validate_max_output_tokens(self, max_output_tokens: int) -> List[str]:
        """验证max_output_tokens参数"""
        errors = []
        
        if not isinstance(max_output_tokens, int):
            errors.append("max_output_tokens参数必须是整数")
        elif max_output_tokens <= 0:
            errors.append("max_output_tokens参数必须大于0")
        elif max_output_tokens > 8192:
            errors.append("max_output_tokens参数不能超过8192")
        
        return errors
    
    def _validate_candidate_count(self, candidate_count: int) -> List[str]:
        """验证candidate_count参数"""
        errors = []
        
        if not isinstance(candidate_count, int):
            errors.append("candidate_count参数必须是整数")
        elif candidate_count <= 0 or candidate_count > 8:
            errors.append("candidate_count参数必须在1-8范围内")
        
        return errors
    
    def _validate_stop_sequences(self, stop_sequences: List[str]) -> List[str]:
        """验证stop_sequences参数"""
        errors = []
        
        if not isinstance(stop_sequences, list):
            errors.append("stop_sequences参数必须是列表")
        elif len(stop_sequences) > 5:
            errors.append("stop_sequences最多支持5个序列")
        else:
            for i, sequence in enumerate(stop_sequences):
                if not isinstance(sequence, str):
                    errors.append(f"stop_sequences[{i}]必须是字符串")
                elif not sequence.strip():
                    errors.append(f"stop_sequences[{i}]不能为空")
        
        return errors
    
    def _validate_response_mime_type(self, response_mime_type: str) -> List[str]:
        """验证response_mime_type参数"""
        errors = []
        
        if not isinstance(response_mime_type, str):
            errors.append("response_mime_type参数必须是字符串")
        else:
            valid_types = {
                "text/plain",
                "application/json",
                "text/html",
                "application/xml"
            }
            if response_mime_type not in valid_types:
                errors.append(f"不支持的response_mime_type: {response_mime_type}")
        
        return errors
    
    def _validate_presence_penalty(self, presence_penalty: Union[int, float]) -> List[str]:
        """验证presence_penalty参数"""
        errors = []
        
        if not isinstance(presence_penalty, (int, float)):
            errors.append("presence_penalty参数必须是数字")
        elif presence_penalty < -2.0 or presence_penalty > 2.0:
            errors.append("presence_penalty参数必须在-2.0到2.0范围内")
        
        return errors
    
    def _validate_frequency_penalty(self, frequency_penalty: Union[int, float]) -> List[str]:
        """验证frequency_penalty参数"""
        errors = []
        
        if not isinstance(frequency_penalty, (int, float)):
            errors.append("frequency_penalty参数必须是数字")
        elif frequency_penalty < -2.0 or frequency_penalty > 2.0:
            errors.append("frequency_penalty参数必须在-2.0到2.0范围内")
        
        return errors
    
    def _validate_seed(self, seed: int) -> List[str]:
        """验证seed参数"""
        errors = []
        
        if not isinstance(seed, int):
            errors.append("seed参数必须是整数")
        elif seed < 0:
            errors.append("seed参数必须是非负整数")
        
        return errors
    
    def _validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证tools参数"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("tools参数必须是列表")
        elif len(tools) > 64:
            errors.append("tools参数不能超过64个工具")
        else:
            tool_names: set[str] = set()
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
        if "parameters" in tool:
            parameters = tool["parameters"]
            if not isinstance(parameters, dict):
                errors.append(f"tools[{index}]的参数必须是字典")
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
            errors.append(f"tools[{tool_index}].parameters.type必须是object")
        
        # 验证properties
        properties = parameters.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"tools[{tool_index}].parameters.properties必须是字典")
        else:
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    errors.append(f"tools[{tool_index}].parameters.properties.{prop_name}必须是字典")
                    continue
                
                if "type" not in prop_schema:
                    errors.append(f"tools[{tool_index}].parameters.properties.{prop_name}缺少type字段")
        
        # 验证required
        required = parameters.get("required", [])
        if not isinstance(required, list):
            errors.append(f"tools[{tool_index}].parameters.required必须是列表")
        else:
            for req_name in required:
                if req_name not in properties:
                    errors.append(f"tools[{tool_index}].parameters.required中的'{req_name}'不在properties中")
        
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
    
    def _validate_reasoning_effort(self, reasoning_effort: str) -> List[str]:
        """验证reasoning_effort参数"""
        errors = []
        
        if not isinstance(reasoning_effort, str):
            errors.append("reasoning_effort参数必须是字符串")
        elif reasoning_effort not in self.REASONING_EFFORT_LEVELS:
            errors.append(f"reasoning_effort必须是以下值之一: {', '.join(self.REASONING_EFFORT_LEVELS)}")
        
        return errors
    
    def _validate_extra_body(self, extra_body: Dict[str, Any]) -> List[str]:
        """验证extra_body参数"""
        errors = []
        
        if not isinstance(extra_body, dict):
            errors.append("extra_body参数必须是字典")
            return errors
        
        # 验证Google特定配置
        google_config = extra_body.get("google")
        if google_config:
            if not isinstance(google_config, dict):
                errors.append("extra_body.google必须是字典")
            else:
                google_errors = self._validate_google_config(google_config)
                errors.extend(google_errors)
        
        return errors
    
    def _validate_google_config(self, google_config: Dict[str, Any]) -> List[str]:
        """验证Google特定配置"""
        errors = []
        
        # 验证思考配置
        thinking_config = google_config.get("thinking_config")
        if thinking_config:
            if not isinstance(thinking_config, dict):
                errors.append("google.thinking_config必须是字典")
            else:
                thinking_errors = self._validate_thinking_config(thinking_config)
                errors.extend(thinking_errors)
        
        # 验证缓存内容
        cached_content = google_config.get("cached_content")
        if cached_content:
            if not isinstance(cached_content, str):
                errors.append("google.cached_content必须是字符串")
            elif not cached_content.startswith("cachedContents/"):
                errors.append("google.cached_content格式无效，应以'cachedContents/'开头")
        
        return errors
    
    def _validate_thinking_config(self, thinking_config: Dict[str, Any]) -> List[str]:
        """验证思考配置"""
        errors = []
        
        # 验证思考预算
        thinking_budget = thinking_config.get("thinking_budget")
        if thinking_budget:
            if not isinstance(thinking_budget, str):
                errors.append("thinking_config.thinking_budget必须是字符串")
            elif thinking_budget not in self.THINKING_BUDGET_LEVELS:
                errors.append(f"thinking_config.thinking_budget必须是以下值之一: {', '.join(self.THINKING_BUDGET_LEVELS)}")
        
        # 验证包含思考
        include_thoughts = thinking_config.get("include_thoughts")
        if include_thoughts is not None:
            if not isinstance(include_thoughts, bool):
                errors.append("thinking_config.include_thoughts必须是布尔值")
        
        return errors
    
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证响应格式
        
        Args:
            response: API响应
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证必需字段
        if "candidates" not in response:
            errors.append("响应缺少candidates字段")
        else:
            candidates_errors = self._validate_candidates(response["candidates"])
            errors.extend(candidates_errors)
        
        # 验证可选字段
        if "usageMetadata" in response:
            usage_errors = self._validate_usage_metadata(response["usageMetadata"])
            errors.extend(usage_errors)
        
        return errors
    
    def _validate_candidates(self, candidates: List[Dict[str, Any]]) -> List[str]:
        """验证候选响应"""
        errors = []
        
        if not isinstance(candidates, list):
            errors.append("candidates字段必须是列表")
            return errors
        
        if len(candidates) == 0:
            errors.append("candidates列表不能为空")
        
        for i, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                errors.append(f"candidates[{i}]必须是字典")
                continue
            
            # 验证content字段
            if "content" in candidate:
                content_errors = self._validate_candidate_content(candidate["content"], i)
                errors.extend(content_errors)
            
            # 验证finishReason字段
            if "finishReason" in candidate:
                finish_reason = candidate["finishReason"]
                valid_reasons = {"STOP", "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER"}
                if finish_reason not in valid_reasons:
                    errors.append(f"candidates[{i}].finishReason无效: {finish_reason}")
        
        return errors
    
    def _validate_candidate_content(self, content: Dict[str, Any], index: int) -> List[str]:
        """验证候选内容"""
        errors = []
        
        if not isinstance(content, dict):
            errors.append(f"candidates[{index}].content必须是字典")
            return errors
        
        # 验证parts字段
        if "parts" not in content:
            errors.append(f"candidates[{index}].content缺少parts字段")
        else:
            parts = content["parts"]
            if not isinstance(parts, list):
                errors.append(f"candidates[{index}].content.parts必须是列表")
            else:
                for j, part in enumerate(parts):
                    part_errors = self._validate_part(part, index, j)
                    errors.extend(part_errors)
        
        # 验证role字段
        if "role" in content and content["role"] != "model":
            errors.append(f"candidates[{index}].content.role必须是'model'")
        
        return errors
    
    def _validate_part(self, part: Dict[str, Any], candidate_index: int, part_index: int) -> List[str]:
        """验证内容部分"""
        errors = []
        
        if not isinstance(part, dict):
            errors.append(f"candidates[{candidate_index}].content.parts[{part_index}]必须是字典")
            return errors
        
        # 检查至少有一个有效字段
        valid_fields = {"text", "inline_data", "functionCall", "functionResponse", "thought"}
        has_valid_field = any(field in part for field in valid_fields)
        
        if not has_valid_field:
            errors.append(f"candidates[{candidate_index}].content.parts[{part_index}]必须包含有效字段之一: {', '.join(valid_fields)}")
        
        return errors
    
    def _validate_usage_metadata(self, usage_metadata: Dict[str, Any]) -> List[str]:
        """验证使用统计"""
        errors = []
        
        if not isinstance(usage_metadata, dict):
            errors.append("usageMetadata字段必须是字典")
            return errors
        
        required_fields = ["promptTokenCount", "candidatesTokenCount", "totalTokenCount"]
        for field in required_fields:
            if field not in usage_metadata:
                errors.append(f"usageMetadata缺少{field}字段")
            elif not isinstance(usage_metadata[field], int) or usage_metadata[field] < 0:
                errors.append(f"usageMetadata的{field}字段必须是非负整数")
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应
        
        Args:
            error_response: 错误响应
            
        Returns:
            str: 用户友好的错误消息
        """
        error = error_response.get("error", {})
        error_code = error.get("code", "unknown")
        error_message = error.get("message", "未知错误")
        error_status = error.get("status", "UNKNOWN")
        
        # 根据错误代码提供友好的错误消息
        error_mappings = {
            400: "请求参数无效",
            401: "认证失败，请检查API密钥",
            403: "权限不足",
            404: "请求的资源不存在",
            429: "请求频率过高，请稍后重试",
            500: "服务器内部错误",
            503: "服务不可用，请稍后重试"
        }
        
        friendly_message = error_mappings.get(error_code, f"未知错误代码: {error_code}")
        return f"{friendly_message}: {error_message} (状态: {error_status})"