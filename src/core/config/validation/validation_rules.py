"""具体验证规则实现

包含各种配置类型的验证规则。
"""

from typing import Dict, Any
import re

from src.interfaces.config.validation import IValidationRule, IValidationContext
from src.infrastructure.validation.result import ValidationResult


class BaseValidationRule(IValidationRule):
    """验证规则基类"""
    
    def __init__(self, rule_id: str, config_type: str, priority: int = 100):
        """初始化验证规则
        
        Args:
            rule_id: 规则ID
            config_type: 配置类型
            priority: 优先级
        """
        self._rule_id = rule_id
        self._config_type = config_type
        self._priority = priority
    
    @property
    def rule_id(self) -> str:
        return self._rule_id
    
    @property
    def config_type(self) -> str:
        return self._config_type
    
    @property
    def priority(self) -> int:
        return self._priority
    
    def validate(self, config: Dict[str, Any], context: IValidationContext) -> ValidationResult:
        """执行验证"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        self._validate_impl(config, context, result)
        return result
    
    def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                       result: ValidationResult) -> None:
        """具体验证逻辑，子类实现"""
        pass


class GlobalConfigValidationRules:
    """全局配置验证规则集合"""
    
    class LogOutputRule(BaseValidationRule):
        """日志输出验证规则"""
        
        def __init__(self):
            super().__init__("global_log_output", "global", 10)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证日志输出配置"""
            log_outputs = config.get("log_outputs", [])
            if not log_outputs:
                result.add_warning("未配置日志输出，日志可能不会被记录")
                return
            
            for output in log_outputs:
                if not isinstance(output, dict):
                    result.add_error("日志输出配置必须是字典类型")
                    continue
                
                output_type = output.get("type")
                if not output_type:
                    result.add_error("日志输出配置缺少type字段")
                    continue
                
                if output_type == "file" and not output.get("path"):
                    result.add_warning("文件日志输出未配置路径，可能无法写入日志")
    
    class SecretPatternRule(BaseValidationRule):
        """敏感信息模式验证规则"""
        
        def __init__(self):
            super().__init__("global_secret_pattern", "global", 20)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证敏感信息模式配置"""
            secret_patterns = config.get("secret_patterns", [])
            if not secret_patterns:
                result.add_warning("未配置敏感信息模式，日志可能泄露敏感信息")
    
    class ProductionDebugRule(BaseValidationRule):
        """生产环境调试模式验证规则"""
        
        def __init__(self):
            super().__init__("global_production_debug", "global", 30)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证生产环境调试模式"""
            if config.get("env") == "production" and config.get("debug"):
                result.add_warning("生产环境不建议启用调试模式")


class LLMConfigValidationRules:
    """LLM配置验证规则集合"""
    
    class APIKeyRule(BaseValidationRule):
        """API密钥验证规则"""
        
        def __init__(self):
            super().__init__("llm_api_key", "llm", 10)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证API密钥配置"""
            model_type = config.get("model_type")
            if model_type in ["openai", "gemini", "anthropic"] and not config.get("api_key"):
                result.add_warning("未配置API密钥，可能需要在运行时通过环境变量提供")
    
    class BaseURLRule(BaseValidationRule):
        """基础URL验证规则"""
        
        def __init__(self):
            super().__init__("llm_base_url", "llm", 20)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证基础URL配置"""
            if not config.get("base_url") and config.get("model_type") not in ["openai"]:
                result.add_warning("未配置基础URL，可能使用默认值")
    
    class RetryConfigRule(BaseValidationRule):
        """重试配置验证规则"""
        
        def __init__(self):
            super().__init__("llm_retry_config", "llm", 30)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证重试配置"""
            retry_config = config.get("retry_config", {})
            if not isinstance(retry_config, dict):
                result.add_error("retry_config必须是字典类型")
                return
            
            # 验证max_retries
            max_retries = retry_config.get("max_retries")
            if max_retries is not None and (not isinstance(max_retries, int) or max_retries < 0):
                result.add_error(f"retry_config.max_retries必须是非负整数，当前值: {max_retries}")
            
            # 验证base_delay
            base_delay = retry_config.get("base_delay")
            if base_delay is not None and (not isinstance(base_delay, (int, float)) or base_delay <= 0):
                result.add_error(f"retry_config.base_delay必须是正数，当前值: {base_delay}")
            
            # 验证max_delay
            max_delay = retry_config.get("max_delay")
            if max_delay is not None and (not isinstance(max_delay, (int, float)) or max_delay <= 0):
                result.add_error(f"retry_config.max_delay必须是正数，当前值: {max_delay}")
            
            # 验证exponential_base
            exponential_base = retry_config.get("exponential_base")
            if exponential_base is not None and (not isinstance(exponential_base, (int, float)) or exponential_base <= 1):
                result.add_error(f"retry_config.exponential_base必须大于1，当前值: {exponential_base}")
    
    class TimeoutConfigRule(BaseValidationRule):
        """超时配置验证规则"""
        
        def __init__(self):
            super().__init__("llm_timeout_config", "llm", 40)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证超时配置"""
            timeout_config = config.get("timeout_config", {})
            if not isinstance(timeout_config, dict):
                result.add_error("timeout_config必须是字典类型")
                return
            
            timeout_fields = {
                "request_timeout": "正整数",
                "connect_timeout": "正整数",
                "read_timeout": "正整数",
                "write_timeout": "正整数"
            }
            
            for field, expected_type in timeout_fields.items():
                value = timeout_config.get(field)
                if value is not None and (not isinstance(value, int) or value <= 0):
                    result.add_error(f"timeout_config.{field}必须是{expected_type}，当前值: {value}")


class ToolConfigValidationRules:
    """工具配置验证规则集合"""
    
    class ToolsExistRule(BaseValidationRule):
        """工具存在性验证规则"""
        
        def __init__(self):
            super().__init__("tool_tools_exist", "tool", 10)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证工具配置"""
            if not config.get("tools"):
                result.add_warning("未配置任何工具，工具集可能为空")


class TokenCounterConfigValidationRules:
    """Token计数器配置验证规则集合"""
    
    class EnhancedModeRule(BaseValidationRule):
        """增强模式验证规则"""
        
        def __init__(self):
            super().__init__("token_counter_enhanced_mode", "token_counter", 10)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证增强模式配置"""
            if config.get("enhanced", False):
                if not config.get("cache"):
                    result.add_warning("增强模式建议配置缓存以提高性能")
                
                if not config.get("calibration"):
                    result.add_warning("增强模式建议配置校准以提高准确性")
    
    class ModelNameRule(BaseValidationRule):
        """模型名称验证规则"""
        
        def __init__(self):
            super().__init__("token_counter_model_name", "token_counter", 20)
        
        def _validate_impl(self, config: Dict[str, Any], context: IValidationContext, 
                          result: ValidationResult) -> None:
            """验证模型名称匹配性"""
            model_type = config.get("model_type")
            model_name = config.get("model_name")
            
            if not model_type or not model_name:
                return
            
            model_name_lower = model_name.lower()
            
            if model_type == "openai" and not model_name.startswith(("gpt-", "text-", "code-")):
                result.add_warning(f"OpenAI模型名称 {model_name} 可能不符合命名规范")
            elif model_type == "anthropic" and "claude" not in model_name_lower:
                result.add_warning(f"Anthropic模型名称 {model_name} 可能不符合命名规范")
            elif model_type == "gemini" and "gemini" not in model_name_lower:
                result.add_warning(f"Gemini模型名称 {model_name} 可能不符合命名规范")