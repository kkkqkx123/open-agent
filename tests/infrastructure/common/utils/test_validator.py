"""数据验证工具单元测试

测试基础设施层数据验证工具的基本功能。
"""

import pytest
from pydantic import BaseModel, ValidationError
from src.infrastructure.common.utils.validator import (
    Validator,
    ValidationResult,
    IValidator,
)


# 测试用Pydantic模型
class TestModel(BaseModel):
    name: str
    age: int
    email: str = None


class TestValidator:
    """测试验证器"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return Validator()

    def test_validation_result_creation(self):
        """测试验证结果创建"""
        result = ValidationResult(True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

        result = ValidationResult(False, ["error1"], ["warning1"])
        assert result.is_valid is False
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]

    def test_validation_result_add_error(self):
        """测试添加错误"""
        result = ValidationResult(True)
        result.add_error("Something went wrong")
        assert result.is_valid is False
        assert result.errors == ["Something went wrong"]

    def test_validation_result_add_warning(self):
        """测试添加警告"""
        result = ValidationResult(True)
        result.add_warning("This might be a problem")
        assert result.is_valid is True  # 警告不影响有效性
        assert result.warnings == ["This might be a problem"]

    def test_validation_result_has_errors(self):
        """测试检查是否有错误"""
        result = ValidationResult(True)
        assert result.has_errors() is False
        
        result.add_error("error")
        assert result.has_errors() is True

    def test_validation_result_has_warnings(self):
        """测试检查是否有警告"""
        result = ValidationResult(True)
        assert result.has_warnings() is False
        
        result.add_warning("warning")
        assert result.has_warnings() is True

    def test_validate_with_pydantic_success(self, validator):
        """测试使用Pydantic验证成功"""
        data = {"name": "Alice", "age": 25, "email": "alice@example.com"}
        result = validator.validate(data, TestModel)
        assert result.is_valid is True
        assert result.errors == []

    def test_validate_with_pydantic_failure(self, validator):
        """测试使用Pydantic验证失败"""
        data = {"name": "Alice", "age": "not_a_number"}
        result = validator.validate(data, TestModel)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "age" in result.errors[0]

    def test_validate_with_pydantic_exception(self, validator):
        """测试验证时发生异常"""
        # 创建一个在实例化时引发异常的模型
        class BrokenModel(BaseModel):
            def __init__(self, **data):
                raise RuntimeError("Broken during validation")
        
        data = {"key": "value"}
        result = validator.validate(data, BrokenModel)
        assert result.is_valid is False
        assert "验证数据时发生错误" in result.errors[0]

    def test_validate_structure(self, validator):
        """测试验证数据结构"""
        data = {"name": "Alice", "age": 25}
        required_fields = ["name", "age"]
        result = validator.validate_structure(data, required_fields)
        assert result.is_valid is True

        # 缺少必需字段
        data = {"name": "Alice"}
        result = validator.validate_structure(data, required_fields)
        assert result.is_valid is False
        assert "缺少必需字段: age" in result.errors

    def test_validate_types(self, validator):
        """测试验证数据类型"""
        data = {"name": "Alice", "age": 25, "score": 95.5}
        type_mapping = {"name": str, "age": int, "score": float}
        result = validator.validate_types(data, type_mapping)
        assert result.is_valid is True

        # 类型不匹配
        data = {"name": "Alice", "age": "25"}
        result = validator.validate_types(data, type_mapping)
        assert result.is_valid is False
        assert "类型错误" in result.errors[0]

        # 字段不存在不应报错
        data = {"name": "Alice"}
        result = validator.validate_types(data, type_mapping)
        assert result.is_valid is True

    def test_validate_values(self, validator):
        """测试验证数据值"""
        import re
        
        data = {
            "status": "active",
            "score": 85,
            "name": "Alice",
            "tags": ["python", "test"]
        }
        
        value_constraints = {
            "status": {"enum": ["active", "inactive", "pending"]},
            "score": {"min": 0, "max": 100},
            "name": {"min_length": 2, "max_length": 50},
            "tags": {"min_length": 1, "max_length": 5},
            "email": {"pattern": re.compile(r'^[^@]+@[^@]+\.[^@]+$')}
        }
        
        result = validator.validate_values(data, value_constraints)
        assert result.is_valid is True

    def test_validate_values_enum_failure(self, validator):
        """测试枚举值验证失败"""
        data = {"status": "invalid"}
        value_constraints = {"status": {"enum": ["active", "inactive"]}}
        result = validator.validate_values(data, value_constraints)
        assert result.is_valid is False
        assert "值无效" in result.errors[0]

    def test_validate_values_range_failure(self, validator):
        """测试范围验证失败"""
        data = {"score": 150}
        value_constraints = {"score": {"min": 0, "max": 100}}
        result = validator.validate_values(data, value_constraints)
        assert result.is_valid is False
        assert "值过大" in result.errors[0]

        data = {"score": -10}
        result = validator.validate_values(data, value_constraints)
        assert result.is_valid is False
        assert "值过小" in result.errors[0]

    def test_validate_values_length_failure(self, validator):
        """测试长度验证失败"""
        data = {"name": "A"}  # 太短
        value_constraints = {"name": {"min_length": 2}}
        result = validator.validate_values(data, value_constraints)
        assert result.is_valid is False
        assert "长度过短" in result.errors[0]

        data = {"name": "A" * 51}  # 太长
        value_constraints = {"name": {"max_length": 50}}
        result = validator.validate_values(data, value_constraints)
        assert result.is_valid is False
        assert "长度过长" in result.errors[0]

    def test_validate_email(self, validator):
        """测试邮箱验证"""
        assert validator.validate_email("user@example.com") is True
        assert validator.validate_email("user.name@domain.co.uk") is True
        assert validator.validate_email("invalid") is False
        assert validator.validate_email("user@") is False
        assert validator.validate_email("@domain.com") is False

    def test_validate_url(self, validator):
        """测试URL验证"""
        assert validator.validate_url("https://example.com") is True
        assert validator.validate_url("http://example.com/path?query=1") is True
        assert validator.validate_url("ftp://example.com") is False  # 不支持ftp
        assert validator.validate_url("not-a-url") is False

    def test_validate_phone(self, validator):
        """测试手机号验证"""
        assert validator.validate_phone("13800138000") is True
        assert validator.validate_phone("13912345678") is True
        assert validator.validate_phone("12345678901") is False  # 不以1开头
        assert validator.validate_phone("1380013800") is False   # 长度不足
        assert validator.validate_phone("138001380001") is False # 长度过长

    def test_interface_implementation(self):
        """测试接口实现"""
        validator = Validator()
        assert isinstance(validator, IValidator)
        
        # 验证所有抽象方法都已实现
        data = {"name": "test"}
        model = TestModel
        
        result = validator.validate(data, model)
        assert result is not None
        
        result = validator.validate_global_config({})
        assert result is not None
        
        result = validator.validate_llm_config({})
        assert result is not None
        
        result = validator.validate_tool_config({})
        assert result is not None
        
        result = validator.validate_token_counter_config({})
        assert result is not None

    def test_config_validation_methods(self, validator):
        """测试配置验证方法（基本实现）"""
        # 这些方法默认返回True，可以被子类覆盖
        assert validator.validate_global_config({}).is_valid is True
        assert validator.validate_llm_config({}).is_valid is True
        assert validator.validate_tool_config({}).is_valid is True
        assert validator.validate_token_counter_config({}).is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])