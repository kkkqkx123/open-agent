"""配置验证器"""

from typing import Any, Dict, List, Optional, Type, get_type_hints
from pydantic import ValidationError

from .validation_result import ValidationResult, ValidationIssue, ValidationSeverity
from .rules import ValidationRuleRegistry, create_default_rule_registry


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, rule_registry: Optional[ValidationRuleRegistry] = None):
        """
        初始化配置验证器
        
        Args:
            rule_registry: 验证规则注册表
        """
        self.rule_registry = rule_registry or create_default_rule_registry()
    
    def validate_config(self, config: Any, config_class: Optional[Type] = None, 
                     context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        验证配置对象
        
        Args:
            config: 配置对象
            config_class: 配置类（可选）
            context: 上下文信息
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        # 如果提供了配置类，验证类型
        if config_class is not None and not isinstance(config, config_class):
            result.add_error(
                field="config",
                message=f"配置类型不匹配，期望: {config_class.__name__}，实际: {type(config).__name__}",
                code="TYPE_MISMATCH"
            )
            return result
        
        # 获取配置的所有字段
        if hasattr(config, '__dataclass_fields__'):
            fields = config.__dataclass_fields__
            for field_name, field_info in fields.items():
                value = getattr(config, field_name, None)
                field_result = self.rule_registry.validate_field(config, field_name, value, context)
                # 总是合并结果，因为 field_result 总是返回 ValidationResult 对象
                result = result.merge(field_result)
        else:
            # 对于非dataclass对象，使用字典属性
            if hasattr(config, '__dict__'):
                for field_name, value in config.__dict__.items():
                    if not field_name.startswith('_'):
                        field_result = self.rule_registry.validate_field(config, field_name, value, context)
                        # 总是合并结果，因为 field_result 总是返回 ValidationResult 对象
                        result = result.merge(field_result)
        
        # 添加配置级别的验证
        self._validate_config_level(config, result, context)
        
        return result
    
    def _validate_config_level(self, config: Any, result: ValidationResult, 
                        context: Optional[Dict[str, Any]]) -> None:
        """配置级别的验证"""
        # 验证模型类型和名称的组合
        if hasattr(config, 'model_type') and hasattr(config, 'model_name'):
            model_type = getattr(config, 'model_type')
            model_name = getattr(config, 'model_name')
            
            # 验证模型类型和名称的兼容性
            incompatible_combinations = {
                ("openai", "claude-3-sonnet-20240229"): "OpenAI不支持Claude模型",
                ("anthropic", "gpt-4"): "Anthropic不支持GPT模型",
                ("gemini", "claude"): "Gemini不支持Claude模型",
                ("human_relay", "gpt-4"): "HumanRelay不支持GPT模型",
            }
            
            combination = (model_type, model_name)
            if combination in incompatible_combinations:
                result.add_error(
                    field="model_type",
                    message=incompatible_combinations[combination],
                    code="INCOMPATIBLE_MODEL"
                )
        
        # 验证API格式和提供商的兼容性
        if hasattr(config, 'api_format') and hasattr(config, 'model_type'):
            api_format = getattr(config, 'api_format')
            model_type = getattr(config, 'model_type')
            
            # 验证API格式和模型类型的兼容性
            incompatible_formats = {
                ("responses", "anthropic"): "Responses API不支持Anthropic模型",
                ("chat_completion", "human_relay"): "Chat Completion API不支持HumanRelay模型",
            }
            
            combination = (api_format, model_type)
            if combination in incompatible_formats:
                result.add_error(
                    field="api_format",
                    message=incompatible_formats[combination],
                    code="INCOMPATIBLE_FORMAT"
                )
        
        # 验证缓存配置的合理性
        if hasattr(config, 'cache_config'):
            cache_config = getattr(config, 'cache_config')
            if cache_config.get('enabled', False) and cache_config.get('max_size', 0) > 0:
                result.add_warning(
                    field="cache_config.max_size",
                    message="缓存已启用但最大大小为0，缓存将不会生效",
                    code="INEFFECTIVE_CACHE_SIZE"
                )
        
        # 验证降级配置的合理性
        if hasattr(config, 'fallback_enabled') and config.fallback_enabled:
            if not config.fallback_models:
                result.add_warning(
                    field="fallback_models",
                    message="降级已启用但没有配置降级模型",
                    code="NO_FALLBACK_MODELS"
                )
        
        # 验证重试配置的合理性
        if hasattr(config, 'max_retries') and config.max_retries > 10:
            result.add_info(
                field="max_retries",
                message="重试次数较多，可能影响性能",
                code="HIGH_RETRY_COUNT"
            )
        
        # 验证超时配置的合理性
        if hasattr(config, 'timeout') and config.timeout > 300:
            result.add_info(
                field="timeout",
                message="超时时间较长，可能影响用户体验",
                code="LONG_TIMEOUT"
            )
    
        # 验证温度参数的合理性
        if hasattr(config, 'temperature'):
            temp = config.temperature
            if temp < 0.0 or temp > 2.0:
                result.add_warning(
                    field="temperature",
                    message="温度参数超出推荐范围(0.0-2.0)",
                    code="TEMPERATURE_OUT_OF_RANGE"
                )
        
        # 验证token限制的合理性
        if hasattr(config, 'max_tokens'):
            max_tokens = config.max_tokens
            if max_tokens > 100000:
                result.add_info(
                    field="max_tokens",
                    message="最大token数较大，可能影响成本",
                    code="HIGH_MAX_TOKENS"
                )
        
        # 验证频率惩罚参数的合理性
        if hasattr(config, 'frequency_penalty'):
            freq_pen = config.frequency_penalty
            if freq_pen < -2.0 or freq_pen > 2.0:
                result.add_warning(
                    field="frequency_penalty",
                    message="频率惩罚参数超出推荐范围(-2.0-2.0)",
                    code="FREQUENCY_PENALTY_OUT_OF_RANGE"
                )
        
        # 验证存在性惩罚参数的合理性
        if hasattr(config, 'presence_penalty'):
            pres_pen = config.presence_penalty
            if pres_pen < -2.0 or pres_pen > 2.0:
                result.add_warning(
                    field="presence_penalty",
                    message="存在性惩罚参数超出推荐范围(-2.0-2.0)",
                    code="PRESENCE_PENALTY_OUT_OF_RANGE"
                )
    
        # 验证工具调用配置的完整性
        if hasattr(config, 'tools') and config.tools:
            if not config.tools:
                result.add_info(
                    field="tools",
                    message="启用了工具调用但没有配置工具列表",
                    code="EMPTY_TOOLS_LIST"
                )
        
        if hasattr(config, 'tool_choice') and config.tool_choice and not config.tools:
            result.add_warning(
                field="tool_choice",
                message="配置了工具选择但没有配置工具列表",
                code="TOOL_CHOICE_WITHOUT_TOOLS"
            )
    
    def validate_llm_client_config(self, config: Any, 
                                context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        验证LLM客户端配置
        
        Args:
            config: LLM客户端配置
            context: 上下文信息
            
        Returns:
            ValidationResult: 验证结果
        """
        result = self.validate_config(config, type(config), context)
        
        # LLM客户端特定验证
        self._validate_llm_client_specific(config, result, context)
        
        return result
    
    def _validate_llm_client_specific(self, config: Any, result: ValidationResult, 
                                context: Optional[Dict[str, Any]]) -> None:
        """LLM客户端特定验证"""
        # 根据模型类型进行特定验证
        model_type = getattr(config, 'model_type', 'unknown')
        
        if model_type == "openai":
            self._validate_openai_config(config, result, context)
        elif model_type == "anthropic":
            self._validate_anthropic_config(config, result, context)
        elif model_type == "gemini":
            self._validate_gemini_config(config, result, context)
        elif model_type == "human_relay":
            self._validate_human_relay_config(config, result, context)
        elif model_type == "mock":
            self._validate_mock_config(config, result, context)
    
    def _validate_openai_config(self, config: Any, result: ValidationResult, 
                         context: Optional[Dict[str, Any]]) -> None:
        """OpenAI配置特定验证"""
        # 验证OpenAI特定参数
        openai_params = [
            'top_logprobs', 'service_tier', 'safety_identifier', 
            'web_search_options', 'seed', 'stream_options'
        ]
        
        for param in openai_params:
            if hasattr(config, param):
                value = getattr(config, param)
                if value is not None:
                    continue
                
                # 验证参数类型
                if param == 'top_logprobs' and not isinstance(value, int):
                    result.add_warning(
                        field=param,
                        message="top_logprobs必须是整数",
                        code="INVALID_TYPE"
                    )
                elif param == 'service_tier' and not isinstance(value, str):
                    result.add_warning(
                        field=param,
                        message="service_tier必须是字符串",
                        code="INVALID_TYPE"
                    )
                elif param == 'seed' and not isinstance(value, int):
                    result.add_warning(
                        field=param,
                        message="seed必须是整数",
                        code="INVALID_TYPE"
                    )
                elif param == 'web_search_options' and not isinstance(value, (dict, list)):
                    result.add_warning(
                        field=param,
                        message="web_search_options必须是字典或列表",
                        code="INVALID_TYPE"
                    )
    
    def _validate_anthropic_config(self, config: Any, result: ValidationResult, 
                             context: Optional[Dict[str, Any]]) -> None:
        """Anthropic配置特定验证"""
        # 验证Anthropic特定参数
        anthropic_params = [
            'top_k', 'thinking_config', 'response_format', 'metadata'
        ]
        
        for param in anthropic_params:
            if hasattr(config, param):
                value = getattr(config, param)
                if value is not None:
                    continue
                
                # 验证参数类型
                if param == 'top_k' and not isinstance(value, int):
                    result.add_warning(
                        field=param,
                        message="top_k必须是整数",
                        code="INVALID_TYPE"
                    )
                elif param == 'thinking_config' and not isinstance(value, (dict, str)):
                    result.add_warning(
                        field=param,
                        message="thinking_config必须是字典或字符串",
                        code="INVALID_TYPE"
                    )
                elif param == 'response_format' and not isinstance(value, (dict, str)):
                    result.add_warning(
                        field=param,
                        message="response_format必须是字典或字符串",
                        code="INVALID_TYPE"
                    )
    
    def _validate_gemini_config(self, config: Any, result: ValidationResult, 
                           context: Optional[Dict[str, Any]]) -> None:
        """Gemini配置特定验证"""
        # 验证Gemini特定参数
        gemini_params = [
            'top_k', 'candidate_count', 'system_instruction', 'response_mime_type', 
            'safety_settings', 'content_cache_enabled'
        ]
        
        for param in gemini_params:
            if hasattr(config, param):
                value = getattr(config, param)
                if value is not None:
                    continue
                
                # 验证参数类型
                if param == 'top_k' and not isinstance(value, int):
                    result.add_warning(
                        field=param,
                        message="top_k必须是整数",
                        code="INVALID_TYPE"
                    )
                elif param == 'candidate_count' and not isinstance(value, int):
                    result.add_warning(
                        field=param,
                        message="candidate_count必须是整数",
                        code="INVALID_TYPE"
                    )
                elif param == 'system_instruction' and not isinstance(value, (dict, str)):
                    result.add_warning(
                        field=param,
                        message="system_instruction必须是字典或字符串",
                        code="INVALID_TYPE"
                    )
                elif param == 'response_mime_type' and not isinstance(value, str):
                    result.add_warning(
                        field=param,
                        message="response_mime_type必须是字符串",
                        code="INVALID_TYPE"
                    )
                elif param == 'safety_settings' and not isinstance(value, (dict, list)):
                    result.add_warning(
                        field=param,
                        message="safety_settings必须是字典或列表",
                        code="INVALID_TYPE"
                    )
    
    def _validate_human_relay_config(self, config: Any, result: ValidationResult, 
                                context: Optional[Dict[str, Any]]) -> None:
        """HumanRelay配置特定验证"""
        # 验证HumanRelay特定参数
        human_relay_params = [
            'mode', 'frontend_timeout', 'max_history_length'
        ]
        
        for param in human_relay_params:
            if hasattr(config, param):
                value = getattr(config, param)
                if value is not None:
                    continue
                
                # 验证参数类型
                if param == 'mode' and value not in ['single', 'multi']:
                    result.add_error(
                        field=param,
                        message="mode必须是'single'或'multi'",
                        code="INVALID_MODE"
                    )
                elif param == 'frontend_timeout' and not isinstance(value, int):
                    result.add_warning(
                        field=param,
                        message="frontend_timeout必须是整数",
                        code="INVALID_TYPE"
                    )
                elif param == 'max_history_length' and not isinstance(value, int):
                    result.add_warning(
                        field=param,
                        message="max_history_length必须是整数",
                        code="INVALID_TYPE"
                    )
    
    def _validate_mock_config(self, config: Any, result: ValidationResult, 
                        context: Optional[Dict[str, Any]]) -> None:
        """Mock配置特定验证"""
        # Mock配置相对宽松，主要验证基本参数
        mock_params = [
            'response_delay', 'error_rate', 'error_types'
        ]
        
        for param in mock_params:
            if hasattr(config, param):
                value = getattr(config, param)
                if value is not None:
                    continue
                
                # 验证参数类型
                if param == 'response_delay' and not isinstance(value, (int, float)):
                    result.add_warning(
                        field=param,
                        message="response_delay必须是数字",
                        code="INVALID_TYPE"
                    )
                elif param == 'error_rate' and not isinstance(value, (int, float)):
                    result.add_warning(
                        field=param,
                        message="error_rate必须是数字",
                        code="INVALID_TYPE"
                    )
                elif param == 'error_types' and not isinstance(value, list):
                    result.add_warning(
                        field=param,
                        message="error_types必须是列表",
                        code="INVALID_TYPE"
                    )
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """
        获取验证摘要
        
        Args:
            result: 验证结果
            
        Returns:
            str: 验证摘要
        """
        if result.is_valid:
            return "配置验证通过"
        
        error_count = len(result.get_errors())
        warning_count = len(result.get_warnings())
        
        if error_count > 0:
            return f"配置验证失败，发现 {error_count} 个错误和 {warning_count} 个警告"
        elif warning_count > 0:
            return f"配置验证通过，但有 {warning_count} 个警告"
        else:
            return "配置验证通过"
    
    def fix_config_issues(self, config: Any, result: ValidationResult) -> Dict[str, Any]:
        """
        尝试修复配置问题
        
        Args:
            config: 配置对象
            result: 验证结果
            
        Returns:
            Dict[str, Any]: 修复后的配置字典
        """
        fixed_config = {}
        
        if hasattr(config, '__dict__'):
            fixed_config = config.__dict__.copy()
        
        # 修复错误
        for issue in result.get_errors():
            if hasattr(config, issue.field):
                current_value = getattr(config, issue.field)
                suggested_value = self._get_suggested_value(issue)
                if suggested_value is not None:
                    fixed_config[issue.field] = suggested_value
        
        # 修复警告
        for issue in result.get_warnings():
            if hasattr(config, issue.field):
                current_value = getattr(config, issue.field)
                suggested_value = self._get_suggested_value(issue)
                if suggested_value is not None:
                    fixed_config[issue.field] = suggested_value
        
        return fixed_config
    
    def _get_suggested_value(self, issue: ValidationIssue) -> Any:
        """获取建议的修复值"""
        field = issue.field
        code = issue.code
        
        # 根据错误代码提供修复建议
        if code == "REQUIRED_FIELD":
            return "default_value"
        elif code == "TYPE_MISMATCH":
            if "model_name" in field.lower():
                return "gpt-4"
            elif "model_type" in field.lower():
                return "openai"
            elif "temperature" in field.lower():
                return 0.7
            elif "timeout" in field.lower():
                return 30
            elif "max_tokens" in field.lower():
                return 2000
        elif "api_key" in field.lower():
            return "your-api-key-here"
        elif "base_url" in field.lower():
            return "https://api.example.com"
        elif "max_retries" in field.lower():
            return 3
        elif "frequency_penalty" in field.lower():
            return 0.0
        elif "presence_penalty" in field.lower():
                0.0
        elif "top_p" in field.lower():
                1.0
        elif "top_k" in field.lower():
                return 40
        elif "candidate_count" in field.lower():
                return 1
        elif "max_output_tokens" in field.lower():
                2048
        elif "stop_sequences" in field.lower():
                return None
        elif "tool_choice" in field.lower():
                return "auto"
        elif "tools" in field.lower():
            return []
        elif "system" in field.lower():
            return "You are a helpful assistant."
        elif "user" in field.lower():
            return "user-identifier"
        
        return None