"""验证结果单元测试"""

import pytest

from src.infrastructure.llm.validation.validation_result import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult
)


class TestValidationSeverity:
    """验证严重程度测试"""
    
    def test_severity_values(self):
        """测试严重程度值"""
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.INFO.value == "info"


class TestValidationIssue:
    """验证问题测试"""
    
    def test_validation_issue_creation(self):
        """测试创建验证问题"""
        issue = ValidationIssue(
            field="model_name",
            message="模型名称不能为空",
            severity=ValidationSeverity.ERROR,
            code="REQUIRED_FIELD",
            context={"example": "gpt-4"}
        )
        
        assert issue.field == "model_name"
        assert issue.message == "模型名称不能为空"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.code == "REQUIRED_FIELD"
        assert issue.context == {"example": "gpt-4"}
    
    def test_validation_issue_to_dict(self):
        """测试验证问题转换为字典"""
        issue = ValidationIssue(
            field="temperature",
            message="温度参数超出范围",
            severity=ValidationSeverity.WARNING,
            code="TEMPERATURE_OUT_OF_RANGE",
            context={"min": 0.0, "max": 2.0, "actual": 2.5}
        )
        
        result = issue.to_dict()
        
        expected = {
            "field": "temperature",
            "message": "温度参数超出范围",
            "severity": "warning",
            "code": "TEMPERATURE_OUT_OF_RANGE",
            "context": {"min": 0.0, "max": 2.0, "actual": 2.5}
        }
        
        assert result == expected
    
    def test_validation_issue_str(self):
        """测试验证问题字符串表示"""
        issue = ValidationIssue(
            field="api_key",
            message="API密钥格式不正确",
            severity=ValidationSeverity.ERROR,
            code="INVALID_API_KEY_FORMAT"
        )
        
        result = str(issue)
        expected = "[ERROR] api_key: API密钥格式不正确"
        
        assert result == expected
    
    def test_validation_issue_str_warning(self):
        """测试验证问题字符串表示（警告）"""
        issue = ValidationIssue(
            field="timeout",
            message="超时时间较长",
            severity=ValidationSeverity.WARNING,
            code="LONG_TIMEOUT"
        )
        
        result = str(issue)
        expected = "[WARNING] timeout: 超时时间较长"
        
        assert result == expected
    
    def test_validation_issue_str_info(self):
        """测试验证问题字符串表示（信息）"""
        issue = ValidationIssue(
            field="max_tokens",
            message="最大token数较大",
            severity=ValidationSeverity.INFO,
            code="HIGH_MAX_TOKENS"
        )
        
        result = str(issue)
        expected = "[INFO] max_tokens: 最大token数较大"
        
        assert result == expected


class TestValidationResult:
    """验证结果测试"""
    
    def test_validation_result_creation_valid(self):
        """测试创建有效验证结果"""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid == True
        assert len(result.issues) == 0
        assert result.summary is None
    
    def test_validation_result_creation_invalid(self):
        """测试创建无效验证结果"""
        issues = [
            ValidationIssue("field1", "error1", ValidationSeverity.ERROR),
            ValidationIssue("field2", "warning1", ValidationSeverity.WARNING)
        ]
        result = ValidationResult(is_valid=False, issues=issues)
        
        assert result.is_valid == False
        assert len(result.issues) == 2
        assert result.issues == issues
    
    def test_validation_result_post_init(self):
        """测试验证结果初始化后处理"""
        # 创建时指定is_valid=True但有错误，应该被修正为False
        issues = [
            ValidationIssue("field1", "error1", ValidationSeverity.ERROR)
        ]
        result = ValidationResult(is_valid=True, issues=issues)
        
        assert result.is_valid == False  # 应该被修正
    
    def test_add_issue(self):
        """测试添加验证问题"""
        result = ValidationResult(is_valid=True)
        
        result.add_issue(
            field="model_name",
            message="模型名称无效",
            severity=ValidationSeverity.ERROR,
            code="INVALID_MODEL",
            context={"supported": ["gpt-4", "claude-3"]}
        )
        
        assert len(result.issues) == 1
        assert result.is_valid == False
        
        issue = result.issues[0]
        assert issue.field == "model_name"
        assert issue.message == "模型名称无效"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.code == "INVALID_MODEL"
        assert issue.context == {"supported": ["gpt-4", "claude-3"]}
    
    def test_add_error(self):
        """测试添加错误"""
        result = ValidationResult(is_valid=True)
        
        result.add_error(
            field="api_key",
            message="API密钥缺失",
            code="MISSING_API_KEY"
        )
        
        assert len(result.issues) == 1
        assert result.is_valid == False
        
        issue = result.issues[0]
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.code == "MISSING_API_KEY"
    
    def test_add_warning(self):
        """测试添加警告"""
        result = ValidationResult(is_valid=True)
        
        result.add_warning(
            field="temperature",
            message="温度参数接近上限",
            code="HIGH_TEMPERATURE"
        )
        
        assert len(result.issues) == 1
        assert result.is_valid == False  # 有警告时仍然无效
        
        issue = result.issues[0]
        assert issue.severity == ValidationSeverity.WARNING
        assert issue.code == "HIGH_TEMPERATURE"
    
    def test_add_info(self):
        """测试添加信息"""
        result = ValidationResult(is_valid=True)
        
        result.add_info(
            field="max_tokens",
            message="最大token数较高",
            code="HIGH_MAX_TOKENS"
        )
        
        assert len(result.issues) == 1
        assert result.is_valid == False  # 有信息时仍然无效
        
        issue = result.issues[0]
        assert issue.severity == ValidationSeverity.INFO
        assert issue.code == "HIGH_MAX_TOKENS"
    
    def test_get_errors(self):
        """测试获取所有错误"""
        result = ValidationResult(is_valid=True)
        
        result.add_error("field1", "error1", "ERROR1")
        result.add_warning("field2", "warning1", "WARNING1")
        result.add_error("field3", "error2", "ERROR2")
        result.add_info("field4", "info1", "INFO1")
        
        errors = result.get_errors()
        
        assert len(errors) == 2
        assert all(issue.severity == ValidationSeverity.ERROR for issue in errors)
        assert errors[0].code == "ERROR1"
        assert errors[1].code == "ERROR2"
    
    def test_get_warnings(self):
        """测试获取所有警告"""
        result = ValidationResult(is_valid=True)
        
        result.add_error("field1", "error1", "ERROR1")
        result.add_warning("field2", "warning1", "WARNING1")
        result.add_warning("field3", "warning2", "WARNING2")
        result.add_info("field4", "info1", "INFO1")
        
        warnings = result.get_warnings()
        
        assert len(warnings) == 2
        assert all(issue.severity == ValidationSeverity.WARNING for issue in warnings)
        assert warnings[0].code == "WARNING1"
        assert warnings[1].code == "WARNING2"
    
    def test_get_infos(self):
        """测试获取所有信息"""
        result = ValidationResult(is_valid=True)
        
        result.add_error("field1", "error1", "ERROR1")
        result.add_warning("field2", "warning1", "WARNING1")
        result.add_info("field3", "info1", "INFO1")
        result.add_info("field4", "info2", "INFO2")
        
        infos = result.get_infos()
        
        assert len(infos) == 2
        assert all(issue.severity == ValidationSeverity.INFO for issue in infos)
        assert infos[0].code == "INFO1"
        assert infos[1].code == "INFO2"
    
    def test_get_issues_by_severity(self):
        """测试根据严重程度获取问题"""
        result = ValidationResult(is_valid=True)
        
        result.add_error("field1", "error1", "ERROR1")
        result.add_warning("field2", "warning1", "WARNING1")
        result.add_info("field3", "info1", "INFO1")
        
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        warnings = result.get_issues_by_severity(ValidationSeverity.WARNING)
        infos = result.get_issues_by_severity(ValidationSeverity.INFO)
        
        assert len(errors) == 1
        assert len(warnings) == 1
        assert len(infos) == 1
        
        assert errors[0].severity == ValidationSeverity.ERROR
        assert warnings[0].severity == ValidationSeverity.WARNING
        assert infos[0].severity == ValidationSeverity.INFO
    
    def test_has_errors(self):
        """测试是否有错误"""
        result = ValidationResult(is_valid=True)
        
        # 初始状态没有错误
        assert result.has_errors() == False
        
        # 添加警告后仍然没有错误
        result.add_warning("field1", "warning1", "WARNING1")
        assert result.has_errors() == False
        
        # 添加信息后仍然没有错误
        result.add_info("field2", "info1", "INFO1")
        assert result.has_errors() == False
        
        # 添加错误后有错误
        result.add_error("field3", "error1", "ERROR1")
        assert result.has_errors() == True
    
    def test_has_warnings(self):
        """测试是否有警告"""
        result = ValidationResult(is_valid=True)
        
        # 初始状态没有警告
        assert result.has_warnings() == False
        
        # 添加错误后仍然没有警告
        result.add_error("field1", "error1", "ERROR1")
        assert result.has_warnings() == False
        
        # 添加信息后仍然没有警告
        result.add_info("field2", "info1", "INFO1")
        assert result.has_warnings() == False
        
        # 添加警告后有警告
        result.add_warning("field3", "warning1", "WARNING1")
        assert result.has_warnings() == True
    
    def test_get_field_issues(self):
        """测试获取特定字段的问题"""
        result = ValidationResult(is_valid=True)
        
        result.add_error("model_name", "error1", "ERROR1")
        result.add_warning("model_name", "warning1", "WARNING1")
        result.add_error("api_key", "error2", "ERROR2")
        result.add_info("model_name", "info1", "INFO1")
        
        model_name_issues = result.get_field_issues("model_name")
        api_key_issues = result.get_field_issues("api_key")
        non_existent_issues = result.get_field_issues("non_existent")
        
        assert len(model_name_issues) == 3
        assert len(api_key_issues) == 1
        assert len(non_existent_issues) == 0
        
        # 验证所有model_name的问题都是该字段的
        assert all(issue.field == "model_name" for issue in model_name_issues)
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = ValidationResult(is_valid=True)
        
        result.add_error("field1", "error1", "ERROR1")
        result.add_warning("field2", "warning1", "WARNING1")
        result.add_info("field3", "info1", "INFO1")
        result.summary = "测试摘要"
        
        dict_result = result.to_dict()
        
        assert dict_result["is_valid"] == False
        assert len(dict_result["issues"]) == 3
        assert dict_result["summary"] == "测试摘要"
        assert dict_result["error_count"] == 1
        assert dict_result["warning_count"] == 1
        assert dict_result["info_count"] == 1
        
        # 验证问题格式
        issue_dicts = dict_result["issues"]
        assert all(isinstance(issue, dict) for issue in issue_dicts)
    
    def test_merge(self):
        """测试合并验证结果"""
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
    
    def test_merge_one_empty_summary(self):
        """测试合并一个空摘要的验证结果"""
        result1 = ValidationResult(is_valid=True)
        result1.add_error("field1", "error1", "ERROR1")
        result1.summary = "摘要1"
        
        result2 = ValidationResult(is_valid=True)
        result2.add_warning("field2", "warning1", "WARNING1")
        # result2.summary 保持 None
        
        merged = result1.merge(result2)
        
        assert merged.summary == "摘要1"
    
    def test_str_valid(self):
        """测试有效验证结果的字符串表示"""
        result = ValidationResult(is_valid=True)
        
        result_str = str(result)
        
        assert result_str == "验证通过"
    
    def test_str_with_errors(self):
        """测试有错误的验证结果的字符串表示"""
        result = ValidationResult(is_valid=True)
        result.add_error("field1", "error1", "ERROR1")
        result.add_error("field2", "error2", "ERROR2")
        
        result_str = str(result)
        
        assert "验证失败" in result_str
        assert "2 个错误" in result_str
    
    def test_str_with_warnings(self):
        """测试有警告的验证结果的字符串表示"""
        result = ValidationResult(is_valid=True)
        result.add_warning("field1", "warning1", "WARNING1")
        result.add_warning("field2", "warning2", "WARNING2")
        
        result_str = str(result)
        
        assert "验证通过" in result_str
        assert "2 个警告" in result_str
    
    def test_str_with_errors_and_warnings(self):
        """测试有错误和警告的验证结果的字符串表示"""
        result = ValidationResult(is_valid=True)
        result.add_error("field1", "error1", "ERROR1")
        result.add_warning("field2", "warning1", "WARNING1")
        
        result_str = str(result)
        
        assert "验证失败" in result_str
        assert "1 个错误" in result_str
    
    def test_get_summary_with_custom_summary(self):
        """测试获取自定义摘要"""
        result = ValidationResult(is_valid=True)
        result.summary = "自定义摘要"
        
        summary = result.get_summary()
        
        assert summary == "自定义摘要"
    
    def test_get_summary_valid(self):
        """测试获取有效配置的摘要"""
        result = ValidationResult(is_valid=True)
        
        summary = result.get_summary()
        
        assert summary == "配置验证通过"
    
    def test_get_summary_with_errors(self):
        """测试获取有错误的摘要"""
        result = ValidationResult(is_valid=True)
        result.add_error("field1", "error1", "ERROR1")
        result.add_warning("field2", "warning1", "WARNING1")
        
        summary = result.get_summary()
        
        assert "1 个错误" in summary
        assert "1 个警告" in summary
    
    def test_get_summary_with_warnings_only(self):
        """测试获取只有警告的摘要"""
        result = ValidationResult(is_valid=True)
        result.add_warning("field1", "warning1", "WARNING1")
        result.add_warning("field2", "warning2", "WARNING2")
        
        summary = result.get_summary()
        
        assert "发现" in summary
        assert "2 个警告" in summary