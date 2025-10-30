"""验证规则单元测试"""

import pytest
from dataclasses import dataclass

from src.infrastructure.llm.validation.rules import (
    ValidationRuleRegistry,
    RequiredFieldRule,
    TypeValidationRule,
    RangeValidationRule,
    PatternValidationRule,
    EnumValidationRule,
    ModelNameValidationRule,
    APITokenValidationRule,
    URLValidationRule,
    TimeoutValidationRule,
    create_default_rule_registry
)
from src.infrastructure.llm.validation.validation_result import ValidationResult, ValidationSeverity


@dataclass
class MockConfig:
    """模拟配置类"""
    model_name: str = "gpt-4"
    model_type: str = "openai"
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 2000
    api_key: str = "sk-test123"
    base_url: str = "https://api.openai.com"
    timeout: int = 30
    max_retries: int = 3


class TestValidationRuleRegistry:
    """验证规则注册表测试"""
    
    @pytest.fixture
    def registry(self):
        """创建规则注册表"""
        return ValidationRuleRegistry()
    
    def test_register_rule(self, registry):
        """测试注册规则"""
        rule = RequiredFieldRule("test_field")
        
        registry.register_rule(rule)
        
        assert "required_field_test_field" in registry._rules
        assert registry._rules["required_field_test_field"] == rule
        assert "test_field" in registry._field_rules
        assert rule in registry._field_rules["test_field"]
    
    def test_get_rules_for_field(self, registry):
        """测试获取字段的规则"""
        rule1 = RequiredFieldRule("test_field")
        rule2 = TypeValidationRule("test_field", str)
        rule3 = RequiredFieldRule("other_field")
        
        registry.register_rule(rule1)
        registry.register_rule(rule2)
        registry.register_rule(rule3)
        
        rules = registry.get_rules_for_field("test_field")
        
        assert len(rules) == 2
        assert rule1 in rules
        assert rule2 in rules
        assert rule3 not in rules
    
    def test_get_rule(self, registry):
        """测试获取规则"""
        rule = RequiredFieldRule("test_field")
        registry.register_rule(rule)
        
        retrieved_rule = registry.get_rule("required_field_test_field")
        
        assert retrieved_rule == rule
        
        # 测试不存在的规则
        non_existent = registry.get_rule("non_existent_rule")
        assert non_existent is None
    
    def test_get_all_rules(self, registry):
        """测试获取所有规则"""
        rule1 = RequiredFieldRule("test_field")
        rule2 = TypeValidationRule("test_field", str)
        
        registry.register_rule(rule1)
        registry.register_rule(rule2)
        
        all_rules = registry.get_all_rules()
        
        assert len(all_rules) == 2
        assert "required_field_test_field" in all_rules
        assert "type_validation_test_field" in all_rules
    
    def test_validate_field(self, registry):
        """测试验证字段"""
        rule = RequiredFieldRule("model_name")
        registry.register_rule(rule)
        
        config = MockConfig(model_name="")
        result = registry.validate_field(config, "model_name", "")
        
        assert result.is_valid == False
        assert len(result.get_errors()) == 1
    
    def test_validate_config(self, registry):
        """测试验证配置"""
        rule = RequiredFieldRule("model_name")
        registry.register_rule(rule)
        
        config = MockConfig(model_name="")
        result = registry.validate_config(config)
        
        assert result.is_valid == False
        assert len(result.get_errors()) == 1


class TestRequiredFieldRule:
    """必填字段验证规则测试"""
    
    def test_validate_valid_value(self):
        """测试验证有效值"""
        rule = RequiredFieldRule("model_name")
        
        result = rule.validate(MockConfig(), "model_name", "gpt-4")
        
        assert result is None
    
    def test_validate_none_value(self):
        """测试验证None值"""
        rule = RequiredFieldRule("model_name")
        
        result = rule.validate(MockConfig(), "model_name", None)
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "REQUIRED_FIELD"
    
    def test_validate_empty_string(self):
        """测试验证空字符串"""
        rule = RequiredFieldRule("model_name")
        
        result = rule.validate(MockConfig(), "model_name", "")
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "REQUIRED_FIELD"
    
    def test_validate_whitespace_string(self):
        """测试验证空白字符串"""
        rule = RequiredFieldRule("model_name")
        
        result = rule.validate(MockConfig(), "model_name", "   ")
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "REQUIRED_FIELD"
    
    def test_rule_properties(self):
        """测试规则属性"""
        rule = RequiredFieldRule("test_field", "Custom message")
        
        assert rule.name == "required_field_test_field"
        assert rule.description == "Custom message"
        assert rule.applicable_fields == ["test_field"]


class TestTypeValidationRule:
    """类型验证规则测试"""
    
    def test_validate_correct_type(self):
        """测试验证正确类型"""
        rule = TypeValidationRule("model_type", str)
        
        result = rule.validate(MockConfig(), "model_type", "openai")
        
        assert result is None
    
    def test_validate_incorrect_type(self):
        """测试验证错误类型"""
        rule = TypeValidationRule("model_type", str)
        
        result = rule.validate(MockConfig(), "model_type", 123)
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code == "TYPE_MISMATCH"
        assert "str" in result.context["expected_type"]
        assert "int" in result.context["actual_type"]


class TestRangeValidationRule:
    """范围验证规则测试"""
    
    def test_validate_within_range(self):
        """测试验证在范围内"""
        rule = RangeValidationRule("temperature", 0.0, 2.0)
        
        result = rule.validate(MockConfig(), "temperature", 1.0)
        
        assert result is None
    
    def test_validate_below_min(self):
        """测试验证低于最小值"""
        rule = RangeValidationRule("temperature", 0.0, 2.0)
        
        result = rule.validate(MockConfig(), "temperature", -0.1)
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "VALUE_TOO_SMALL"
    
    def test_validate_above_max(self):
        """测试验证高于最大值"""
        rule = RangeValidationRule("temperature", 0.0, 2.0)
        
        result = rule.validate(MockConfig(), "temperature", 2.1)
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code == "VALUE_TOO_LARGE"
    
    def test_validate_none_min_max(self):
        """测试验证无最小最大值限制"""
        rule = RangeValidationRule("temperature", None, None)
        
        result = rule.validate(MockConfig(), "temperature", 5.0)
        
        assert result is None


class TestPatternValidationRule:
    """模式匹配验证规则测试"""
    
    def test_validate_matching_pattern(self):
        """测试验证匹配模式"""
        rule = PatternValidationRule("api_key", r"^sk-[a-zA-Z0-9]+$")
        
        result = rule.validate(MockConfig(), "api_key", "sk-test123")
        
        assert result is None
    
    def test_validate_non_matching_pattern(self):
        """测试验证不匹配模式"""
        rule = PatternValidationRule("api_key", r"^sk-[a-zA-Z0-9]+$")
        
        result = rule.validate(MockConfig(), "api_key", "invalid-key")
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code == "PATTERN_MISMATCH"
    
    def test_validate_non_string_value(self):
        """测试验证非字符串值"""
        rule = PatternValidationRule("api_key", r"^sk-[a-zA-Z0-9]+$")
        
        result = rule.validate(MockConfig(), "api_key", 123)
        
        assert result is None  # 非字符串值不进行模式验证


class TestEnumValidationRule:
    """枚举值验证规则测试"""
    
    def test_validate_valid_enum_value(self):
        """测试验证有效枚举值"""
        rule = EnumValidationRule("model_type", ["openai", "anthropic", "gemini"])
        
        result = rule.validate(MockConfig(), "model_type", "openai")
        
        assert result is None
    
    def test_validate_invalid_enum_value(self):
        """测试验证无效枚举值"""
        rule = EnumValidationRule("model_type", ["openai", "anthropic", "gemini"])
        
        result = rule.validate(MockConfig(), "model_type", "invalid")
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "INVALID_ENUM_VALUE"
        assert "openai" in str(result.context["valid_values"])


class TestModelNameValidationRule:
    """模型名称验证规则测试"""
    
    @pytest.fixture
    def rule(self):
        """创建规则实例"""
        return ModelNameValidationRule()
    
    def test_validate_supported_model(self, rule):
        """测试验证支持的模型"""
        result = rule.validate(MockConfig(), "model_name", "gpt-4")
        
        assert result is None
    
    def test_validate_unsupported_model(self, rule):
        """测试验证不支持的模型"""
        result = rule.validate(MockConfig(), "model_name", "unsupported-model")
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "UNSUPPORTED_MODEL"
        assert "gpt-4" in str(result.context["supported_models"])
    
    def test_rule_properties(self, rule):
        """测试规则属性"""
        assert rule.name == "model_name_validation"
        assert "模型名称" in rule.description
        assert rule.applicable_fields == ["model_name"]


class TestAPITokenValidationRule:
    """API密钥验证规则测试"""
    
    @pytest.fixture
    def rule(self):
        """创建规则实例"""
        return APITokenValidationRule()
    
    def test_validate_missing_api_key(self, rule):
        """测试验证缺失API密钥"""
        result = rule.validate(MockConfig(), "api_key", None)
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "MISSING_API_KEY"
    
    def test_validate_valid_api_key(self, rule):
        """测试验证有效API密钥"""
        result = rule.validate(MockConfig(), "api_key", "sk-test123")
        
        assert result is None
    
    def test_validate_invalid_api_key_format(self, rule):
        """测试验证无效API密钥格式"""
        result = rule.validate(MockConfig(), "api_key", "invalid-format")
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code == "INVALID_API_KEY_FORMAT"
    
    def test_validate_environment_variable_reference(self, rule):
        """测试验证环境变量引用"""
        result = rule.validate(MockConfig(), "api_key", "${OPENAI_API_KEY}")
        
        assert result is None  # 环境变量引用跳过验证
    
    def test_rule_properties(self, rule):
        """测试规则属性"""
        assert rule.name == "api_key_validation"
        assert "API密钥" in rule.description
        assert rule.applicable_fields == ["api_key"]


class TestURLValidationRule:
    """URL验证规则测试"""
    
    @pytest.fixture
    def rule(self):
        """创建规则实例"""
        return URLValidationRule()
    
    def test_validate_valid_https_url(self, rule):
        """测试验证有效HTTPS URL"""
        result = rule.validate(MockConfig(), "base_url", "https://api.openai.com")
        
        assert result is None
    
    def test_validate_valid_http_url(self, rule):
        """测试验证有效HTTP URL"""
        result = rule.validate(MockConfig(), "base_url", "http://api.example.com")
        
        assert result is None
    
    def test_validate_missing_url(self, rule):
        """测试验证缺失URL"""
        result = rule.validate(MockConfig(), "base_url", None)
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code == "MISSING_URL"
    
    def test_validate_invalid_protocol(self, rule):
        """测试验证无效协议"""
        result = rule.validate(MockConfig(), "base_url", "ftp://api.example.com")
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code == "INVALID_URL_FORMAT"
    
    def test_validate_malformed_url(self, rule):
        """测试验证格式错误的URL"""
        result = rule.validate(MockConfig(), "base_url", "not-a-url")
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code in ["INVALID_URL_FORMAT", "URL_PARSE_ERROR"]
    
    def test_rule_properties(self, rule):
        """测试规则属性"""
        assert rule.name == "url_validation"
        assert "URL" in rule.description
        assert rule.applicable_fields == ["base_url"]


class TestTimeoutValidationRule:
    """超时验证规则测试"""
    
    @pytest.fixture
    def rule(self):
        """创建规则实例"""
        return TimeoutValidationRule()
    
    def test_validate_valid_timeout(self, rule):
        """测试验证有效超时"""
        result = rule.validate(MockConfig(), "timeout", 30)
        
        assert result is None
    
    def test_validate_timeout_too_small(self, rule):
        """测试验证超时太小"""
        result = rule.validate(MockConfig(), "timeout", 0)
        
        assert result is not None
        assert result.severity == ValidationSeverity.ERROR
        assert result.code == "INVALID_TIMEOUT"
    
    def test_validate_timeout_too_large(self, rule):
        """测试验证超时太大"""
        result = rule.validate(MockConfig(), "timeout", 5000)
        
        assert result is not None
        assert result.severity == ValidationSeverity.WARNING
        assert result.code == "INVALID_TIMEOUT"
    
    def test_validate_none_timeout(self, rule):
        """测试验证None超时"""
        result = rule.validate(MockConfig(), "timeout", None)
        
        assert result is None
    
    def test_rule_properties(self, rule):
        """测试规则属性"""
        assert rule.name == "timeout_validation"
        assert "超时" in rule.description
        assert "timeout" in rule.applicable_fields
        assert "max_retries" in rule.applicable_fields


class TestCreateDefaultRuleRegistry:
    """创建默认规则注册表测试"""
    
    def test_create_default_rule_registry(self):
        """测试创建默认规则注册表"""
        registry = create_default_rule_registry()
        
        assert isinstance(registry, ValidationRuleRegistry)
        
        # 验证默认规则被注册
        all_rules = registry.get_all_rules()
        assert len(all_rules) > 0
        
        # 验证特定规则存在
        assert "required_field_model_name" in all_rules
        assert "type_validation_model_type" in all_rules
        assert "model_name_validation" in all_rules
        assert "api_key_validation" in all_rules
        assert "url_validation" in all_rules
        assert "timeout_validation" in all_rules
    
    def test_default_rules_functionality(self):
        """测试默认规则功能"""
        registry = create_default_rule_registry()
        
        # 测试必填字段规则
        config = MockConfig(model_name="")
        result = registry.validate_field(config, "model_name", "")
        assert result.is_valid == False
        
        # 测试模型名称规则
        result = registry.validate_field(config, "model_name", "invalid-model")
        assert result.is_valid == False
        
        # 测试API密钥规则
        result = registry.validate_field(config, "api_key", None)
        assert result.is_valid == False