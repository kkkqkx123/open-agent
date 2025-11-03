"""验证模块集成测试"""

import pytest
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from src.infrastructure.llm.validation.config_validator import ConfigValidator
from src.infrastructure.llm.validation.rules import (
    ValidationRuleRegistry,
    create_default_rule_registry,
    RequiredFieldRule,
    TypeValidationRule,
    ModelNameValidationRule
)
from src.infrastructure.llm.validation.validation_result import ValidationResult, ValidationSeverity


@dataclass
class LLMConfig:
    """LLM配置类"""
    model_type: str = "openai"
    model_name: str = "gpt-4"
    api_format: str = "chat_completion"
    api_key: str = "sk-test123"
    base_url: str = "https://api.openai.com"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    max_retries: int = 3
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    top_p: float = 1.0
    fallback_enabled: bool = False
    fallback_models: Optional[List[str]] = None
    cache_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = []
        if self.cache_config is None:
            self.cache_config = {"enabled": False, "max_size": 0}
        if self.tools is None:
            self.tools = []


@dataclass
class OpenAIConfig(LLMConfig):
    """OpenAI特定配置"""
    model_type: str = "openai"
    top_logprobs: Optional[int] = None
    seed: Optional[int] = None
    stream_options: Optional[Dict[str, Any]] = None


@dataclass
class AnthropicConfig(LLMConfig):
    """Anthropic特定配置"""
    model_type: str = "anthropic"
    model_name: str = "claude-3-sonnet-20240229"
    top_k: Optional[int] = None
    thinking_config: Optional[str] = None


@dataclass
class GeminiConfig(LLMConfig):
    """Gemini特定配置"""
    model_type: str = "gemini"
    model_name: str = "gemini-pro"
    top_k: Optional[int] = None
    candidate_count: Optional[int] = None
    system_instruction: Optional[str] = None


class TestValidationIntegration:
    """验证模块集成测试"""
    
    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return ConfigValidator()
    
    @pytest.fixture
    def custom_registry(self):
        """创建自定义规则注册表"""
        registry = ValidationRuleRegistry()
        
        # 添加自定义规则
        registry.register_rule(RequiredFieldRule("model_name"))
        registry.register_rule(TypeValidationRule("model_type", str))
        registry.register_rule(ModelNameValidationRule())
        
        return registry
    
    @pytest.fixture
    def custom_validator(self, custom_registry):
        """创建使用自定义注册表的验证器"""
        return ConfigValidator(custom_registry)
    
    def test_complete_config_validation(self, validator):
        """测试完整配置验证"""
        config = LLMConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="sk-test123",
            base_url="https://api.openai.com",
            temperature=0.7,
            max_tokens=2000,
            timeout=30,
            max_retries=3
        )
        
        result = validator.validate_config(config)
        
        assert result.is_valid == True
        assert len(result.get_errors()) == 0
    
    def test_openai_config_validation(self, validator):
        """测试OpenAI配置验证"""
        config = OpenAIConfig(
            model_name="gpt-4",
            api_key="sk-test123",
            top_logprobs=5,
            seed=42
        )
        
        result = validator.validate_llm_client_config(config)
        
        assert result.is_valid == True
        assert len(result.get_errors()) == 0
    
    def test_anthropic_config_validation(self, validator):
        """测试Anthropic配置验证"""
        config = AnthropicConfig(
            model_name="claude-3-sonnet-20240229",
            api_key="sk-ant-test123",
            top_k=40
        )
        
        result = validator.validate_llm_client_config(config)
        
        assert result.is_valid == True
        assert len(result.get_errors()) == 0
    
    def test_gemini_config_validation(self, validator):
        """测试Gemini配置验证"""
        config = GeminiConfig(
            model_name="gemini-pro",
            api_key="AIza-test123",
            top_k=40,
            candidate_count=1
        )
        
        result = validator.validate_llm_client_config(config)
        
        assert result.is_valid == True
        assert len(result.get_errors()) == 0
    
    def test_incompatible_model_combination(self, validator):
        """测试不兼容的模型组合"""
        config = LLMConfig(
            model_type="openai",
            model_name="claude-3-sonnet-20240229",  # OpenAI不支持Claude
            api_key="sk-test123"
        )
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        errors = result.get_errors()
        assert any("INCOMPATIBLE_MODEL" in error.code for error in errors)
    
    def test_incompatible_api_format(self, validator):
        """测试不兼容的API格式"""
        config = LLMConfig(
            model_type="anthropic",
            api_format="responses",  # Responses API不支持Anthropic
            api_key="sk-ant-test123"
        )
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        errors = result.get_errors()
        assert any("INCOMPATIBLE_FORMAT" in error.code for error in errors)
    
    def test_fallback_configuration_validation(self, validator):
        """测试降级配置验证"""
        # 启用降级但没有配置降级模型
        config = LLMConfig(
            fallback_enabled=True,
            fallback_models=[]
        )
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        warnings = result.get_warnings()
        assert any("NO_FALLBACK_MODELS" in warning.code for warning in warnings)
        
        # 修复配置
        config.fallback_models = ["gpt-3.5-turbo", "claude-3-haiku-20240307"]
        result = validator.validate_config(config)
        
        # 应该没有关于降级模型的警告
        warnings = result.get_warnings()
        assert not any("NO_FALLBACK_MODELS" in warning.code for warning in warnings)
    
    def test_cache_configuration_validation(self, validator):
        """测试缓存配置验证"""
        # 启用缓存但最大大小为0
        config = LLMConfig(
            cache_config={"enabled": True, "max_size": 0}
        )
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        warnings = result.get_warnings()
        assert any("INEFFECTIVE_CACHE_SIZE" in warning.code for warning in warnings)
        
        # 修复配置
        if config.cache_config is not None:
            config.cache_config["max_size"] = 100
        result = validator.validate_config(config)
        
        # 应该没有关于缓存大小的警告
        warnings = result.get_warnings()
        assert not any("INEFFECTIVE_CACHE_SIZE" in warning.code for warning in warnings)
    
    def test_parameter_range_validation(self, validator):
        """测试参数范围验证"""
        config = LLMConfig(
            temperature=2.5,  # 超出范围
            max_tokens=150000,  # 较大值
            frequency_penalty=3.0,  # 超出范围
            timeout=400,  # 较长超时
            max_retries=15  # 较多重试
        )
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        
        warnings = result.get_warnings()
        infos = result.get_infos()
        
        # 应该有参数范围警告
        assert any("TEMPERATURE_OUT_OF_RANGE" in warning.code for warning in warnings)
        assert any("FREQUENCY_PENALTY_OUT_OF_RANGE" in warning.code for warning in warnings)
        
        # 应该有信息性提示
        assert any("HIGH_MAX_TOKENS" in info.code for info in infos)
        assert any("LONG_TIMEOUT" in info.code for info in infos)
        assert any("HIGH_RETRY_COUNT" in info.code for info in infos)
    
    def test_tools_configuration_validation(self, validator):
        """测试工具配置验证"""
        # 配置工具选择但没有工具列表
        config = LLMConfig(
            tool_choice="auto",
            tools=[]
        )
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        warnings = result.get_warnings()
        assert any("TOOL_CHOICE_WITHOUT_TOOLS" in warning.code for warning in warnings)
        
        # 修复配置
        config.tools = [{"type": "function", "function": {"name": "test_tool"}}]
        result = validator.validate_config(config)
        
        # 应该没有关于工具选择的警告
        warnings = result.get_warnings()
        assert not any("TOOL_CHOICE_WITHOUT_TOOLS" in warning.code for warning in warnings)
    
    def test_custom_registry_validation(self, custom_validator):
        """测试自定义注册表验证"""
        config = LLMConfig(
            model_type="openai",
            model_name="gpt-4"
        )
        
        result = custom_validator.validate_config(config)
        
        assert result.is_valid == True
        assert len(result.get_errors()) == 0
    
    def test_custom_registry_validation_failure(self, custom_validator):
        """测试自定义注册表验证失败"""
        config = LLMConfig(
            model_type=123,  # type: ignore # 错误类型
            model_name=""  # 空值
        )
        
        result = custom_validator.validate_config(config)
        
        assert result.is_valid == False
        errors = result.get_errors()
        assert len(errors) >= 2  # 至少有类型错误和必填字段错误
    
    def test_validation_result_merge(self):
        """测试验证结果合并"""
        result1 = ValidationResult(is_valid=True)
        result1.add_error("field1", "error1", "ERROR1")
        result1.add_warning("field2", "warning1", "WARNING1")
        result1.summary = "摘要1"
        
        result2 = ValidationResult(is_valid=True)
        result2.add_error("field3", "error2", "ERROR2")
        result2.add_info("field4", "info1", "INFO1")
        result2.summary = "摘要2"
        
        merged = result1.merge(result2)
        
        assert merged.is_valid == False
        assert len(merged.issues) == 4
        assert merged.summary == "摘要1; 摘要2"
        
        # 验证所有问题都被包含
        error_codes = [issue.code for issue in merged.get_errors()]
        warning_codes = [issue.code for issue in merged.get_warnings()]
        info_codes = [issue.code for issue in merged.get_infos()]
        
        assert "ERROR1" in error_codes
        assert "ERROR2" in error_codes
        assert "WARNING1" in warning_codes
        assert "INFO1" in info_codes
    
    def test_validation_with_context(self, validator):
        """测试带上下文的验证"""
        config = LLMConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="${OPENAI_API_KEY}"  # 环境变量引用
        )
        
        context = {"environment": "production"}
        result = validator.validate_config(config, context=context)
        
        # 环境变量引用应该被接受
        assert len([e for e in result.get_errors() if "MISSING_API_KEY" in e.code]) == 0
    
    def test_non_dataclass_validation(self, validator):
        """测试非dataclass对象验证"""
        config_dict = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test123",
            "temperature": 0.7
        }
        
        result = validator.validate_config(config_dict)
        
        assert isinstance(result, ValidationResult)
        # 字典对象应该能够被验证，但可能缺少某些字段级验证
    
    def test_validation_fix_suggestions(self, validator):
        """测试验证修复建议"""
        config = LLMConfig(
            model_name="",  # 空值
            temperature=2.5,  # 超出范围
            api_key=None  # type: ignore # 缺失
        )
        
        result = validator.validate_config(config)
        fixed_config = validator.fix_config_issues(config, result)
        
        # 验证修复建议
        assert "model_name" in fixed_config
        assert "temperature" in fixed_config
        assert "api_key" in fixed_config
        
        # 验证建议值
        assert fixed_config["model_name"] == "gpt-4"
        assert fixed_config["temperature"] == 0.7
        assert fixed_config["api_key"] == "your-api-key-here"
    
    def test_default_rule_registry_completeness(self):
        """测试默认规则注册表的完整性"""
        registry = create_default_rule_registry()
        all_rules = registry.get_all_rules()
        
        # 验证关键规则存在
        required_rules = [
            "required_field_model_name",
            "type_validation_model_type",
            "model_name_validation",
            "api_key_validation",
            "url_validation",
            "timeout_validation"
        ]
        
        for rule_name in required_rules:
            assert rule_name in all_rules, f"缺少规则: {rule_name}"
    
    def test_validation_summary_generation(self, validator):
        """测试验证摘要生成"""
        # 有效配置
        valid_config = LLMConfig()
        valid_result = validator.validate_config(valid_config)
        valid_summary = validator.get_validation_summary(valid_result)
        assert "配置验证通过" in valid_summary
        
        # 有错误的配置
        invalid_config = LLMConfig(model_name="")
        invalid_result = validator.validate_config(invalid_config)
        invalid_summary = validator.get_validation_summary(invalid_result)
        assert "配置验证失败" in invalid_summary
        
        # 有警告的配置
        warning_config = LLMConfig(temperature=2.5)
        warning_result = validator.validate_config(warning_config)
        warning_summary = validator.get_validation_summary(warning_result)
        assert "配置验证通过" in warning_summary and "警告" in warning_summary
    
    def test_validation_performance(self, validator):
        """测试验证性能"""
        import time
        
        config = LLMConfig()
        
        # 测试多次验证的性能
        start_time = time.time()
        for _ in range(100):
            result = validator.validate_config(config)
        end_time = time.time()
        
        # 100次验证应该在合理时间内完成（小于1秒）
        elapsed = end_time - start_time
        assert elapsed < 1.0, f"验证性能过慢: {elapsed:.3f}秒"