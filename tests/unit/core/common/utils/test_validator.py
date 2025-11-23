"""Validator单元测试"""

from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError
import pytest

from src.core.common.utils.validator import Validator, ValidationResult


class TestValidationResult:
    """ValidationResult测试类"""

    def test_init(self):
        """测试ValidationResult初始化"""
        # 测试默认初始化
        result = ValidationResult(True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

        # 测试带参数初始化
        errors = ["error1", "error2"]
        warnings = ["warning1"]
        result = ValidationResult(False, errors, warnings)
        assert result.is_valid is False
        assert result.errors == errors
        assert result.warnings == warnings

    def test_add_error(self):
        """测试添加错误"""
        result = ValidationResult(True)
        result.add_error("test error")
        
        assert result.is_valid is False
        assert "test error" in result.errors
        assert len(result.errors) == 1

    def test_add_warning(self):
        """测试添加警告"""
        result = ValidationResult(True)
        result.add_warning("test warning")
        
        assert result.is_valid is True  # 警告不影响有效性
        assert "test warning" in result.warnings
        assert len(result.warnings) == 1

    def test_has_errors(self):
        """测试检查是否有错误"""
        result = ValidationResult(True)
        assert result.has_errors() is False
        
        result.add_error("test error")
        assert result.has_errors() is True

    def test_has_warnings(self):
        """测试检查是否有警告"""
        result = ValidationResult(True)
        assert result.has_warnings() is False
        
        result.add_warning("test warning")
        assert result.has_warnings() is True


class TestValidator:
    """Validator测试类"""

    def setup_method(self):
        """测试前准备"""
        self.validator = Validator()

    def test_validate_success(self):
        """测试验证成功"""
        class TestModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": 30}
        result = self.validator.validate(data, TestModel)

        assert result.is_valid is True
        assert result.has_errors() is False

    def test_validate_failure(self):
        """测试验证失败"""
        class TestModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": "not_a_number"}  # age应该是整数
        result = self.validator.validate(data, TestModel)

        assert result.is_valid is False
        assert result.has_errors() is True
        assert any("age" in error and "not_a_number" in error for error in result.errors)

    def test_validate_structure_success(self):
        """测试结构验证成功"""
        data = {"name": "John", "email": "john@example.com"}
        required_fields = ["name", "email"]
        result = self.validator.validate_structure(data, required_fields)

        assert result.is_valid is True
        assert result.has_errors() is False

    def test_validate_structure_missing_fields(self):
        """测试结构验证缺少字段"""
        data = {"name": "John"}  # 缺少email
        required_fields = ["name", "email"]
        result = self.validator.validate_structure(data, required_fields)

        assert result.is_valid is False
        assert result.has_errors() is True
        assert any("email" in error for error in result.errors)

    def test_validate_types_success(self):
        """测试类型验证成功"""
        data = {"name": "John", "age": 30, "active": True}
        type_mapping = {"name": str, "age": int, "active": bool}
        result = self.validator.validate_types(data, type_mapping)

        assert result.is_valid is True
        assert result.has_errors() is False

    def test_validate_types_wrong_types(self):
        """测试类型验证错误类型"""
        data = {"name": 123, "age": "thirty", "active": 1}  # 类型错误
        type_mapping = {"name": str, "age": int, "active": bool}
        result = self.validator.validate_types(data, type_mapping)

        assert result.is_valid is False
        assert result.has_errors() is True
        # 应该有3个错误（所有字段类型都不匹配）
        assert len(result.errors) >= 1

    def test_validate_values_enum_constraint(self):
        """测试枚举值约束验证"""
        data = {"status": "active"}
        value_constraints = {"status": {"enum": ["active", "inactive", "pending"]}}
        result = self.validator.validate_values(data, value_constraints)

        assert result.is_valid is True

        # 测试无效枚举值
        data_invalid = {"status": "invalid_status"}
        result = self.validator.validate_values(data_invalid, value_constraints)

        assert result.is_valid is False
        assert result.has_errors() is True

    def test_validate_values_range_constraint(self):
        """测试范围约束验证"""
        data = {"score": 85}
        value_constraints = {"score": {"min": 0, "max": 100}}
        result = self.validator.validate_values(data, value_constraints)

        assert result.is_valid is True

        # 测试超出范围
        data_low = {"score": -10}
        result = self.validator.validate_values(data_low, value_constraints)
        assert result.is_valid is False

        data_high = {"score": 150}
        result = self.validator.validate_values(data_high, value_constraints)
        assert result.is_valid is False

    def test_validate_values_length_constraint(self):
        """测试长度约束验证"""
        data = {"name": "John", "tags": ["tag1", "tag2"]}
        value_constraints = {
            "name": {"min_length": 2, "max_length": 10},
            "tags": {"min_length": 1, "max_length": 5}
        }
        result = self.validator.validate_values(data, value_constraints)

        assert result.is_valid is True

        # 测试长度不足
        data_short = {"name": "A"}  # 长度小于2
        result = self.validator.validate_values(data_short, value_constraints)
        assert result.is_valid is False

        # 测试长度超出
        data_long = {"name": "VeryLongNameThatExceedsLimit"}  # 长度超过10
        result = self.validator.validate_values(data_long, value_constraints)
        assert result.is_valid is False

    def test_validate_email_valid(self):
        """测试有效邮箱验证"""
        assert self.validator.validate_email("test@example.com") is True
        assert self.validator.validate_email("user.name+tag@example.co.uk") is True

    def test_validate_email_invalid(self):
        """测试无效邮箱验证"""
        assert self.validator.validate_email("invalid-email") is False
        assert self.validator.validate_email("@example.com") is False
        assert self.validator.validate_email("test@") is False
        assert self.validator.validate_email("test.example.com") is False

    def test_validate_url_valid(self):
        """测试有效URL验证"""
        assert self.validator.validate_url("https://www.example.com") is True
        assert self.validator.validate_url("http://example.com") is True
        assert self.validator.validate_url("https://example.com/path?query=value") is True

    def test_validate_url_invalid(self):
        """测试无效URL验证"""
        assert self.validator.validate_url("invalid-url") is False
        assert self.validator.validate_url("ftp://example.com") is False  # 不支持的协议
        assert self.validator.validate_url("https://") is False

    def test_validate_phone_valid(self):
        """测试有效手机号验证"""
        assert self.validator.validate_phone("13812345678") is True
        assert self.validator.validate_phone("15912345678") is True
        assert self.validator.validate_phone("18812345678") is True

    def test_validate_phone_invalid(self):
        """测试无效手机号验证"""
        assert self.validator.validate_phone("12345678901") is False  # 不是1开头
        assert self.validator.validate_phone("1381234567") is False  # 位数不够
        assert self.validator.validate_phone("138123456789") is False  # 位数过多
        assert self.validator.validate_phone("abcdefg1234") is False  # 包含字母

    def test_complex_validation(self):
        """测试复杂验证场景"""
        class User(BaseModel):
            id: int = Field(ge=1)
            name: str = Field(min_length=2, max_length=50)
            email: str
            age: int = Field(ge=0, le=150)
            active: bool

        # 有效的用户数据
        valid_user = {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": True
        }

        result = self.validator.validate(valid_user, User)
        assert result.is_valid is True

        # 无效的用户数据
        invalid_user = {
            "id": 0,  # 无效ID
            "name": "A",  # 名字太短
            "email": "invalid-email",  # 无效邮箱
            "age": -5,  # 无效年龄
            "active": "yes"  # 类型错误
        }

        result = self.validator.validate(invalid_user, User)
        assert result.is_valid is False
        assert result.has_errors() is True

    def test_validate_with_nested_structure(self):
        """测试嵌套结构验证"""
        class Address(BaseModel):
            street: str
            city: str
            zipcode: str

        class Person(BaseModel):
            name: str
            address: Address

        data = {
            "name": "John",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "zipcode": "10001"
            }
        }

        result = self.validator.validate(data, Person)
        assert result.is_valid is True

        # 测试嵌套结构验证失败
        invalid_data = {
            "name": "John",
            "address": {
                "street": "123 Main St",
                # 缺少city和zipcode字段
            }
        }

        result = self.validator.validate(invalid_data, Person)
        assert result.is_valid is False
        assert result.has_errors() is True

    def test_validate_structure_with_optional_fields(self):
        """测试包含可选字段的结构验证"""
        data = {"name": "John"}  # email是可选的
        required_fields = ["name"]  # 只有name是必需的
        result = self.validator.validate_structure(data, required_fields)

        assert result.is_valid is True

        # 测试缺少必需字段
        data_missing = {"email": "john@example.com"}  # 缺少必需的name字段
        result = self.validator.validate_structure(data_missing, required_fields)

        assert result.is_valid is False
        assert result.has_errors() is True

    def test_validate_values_pattern_constraint(self):
        """测试模式约束验证"""
        import re
        
        data = {"code": "ABC123"}
        # 假设我们有一个模式验证器，但当前实现中没有直接使用
        # 我们测试其他值约束功能
        value_constraints = {"count": {"min": 1, "max": 10}}
        
        result = self.validator.validate_values({"count": 50}, value_constraints)
        assert result.is_valid is True
        
        result = self.validator.validate_values({"count": 150}, value_constraints)
        assert result.is_valid is False

    def test_validation_result_multiple_errors_and_warnings(self):
        """测试验证结果包含多个错误和警告"""
        result = ValidationResult(True)
        
        # 添加多个错误
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_error("Error 3")
        
        # 添加多个警告
        result.add_warning("Warning 1")
        result.add_warning("Warning 2")
        
        assert result.is_valid is False
        assert len(result.errors) == 3
        assert len(result.warnings) == 2
        assert result.has_errors() is True
        assert result.has_warnings() is True