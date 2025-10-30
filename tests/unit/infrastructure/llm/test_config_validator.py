"""配置验证器单元测试"""

import pytest
from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.infrastructure.llm.validation.config_validator import ConfigValidator
from src.infrastructure.llm.validation.validation_result import ValidationResult, ValidationSeverity
from src.infrastructure.llm.validation.rules import ValidationRuleRegistry, create_default_rule_registry


@dataclass
class MockConfig:
    """模拟配置类"""
    model_type: str = "openai"
    model_name: str = "gpt-4"
    api_format: str = "chat_completion"
    api_key: str = "sk-test"
    base_url: str = "https://api.openai.com"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    max_retries: int = 3
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    top_p: float = 1.0
    fallback_enabled: bool = False
    fallback_models: Optional[list] = None
    cache_config: Optional[Dict[str, Any]] = None
    tools: Optional[list] = None
    tool_choice: Optional[str] = None
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = []
        if self.cache_config is None:
            self.cache_config = {"enabled": False, "max_size": 0}
        if self.tools is None:
            self.tools = []


class TestConfigValidator:
    """配置验证器测试"""
    
    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return ConfigValidator()
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MockConfig()
    
    def test_validate_config_success(self, validator, config):
        """测试成功验证配置"""
        result = validator.validate_config(config)
        
        assert result.is_valid == True
        assert len(result.get_errors()) == 0
    
    def test_validate_config_type_mismatch(self, validator, config):
        """测试类型不匹配"""
        result = validator.validate_config(config, str)
        
        assert result.is_valid == False
        errors = result.get_errors()
        assert len(errors) == 1
        assert "TYPE_MISMATCH" in errors[0].code
    
    def test_validate_config_with_rules(self, validator, config):
        """测试使用规则验证配置"""
        # 创建一个会失败的规则
        rule_registry = ValidationRuleRegistry()
        
        from src.infrastructure.llm.validation.rules import ValidationRule, ValidationIssue
        
        class FailingRule(ValidationRule):
            @property
            def name(self):
                return "failing_rule"
            
            @property
            def description(self):
                return "Always fails"
            
            @property
            def applicable_fields(self):
                return ["model_name"]
            
            def validate(self, config, field, value, context):
                return ValidationIssue(
                    field=field,
                    message="Test failure",
                    severity=ValidationSeverity.ERROR,
                    code="TEST_FAILURE"
                )
        
        rule_registry.register_rule(FailingRule())
        validator.rule_registry = rule_registry
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        errors = result.get_errors()
        assert len(errors) == 1
        assert errors[0].code == "TEST_FAILURE"
    
    def test_validate_config_level_incompatible_model(self, validator, config):
        """测试不兼容的模型类型和名称组合"""
        config.model_type = "openai"
        config.model_name = "claude-3-sonnet-20240229"
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        errors = result.get_errors()
        assert any("INCOMPATIBLE_MODEL" in error.code for error in errors)
    
    def test_validate_config_level_incompatible_format(self, validator, config):
        """测试不兼容的API格式和模型类型"""
        config.api_format = "responses"
        config.model_type = "anthropic"
        
        result = validator.validate_config(config)
        
        assert result.is_valid == False
        errors = result.get_errors()
        assert any("INCOMPATIBLE_FORMAT" in error.code for error in errors)
    
    def test_validate_config_level_ineffective_cache(self, validator, config):
        """测试无效的缓存配置"""
        config.cache_config = {"enabled": True, "max_size": 0}
        
        result = validator.validate_config(config)
        
        warnings = result.get_warnings()
        assert any("INEFFECTIVE_CACHE_SIZE" in warning.code for warning in warnings)
    
    def test_validate_config_level_no_fallback_models(self, validator, config):
        """测试没有降级模型的降级配置"""
        config.fallback_enabled = True
        config.fallback_models = []
        
        result = validator.validate_config(config)
        
        warnings = result.get_warnings()
        assert any("NO_FALLBACK_MODELS" in warning.code for warning in warnings)
    
    def test_validate_config_level_high_retry_count(self, validator, config):
        """测试高重试次数"""
        config.max_retries = 15
        
        result = validator.validate_config(config)
        
        infos = result.get_infos()
        assert any("HIGH_RETRY_COUNT" in info.code for info in infos)
    
    def test_validate_config_level_long_timeout(self, validator, config):
        """测试长超时时间"""
        config.timeout = 400
        
        result = validator.validate_config(config)
        
        infos = result.get_infos()
        assert any("LONG_TIMEOUT" in info.code for info in infos)
    
    def test_validate_config_level_temperature_out_of_range(self, validator, config):
        """测试温度参数超出范围"""
        config.temperature = 2.5
        
        result = validator.validate_config(config)
        
        warnings = result.get_warnings()
        assert any("TEMPERATURE_OUT_OF_RANGE" in warning.code for warning in warnings)
    
    def test_validate_config_level_high_max_tokens(self, validator, config):
        """测试高最大token数"""
        config.max_tokens = 150000
        
        result = validator.validate_config(config)
        
        infos = result.get_infos()
        assert any("HIGH_MAX_TOKENS" in info.code for info in infos)
    
    def test_validate_config_level_frequency_penalty_out_of_range(self, validator, config):
        """测试频率惩罚参数超出范围"""
        config.frequency_penalty = 2.5
        
        result = validator.validate_config(config)
        
        warnings = result.get_warnings()
        assert any("FREQUENCY_PENALTY_OUT_OF_RANGE" in warning.code for warning in warnings)
    
    def test_validate_config_level_presence_penalty_out_of_range(self, validator, config):
        """测试存在性惩罚参数超出范围"""
        config.presence_penalty = -2.5
        
        result = validator.validate_config(config)
        
        warnings = result.get_warnings()
        assert any("PRESENCE_PENALTY_OUT_OF_RANGE" in warning.code for warning in warnings)
    
    def test_validate_config_level_tool_choice_without_tools(self, validator, config):
        """测试有工具选择但没有工具列表"""
        config.tool_choice = "auto"
        config.tools = []
        
        result = validator.validate_config(config)
        
        warnings = result.get_warnings()
        assert any("TOOL_CHOICE_WITHOUT_TOOLS" in warning.code for warning in warnings)
    
    def test_validate_llm_client_config_openai(self, validator, config):
        """测试OpenAI客户端配置验证"""
        config.model_type = "openai"
        
        result = validator.validate_llm_client_config(config)
        
        # 应该成功，没有OpenAI特定错误
        assert len([e for e in result.get_errors() if "INVALID_TYPE" in e.code]) == 0
    
    def test_validate_llm_client_config_anthropic(self, validator, config):
        """测试Anthropic客户端配置验证"""
        config.model_type = "anthropic"
        
        result = validator.validate_llm_client_config(config)
        
        # 应该成功，没有Anthropic特定错误
        assert len([e for e in result.get_errors() if "INVALID_TYPE" in e.code]) == 0
    
    def test_validate_llm_client_config_gemini(self, validator, config):
        """测试Gemini客户端配置验证"""
        config.model_type = "gemini"
        
        result = validator.validate_llm_client_config(config)
        
        # 应该成功，没有Gemini特定错误
        assert len([e for e in result.get_errors() if "INVALID_TYPE" in e.code]) == 0
    
    def test_validate_llm_client_config_human_relay(self, validator, config):
        """测试HumanRelay客户端配置验证"""
        config.model_type = "human_relay"
        
        result = validator.validate_llm_client_config(config)
        
        # 应该成功，没有HumanRelay特定错误
        assert len([e for e in result.get_errors() if "INVALID_MODE" in e.code]) == 0
    
    def test_validate_llm_client_config_mock(self, validator, config):
        """测试Mock客户端配置验证"""
        config.model_type = "mock"
        
        result = validator.validate_llm_client_config(config)
        
        # 应该成功，没有Mock特定错误
        assert len([e for e in result.get_errors() if "INVALID_TYPE" in e.code]) == 0
    
    def test_get_validation_summary_valid(self, validator, config):
        """测试获取有效配置的验证摘要"""
        result = validator.validate_config(config)
        summary = validator.get_validation_summary(result)
        
        assert summary == "配置验证通过"
    
    def test_get_validation_summary_with_errors(self, validator, config):
        """测试获取有错误配置的验证摘要"""
        config.model_type = "openai"
        config.model_name = "claude-3-sonnet-20240229"  # 不兼容组合
        
        result = validator.validate_config(config)
        summary = validator.get_validation_summary(result)
        
        assert "配置验证失败" in summary
        assert "1 个错误" in summary
    
    def test_get_validation_summary_with_warnings(self, validator, config):
        """测试获取有警告配置的验证摘要"""
        config.temperature = 2.5  # 超出范围
        
        result = validator.validate_config(config)
        summary = validator.get_validation_summary(result)
        
        assert "配置验证通过" in summary
        assert "个警告" in summary  # 可能是1个或多个警告
    
    def test_fix_config_issues(self, validator, config):
        """测试修复配置问题"""
        # 创建一些问题
        config.model_name = ""  # 空模型名称
        config.temperature = 2.5  # 超出范围
        
        result = validator.validate_config(config)
        fixed_config = validator.fix_config_issues(config, result)
        
        # 验证修复建议
        assert "model_name" in fixed_config
        assert "temperature" in fixed_config
    
    def test_get_suggested_value(self, validator):
        """测试获取建议的修复值"""
        from src.infrastructure.llm.validation.validation_result import ValidationIssue
        
        # 测试不同字段的建议值
        issue1 = ValidationIssue("model_name", "error", ValidationSeverity.ERROR, "REQUIRED_FIELD")
        issue2 = ValidationIssue("temperature", "error", ValidationSeverity.ERROR, "TYPE_MISMATCH")
        issue3 = ValidationIssue("api_key", "error", ValidationSeverity.ERROR, "REQUIRED_FIELD")
        
        value1 = validator._get_suggested_value(issue1)
        value2 = validator._get_suggested_value(issue2)
        value3 = validator._get_suggested_value(issue3)
        
        assert value1 == "gpt-4"
        assert value2 == 0.7
        assert value3 == "your-api-key-here"
    
    def test_validate_non_dataclass_config(self, validator):
        """测试验证非dataclass配置"""
        # 创建一个简单的字典对象
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "temperature": 0.7
        }
        
        result = validator.validate_config(config)
        
        # 应该能够验证字典对象
        assert isinstance(result, ValidationResult)
    
    def test_validate_config_with_context(self, validator, config):
        """测试带上下文的配置验证"""
        context = {"environment": "production"}
        
        result = validator.validate_config(config, context=context)
        
        # 应该能够处理上下文
        assert isinstance(result, ValidationResult)