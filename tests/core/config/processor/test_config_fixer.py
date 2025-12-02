"""config_fixer.py模块的单元测试"""

import pytest
from src.core.config.processor.config_fixer import ConfigFixer
from src.core.config.processor.validation_report import FixSuggestion


class TestConfigFixer:
    """ConfigFixer类的测试"""

    def setup_method(self):
        """测试前的设置"""
        self.config_fixer = ConfigFixer()

    def test_init(self):
        """测试初始化"""
        assert isinstance(self.config_fixer, ConfigFixer)
        assert len(self.config_fixer.fix_strategies) == 3
        assert "missing_field" in self.config_fixer.fix_strategies
        assert "invalid_type" in self.config_fixer.fix_strategies
        assert "invalid_value" in self.config_fixer.fix_strategies

    def test_suggest_fixes_missing_field(self):
        """测试缺失字段的修复建议"""
        config = {"existing_field": "value"}
        field_issues = [
            {
                "field": "missing_field",
                "type": "missing_field",
                "default_value": "default_value"
            }
        ]
        
        suggestions = self.config_fixer.suggest_fixes(config, field_issues)
        assert len(suggestions) == 1
        assert isinstance(suggestions[0], FixSuggestion)
        assert "添加缺失字段" in suggestions[0].description

        # 应用修复建议
        suggestions[0].apply()
        assert "missing_field" in config
        assert config["missing_field"] == "default_value"

    def test_suggest_fixes_invalid_type(self):
        """测试无效类型的修复建议"""
        config = {"field": "not_an_int"}
        field_issues = [
            {
                "field": "field",
                "type": "invalid_type",
                "expected_type": int
            }
        ]
        
        suggestions = self.config_fixer.suggest_fixes(config, field_issues)
        assert len(suggestions) == 1
        assert "修复字段 'field' 的类型错误" in suggestions[0].description

        # 应用修复建议
        suggestions[0].apply()
        # 由于无法将字符串转换为整数，应使用默认值
        assert config["field"] == 0

    def test_suggest_fixes_invalid_value(self):
        """测试无效值的修复建议"""
        config = {"field": "invalid_value"}
        field_issues = [
            {
                "field": "field",
                "type": "invalid_value",
                "valid_values": ["valid_value1", "valid_value2"]
            }
        ]
        
        suggestions = self.config_fixer.suggest_fixes(config, field_issues)
        assert len(suggestions) == 1
        assert "修复字段 'field' 的无效值" in suggestions[0].description

        # 应用修复建议
        suggestions[0].apply()
        assert config["field"] == "valid_value1"

    def test_suggest_fixes_multiple_issues(self):
        """测试多个问题的修复建议"""
        config = {"field1": "invalid_type"}
        field_issues = [
            {
                "field": "field1",
                "type": "invalid_type",
                "expected_type": int
            },
            {
                "field": "field2",
                "type": "missing_field",
                "default_value": "default"
            }
        ]
        
        suggestions = self.config_fixer.suggest_fixes(config, field_issues)
        assert len(suggestions) == 2

        # 应用所有修复建议
        for suggestion in suggestions:
            suggestion.apply()
        
        assert config["field1"] == 0  # 修复类型错误
        assert config["field2"] == "default" # 添加缺失字段

    def test_fix_missing_field(self):
        """测试修复缺失字段"""
        config = {"existing_field": "value"}
        self.config_fixer._fix_missing_field(config, "new_field", "new_value")
        assert "new_field" in config
        assert config["new_field"] == "new_value"

    def test_fix_missing_field_already_exists(self):
        """测试字段已存在的情况"""
        config = {"existing_field": "original_value"}
        self.config_fixer._fix_missing_field(config, "existing_field", "new_value")
        # 字段已存在，不应修改
        assert config["existing_field"] == "original_value"

    def test_fix_invalid_type_convertible(self):
        """测试可转换类型的修复"""
        config = {"field": "123"}
        self.config_fixer._fix_invalid_type(config, "field", int)
        assert config["field"] == 123  # 字符串"123"可以转换为整数

    def test_fix_invalid_type_not_convertible(self):
        """测试不可转换类型的修复"""
        config = {"field": "not_an_int"}
        self.config_fixer._fix_invalid_type(config, "field", int)
        assert config["field"] == 0  # 无法转换，使用默认值

    def test_fix_invalid_value_with_valid_values(self):
        """测试修复无效值（有有效值列表）"""
        config = {"field": "invalid_value"}
        self.config_fixer._fix_invalid_value(config, "field", ["valid1", "valid2"])
        assert config["field"] == "valid1"

    def test_fix_invalid_value_empty_valid_values(self):
        """测试修复无效值（空有效值列表）"""
        config = {"field": "invalid_value"}
        self.config_fixer._fix_invalid_value(config, "field", [])
        assert config["field"] is None

    def test_get_default_value_str(self):
        """测试获取字符串默认值"""
        default = self.config_fixer._get_default_value(str)
        assert default == ""

    def test_get_default_value_int(self):
        """测试获取整数默认值"""
        default = self.config_fixer._get_default_value(int)
        assert default == 0

    def test_get_default_value_float(self):
        """测试获取浮点数默认值"""
        default = self.config_fixer._get_default_value(float)
        assert default == 0.0

    def test_get_default_value_bool(self):
        """测试获取布尔值默认值"""
        default = self.config_fixer._get_default_value(bool)
        assert default is False

    def test_get_default_value_list(self):
        """测试获取列表默认值"""
        default = self.config_fixer._get_default_value(list)
        assert default == []

    def test_get_default_value_dict(self):
        """测试获取字典默认值"""
        default = self.config_fixer._get_default_value(dict)
        assert default == {}

    def test_get_default_value_other_type(self):
        """测试获取其他类型默认值"""
        default = self.config_fixer._get_default_value(object)
        assert default is None