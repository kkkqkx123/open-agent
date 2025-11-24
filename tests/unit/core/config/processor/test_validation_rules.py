"""validation_rules.py模块的单元测试"""

import pytest
from src.core.config.processor.validation_rules import ValidationRule
from src.core.config.processor.validation_utils import ValidationLevel
from src.core.config.processor.validation_report import EnhancedValidationResult


class TestValidationRule:
    """ValidationRule基类的测试"""

    def test_validation_rule_abstract_interface(self):
        """测试验证规则抽象接口"""
        # 验证抽象基类不能被直接实例化
        with pytest.raises(TypeError):
            ValidationRule("test_rule", ValidationLevel.SEMANTIC, "Test description")

    def test_validation_rule_attributes(self):
        """测试验证规则属性"""
        class ConcreteValidationRule(ValidationRule):
            def validate(self, config, context):
                return EnhancedValidationResult(
                    rule_id=self.rule_id,
                    level=self.level,
                    passed=True,
                    message="Test validation"
                )

        rule = ConcreteValidationRule("test_rule", ValidationLevel.SEMANTIC, "Test description")
        assert rule.rule_id == "test_rule"
        assert rule.level == ValidationLevel.SEMANTIC
        assert rule.description == "Test description"

    def test_validation_rule_validate_method(self):
        """测试验证规则的验证方法"""
        class ConcreteValidationRule(ValidationRule):
            def validate(self, config, context):
                return EnhancedValidationResult(
                    rule_id=self.rule_id,
                    level=self.level,
                    passed=True,
                    message="Test validation"
                )

        rule = ConcreteValidationRule("test_rule", ValidationLevel.SEMANTIC, "Test description")
        result = rule.validate({"key": "value"}, {"context_key": "context_value"})
        
        assert isinstance(result, EnhancedValidationResult)
        assert result.rule_id == "test_rule"
        assert result.level == ValidationLevel.SEMANTIC
        assert result.passed is True
        assert result.message == "Test validation"