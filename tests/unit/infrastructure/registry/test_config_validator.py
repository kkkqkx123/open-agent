"""配置验证器单元测试"""

import pytest
from src.infrastructure.registry.config_validator import (
    BaseConfigValidator,
    ValidationResult,
    ValidationSeverity
)


class TestValidationResult:
    """测试ValidationResult类"""
    
    def test_init(self):
        """测试初始化"""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.info == []
    
    def test_add_error(self):
        """测试添加错误"""
        result = ValidationResult()
        result.add_error("测试错误")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "测试错误"
    
    def test_add_warning(self):
        """测试添加警告"""
        result = ValidationResult()
        result.add_warning("测试警告")
        
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.warnings[0] == "测试警告"
    
    def test_add_info(self):
        """测试添加信息"""
        result = ValidationResult()
        result.add_info("测试信息")
        
        assert result.is_valid is True
        assert len(result.info) == 1
        assert result.info[0] == "测试信息"
    
    def test_merge(self):
        """测试合并结果"""
        result1 = ValidationResult()
        result1.add_error("错误1")
        result1.add_warning("警告1")
        
        result2 = ValidationResult()
        result2.add_error("错误2")
        result2.add_info("信息1")
        
        result1.merge(result2)
        
        assert result1.is_valid is False
        assert len(result1.errors) == 2
        assert len(result1.warnings) == 1
        assert len(result1.info) == 1
    
    def test_has_messages(self):
        """测试检查消息"""
        result = ValidationResult()
        
        # 测试没有消息
        assert not result.has_messages(ValidationSeverity.ERROR)
        assert not result.has_messages(ValidationSeverity.WARNING)
        assert not result.has_messages(ValidationSeverity.INFO)
        
        # 添加错误
        result.add_error("错误")
        assert result.has_messages(ValidationSeverity.ERROR)
        assert not result.has_messages(ValidationSeverity.WARNING)
        assert not result.has_messages(ValidationSeverity.INFO)
        
        # 添加警告
        result.add_warning("警告")
        assert result.has_messages(ValidationSeverity.ERROR)
        assert result.has_messages(ValidationSeverity.WARNING)
        assert not result.has_messages(ValidationSeverity.INFO)
        
        # 添加信息
        result.add_info("信息")
        assert result.has_messages(ValidationSeverity.ERROR)
        assert result.has_messages(ValidationSeverity.WARNING)
        assert result.has_messages(ValidationSeverity.INFO)
    
    def test_get_messages(self):
        """测试获取消息"""
        result = ValidationResult()
        result.add_error("错误1")
        result.add_error("错误2")
        result.add_warning("警告1")
        result.add_info("信息1")
        
        errors = result.get_messages(ValidationSeverity.ERROR)
        warnings = result.get_messages(ValidationSeverity.WARNING)
        info = result.get_messages(ValidationSeverity.INFO)
        
        assert len(errors) == 2
        assert len(warnings) == 1
        assert len(info) == 1
        assert "错误1" in errors
        assert "错误2" in errors
        assert warnings[0] == "警告1"
        assert info[0] == "信息1"


class TestBaseConfigValidator:
    """测试BaseConfigValidator类"""
    
    def test_init(self):
        """测试初始化"""
        validator = BaseConfigValidator("TestValidator")
        assert validator.name == "TestValidator"
    
    def test_validate_empty_config(self):
        """测试验证空配置"""
        validator = BaseConfigValidator()
        result = validator.validate({})
        
        assert result.is_valid is False
        assert any("配置不能为空" in error for error in result.errors)
    
    def test_validate_non_dict_config(self):
        """测试验证非字典配置"""
        validator = BaseConfigValidator()
        result = validator.validate("invalid")  # type: ignore
        
        assert result.is_valid is False
        assert any("配置必须是字典类型" in error for error in result.errors)
    
    def test_validate_valid_config(self):
        """测试验证有效配置"""
        validator = BaseConfigValidator()
        result = validator.validate({"key": "value"})
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_required_fields(self):
        """测试验证必需字段"""
        validator = BaseConfigValidator()
        config = {"existing_field": "value"}
        required_fields = ["missing_field", "another_missing"]
        
        result = ValidationResult()
        validator._validate_required_fields(config, required_fields, result)
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert any("missing_field" in error for error in result.errors)
        assert any("another_missing" in error for error in result.errors)
    
    def test_validate_field_types(self):
        """测试验证字段类型"""
        validator = BaseConfigValidator()
        config = {"string_field": "value", "int_field": 123}
        type_rules = {
            "string_field": str,
            "int_field": int,
            "bool_field": bool
        }
        
        result = ValidationResult()
        validator._validate_field_types(config, type_rules, result)
        
        # 应该没有错误，因为bool_field不在配置中
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # 添加错误类型的字段
        config["int_field"] = "not_an_int"
        validator._validate_field_types(config, type_rules, result)
        
        assert result.is_valid is False
        assert any("int_field" in error for error in result.errors)
    
    def test_validate_field_values(self):
        """测试验证字段值"""
        validator = BaseConfigValidator()
        config = {"enum_field": "value1", "range_field": 5}
        value_rules = {
            "enum_field": {"enum": ["value1", "value2"]},
            "range_field": {"range": [1, 10]},
            "pattern_field": {"pattern": r"^[a-z]+$"}
        }
        
        result = ValidationResult()
        validator._validate_field_values(config, value_rules, result)
        
        # 应该没有错误
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # 测试枚举值错误
        config["enum_field"] = "invalid_value"
        validator._validate_field_values(config, value_rules, result)
        
        assert result.is_valid is False
        assert any("enum_field" in error for error in result.errors)
        
        # 测试范围错误
        config["enum_field"] = "value1"  # 恢复有效值
        config["range_field"] = 15
        validator._validate_field_values(config, value_rules, result)
        
        assert result.is_valid is False
        assert any("range_field" in error for error in result.errors)
    
    def test_validate_class_path(self):
        """测试验证类路径"""
        validator = BaseConfigValidator()
        result = ValidationResult()
        
        # 测试有效类路径
        validator._validate_class_path("module.submodule:ClassName", result)
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # 测试无效类路径 - 缺少冒号
        validator._validate_class_path("module.submodule.ClassName", result)
        assert result.is_valid is False
        assert any("类路径格式不正确" in error for error in result.errors)
        
        # 测试无效类路径 - 空字符串
        validator._validate_class_path("", result)
        assert result.is_valid is False
        assert any("类路径不能为空" in error for error in result.errors)
    
    def test_validate_file_path(self):
        """测试验证文件路径"""
        validator = BaseConfigValidator()
        result = ValidationResult()
        
        # 测试有效文件路径
        validator._validate_file_path("path/to/file.yaml", result)
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # 测试无效文件路径 - 包含非法字符
        validator._validate_file_path("path/to/file<>.yaml", result)
        assert result.is_valid is False
        assert any("文件路径包含非法字符" in error for error in result.errors)
        
        # 测试无效文件路径 - 空字符串
        validator._validate_file_path("", result)
        assert result.is_valid is False
        assert any("文件路径不能为空" in error for error in result.errors)


if __name__ == "__main__":
    pytest.main([__file__])