"""validation_report.py模块的单元测试"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from src.core.config.processor.validation_report import (
    FixSuggestion, EnhancedValidationResult, ValidationReport
)
from src.core.config.processor.validation_utils import ValidationLevel, ValidationSeverity


class TestFixSuggestion:
    """修复建议类的测试"""

    def test_init(self):
        """测试初始化"""
        mock_action = Mock()
        suggestion = FixSuggestion("修复描述", mock_action, confidence=0.9)
        
        assert suggestion.description == "修复描述"
        assert suggestion.fix_action == mock_action
        assert suggestion.confidence == 0.9

    def test_init_default_confidence(self):
        """测试默认置信度"""
        mock_action = Mock()
        suggestion = FixSuggestion("修复描述", mock_action)
        
        assert suggestion.confidence == 0.8  # 默认值

    def test_apply_fix(self):
        """测试应用修复"""
        mock_action = Mock()
        suggestion = FixSuggestion("修复描述", mock_action)
        
        suggestion.fix_action()  # 调用修复动作
        mock_action.assert_called_once()


class TestEnhancedValidationResult:
    """增强验证结果类的测试"""

    def test_init(self):
        """测试初始化"""
        result = EnhancedValidationResult(
            rule_id="test_rule",
            level=ValidationLevel.SCHEMA,
            passed=True,
            message="测试消息"
        )
        
        assert result.rule_id == "test_rule"
        assert result.level == ValidationLevel.SCHEMA
        assert result.passed is True
        assert result.message == "测试消息"
        assert len(result.suggestions) == 0
        assert len(result.fix_suggestions) == 0
        assert isinstance(result.timestamp, datetime)
        assert result.severity == ValidationSeverity.WARNING

    def test_add_warning(self):
        """测试添加警告"""
        result = EnhancedValidationResult(
            rule_id="test_rule",
            level=ValidationLevel.SCHEMA,
            passed=True
        )
        
        result.add_warning("警告消息")
        assert result.message == "警告消息"
        assert result.severity == ValidationSeverity.WARNING


class TestValidationReport:
    """验证报告类的测试"""

    def setup_method(self):
        """测试前的设置"""
        self.report = ValidationReport("test_config.yaml")

    def test_init(self):
        """测试初始化"""
        assert self.report.config_path == "test_config.yaml"
        assert isinstance(self.report.timestamp, datetime)
        assert len(self.report.level_results) == 0
        assert self.report.summary["total_rules"] == 0
        assert self.report.summary["passed"] == 0
        assert self.report.summary["failed"] == 0
        assert self.report.summary["warnings"] == 0
        assert self.report.summary["errors"] == 0

    def test_add_level_results(self):
        """测试添加级别验证结果"""
        results = [
            EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, True),
            EnhancedValidationResult("rule2", ValidationLevel.SCHEMA, False)
        ]
        
        self.report.add_level_results(ValidationLevel.SCHEMA, results)
        
        assert ValidationLevel.SCHEMA in self.report.level_results
        assert len(self.report.level_results[ValidationLevel.SCHEMA]) == 2
        assert self.report.summary["total_rules"] == 2
        assert self.report.summary["passed"] == 1
        assert self.report.summary["failed"] == 1

    def test_get_fix_suggestions(self):
        """测试获取修复建议"""
        # 创建包含修复建议的结果
        result_with_suggestion = EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, False)
        mock_action = Mock()
        suggestion = FixSuggestion("修复建议", mock_action)
        result_with_suggestion.fix_suggestions.append(suggestion)
        
        self.report.add_level_results(ValidationLevel.SCHEMA, [result_with_suggestion])
        
        suggestions = self.report.get_fix_suggestions()
        assert len(suggestions) == 1
        assert suggestions[0] == suggestion

    def test_get_fix_suggestions_no_failed_results(self):
        """测试没有失败结果时的修复建议"""
        result = EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, True)  # 通过的测试
        self.report.add_level_results(ValidationLevel.SCHEMA, [result])
        
        suggestions = self.report.get_fix_suggestions()
        assert len(suggestions) == 0

    def test_is_valid_all_passed(self):
        """测试所有验证都通过的情况"""
        results = [
            EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, True),
            EnhancedValidationResult("rule2", ValidationLevel.SEMANTIC, True)
        ]
        self.report.add_level_results(ValidationLevel.SCHEMA, [results[0]])
        self.report.add_level_results(ValidationLevel.SEMANTIC, [results[1]])
        
        assert self.report.is_valid() is True
        assert self.report.is_valid_property is True

    def test_is_valid_with_warning(self):
        """测试包含警告但没有错误的情况"""
        result = EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, False)
        result.severity = ValidationSeverity.WARNING
        self.report.add_level_results(ValidationLevel.SCHEMA, [result])
        
        # 默认情况下，警告不算错误
        assert self.report.is_valid() is True
        
        # 但如果将最小严重级别设为WARNING，则应返回False
        assert self.report.is_valid(ValidationSeverity.WARNING) is False

    def test_is_valid_with_error(self):
        """测试包含错误的情况"""
        result = EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, False)
        result.severity = ValidationSeverity.ERROR
        self.report.add_level_results(ValidationLevel.SCHEMA, [result])
        
        assert self.report.is_valid() is False

    def test_is_valid_with_critical(self):
        """测试包含严重错误的情况"""
        result = EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, False)
        result.severity = ValidationSeverity.CRITICAL
        self.report.add_level_results(ValidationLevel.SCHEMA, [result])
        
        assert self.report.is_valid() is False

    def test_summary_updates_correctly(self):
        """测试摘要正确更新"""
        # 添加通过的验证结果
        passed_result = EnhancedValidationResult("rule1", ValidationLevel.SCHEMA, True)
        # 添加带警告的验证结果
        warning_result = EnhancedValidationResult("rule2", ValidationLevel.SEMANTIC, False)
        warning_result.severity = ValidationSeverity.WARNING
        # 添加带错误的验证结果
        error_result = EnhancedValidationResult("rule3", ValidationLevel.DEPENDENCY, False)
        error_result.severity = ValidationSeverity.ERROR
        
        self.report.add_level_results(ValidationLevel.SCHEMA, [passed_result])
        self.report.add_level_results(ValidationLevel.SEMANTIC, [warning_result])
        self.report.add_level_results(ValidationLevel.DEPENDENCY, [error_result])
        
        # 检查摘要统计
        summary = self.report.summary
        assert summary["total_rules"] == 3
        assert summary["passed"] == 1
        assert summary["failed"] == 2
        assert summary["warnings"] == 1
        assert summary["errors"] == 1