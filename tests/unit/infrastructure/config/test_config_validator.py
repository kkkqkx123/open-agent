"""配置验证器测试"""

import pytest
from pydantic import ValidationError
from infrastructure.config.utils.validator import ConfigValidator, ValidationResult
from src.infrastructure.config.models.global_config import GlobalConfig
from src.infrastructure.config.models.llm_config import LLMConfig
from src.infrastructure.config.models.agent_config import AgentConfig
from src.infrastructure.config.models.tool_config import ToolConfig


class TestConfigValidator:
    """配置验证器测试类"""

    def setup_method(self):
        """测试前设置"""
        self.validator = ConfigValidator()

    def test_validate_config_success(self):
        """测试成功验证配置"""
        config = {
            "log_level": "INFO",
            "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
            "secret_patterns": ["sk-.*"],
            "env": "development",
        }

        result = self.validator.validate_config(config, GlobalConfig)

        assert result.is_valid
        assert not result.has_errors()
        assert not result.has_warnings()

    def test_validate_config_failure(self):
        """测试失败验证配置"""
        config = {
            "log_level": "INVALID_LEVEL",
            "log_outputs": [],
            "secret_patterns": [],
        }

        result = self.validator.validate_config(config, GlobalConfig)

        assert not result.is_valid
        assert result.has_errors()
        assert not result.has_warnings()
        assert any("log_level" in error for error in result.errors)

    def test_validate_llm_config_success(self):
        """测试成功验证LLM配置"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-test123456789",
            "parameters": {"temperature": 0.7, "max_tokens": 2000},
        }

        result = self.validator.validate_llm_config(config)

        assert result.is_valid
        assert not result.has_errors()

    def test_validate_llm_config_missing_api_key(self):
        """测试缺少API密钥的LLM配置"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "base_url": "https://api.openai.com/v1",
            "parameters": {"temperature": 0.7},
        }

        result = self.validator.validate_llm_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any("API密钥" in warning for warning in result.warnings)

    def test_validate_llm_config_invalid_type(self):
        """测试无效模型类型的LLM配置"""
        config = {"model_type": "invalid_type", "model_name": "gpt-4"}

        result = self.validator.validate_llm_config(config)

        assert not result.is_valid
        assert result.has_errors()

    def test_validate_agent_config_success(self):
        """测试成功验证Agent配置"""
        config = {
            "name": "test_agent",
            "llm": "gpt-4",
            "tool_sets": ["basic"],
            "tools": ["search"],
            "system_prompt": "You are a helpful assistant.",
            "rules": ["be_helpful"],
            "user_command": "help",
        }

        result = self.validator.validate_agent_config(config)

        assert result.is_valid
        assert not result.has_errors()

    def test_validate_agent_config_no_tools(self):
        """测试无工具的Agent配置"""
        config = {
            "name": "test_agent",
            "llm": "gpt-4",
            "system_prompt": "You are a helpful assistant.",
        }

        result = self.validator.validate_agent_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any("工具" in warning for warning in result.warnings)

    def test_validate_agent_config_empty_prompt(self):
        """测试空提示词的Agent配置"""
        config = {"name": "test_agent", "llm": "gpt-4", "tools": ["search"]}

        result = self.validator.validate_agent_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any("提示词" in warning for warning in result.warnings)

    def test_validate_tool_config_success(self):
        """测试成功验证工具配置"""
        config = {
            "name": "test_tool",
            "description": "Test tool",
            "tools": ["search", "calculator"],
            "timeout": 30,
            "max_retries": 3,
            "parameters": {"param1": "value1"},
        }

        result = self.validator.validate_tool_config(config)

        assert result.is_valid
        assert not result.has_errors()

    def test_validate_tool_config_no_tools(self):
        """测试无工具的工具配置"""
        config = {
            "name": "test_tool",
            "description": "Test tool",
            "timeout": 30,
            "max_retries": 3,
        }

        result = self.validator.validate_tool_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any("工具" in warning for warning in result.warnings)

    def test_validate_global_config_success(self):
        """测试成功验证全局配置"""
        config = {
            "log_level": "INFO",
            "log_outputs": [
                {"type": "console", "level": "INFO", "format": "text"},
                {
                    "type": "file",
                    "level": "DEBUG",
                    "format": "json",
                    "path": "logs/agent.log",
                },
            ],
            "secret_patterns": ["sk-[a-zA-Z0-9]{20,}", "\\w+@\\w+\\.\\w+"],
            "env": "development",
            "debug": False,
            "hot_reload": True,
            "watch_interval": 5,
        }

        result = self.validator.validate_global_config(config)

        assert result.is_valid
        assert not result.has_errors()

    def test_validate_global_config_no_log_outputs(self):
        """测试无日志输出的全局配置"""
        config = {
            "log_level": "INFO",
            "log_outputs": [],
            "secret_patterns": [],
            "env": "development",
        }

        result = self.validator.validate_global_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any("日志输出" in warning for warning in result.warnings)

    def test_validate_global_config_no_secret_patterns(self):
        """测试无敏感信息模式的全局配置"""
        config = {
            "log_level": "INFO",
            "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
            "secret_patterns": [],
            "env": "development",
        }

        result = self.validator.validate_global_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any("敏感信息" in warning for warning in result.warnings)

    def test_validate_global_config_production_with_debug(self):
        """测试生产环境启用调试模式的全局配置"""
        config = {
            "log_level": "INFO",
            "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
            "secret_patterns": ["sk-.*"],
            "env": "production",
            "debug": True,
        }

        result = self.validator.validate_global_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any(
            "生产环境" in warning and "调试模式" in warning
            for warning in result.warnings
        )

    def test_validate_global_config_file_log_no_path(self):
        """测试文件日志无路径的全局配置"""
        config = {
            "log_level": "INFO",
            "log_outputs": [
                {
                    "type": "file",
                    "level": "DEBUG",
                    "format": "json",
                    # 缺少path
                }
            ],
            "secret_patterns": ["sk-.*"],
            "env": "development",
        }

        result = self.validator.validate_global_config(config)

        assert result.is_valid  # 基本验证通过
        assert result.has_warnings()  # 但有警告
        assert any(
            "文件日志" in warning and "路径" in warning for warning in result.warnings
        )

    def test_validate_config_structure(self):
        """测试配置结构验证"""
        config = {"field1": "value1", "field2": 123}

        # 测试成功情况
        result = self.validator.validate_config_structure(config, ["field1", "field2"])
        assert result.is_valid
        assert not result.has_errors()

        # 测试失败情况
        result = self.validator.validate_config_structure(config, ["field1", "field3"])
        assert not result.is_valid
        assert result.has_errors()
        assert any("field3" in error for error in result.errors)

    def test_validate_config_types(self):
        """测试配置类型验证"""
        config = {"string_field": "value", "int_field": 123, "bool_field": True}

        type_mapping = {"string_field": str, "int_field": int, "bool_field": bool}

        # 测试成功情况
        result = self.validator.validate_config_types(config, type_mapping)
        assert result.is_valid
        assert not result.has_errors()

        # 测试失败情况
        config["int_field"] = "not_an_int"
        result = self.validator.validate_config_types(config, type_mapping)
        assert not result.is_valid
        assert result.has_errors()
        assert any("int_field" in error for error in result.errors)

    def test_validate_config_values(self):
        """测试配置值验证"""
        import re

        config = {
            "enum_field": "option1",
            "range_field": 5,
            "length_field": "valid_string",
            "pattern_field": "abc123",
        }

        value_constraints = {
            "enum_field": {"enum": ["option1", "option2", "option3"]},
            "range_field": {"min": 1, "max": 10},
            "length_field": {"min_length": 5, "max_length": 20},
            "pattern_field": {"pattern": re.compile(r"^[a-z]+[0-9]+$")},
        }

        # 测试成功情况
        result = self.validator.validate_config_values(config, value_constraints)
        assert result.is_valid
        assert not result.has_errors()

        # 测试枚举值失败
        config["enum_field"] = "invalid_option"
        result = self.validator.validate_config_values(config, value_constraints)
        assert not result.is_valid
        assert result.has_errors()

        # 重置为有效值
        config["enum_field"] = "option1"

        # 测试范围失败
        config["range_field"] = 20
        result = self.validator.validate_config_values(config, value_constraints)
        assert not result.is_valid
        assert result.has_errors()

        # 重置为有效值
        config["range_field"] = 5

        # 测试长度失败
        config["length_field"] = "sh"  # 长度为2，小于min_length=5
        result = self.validator.validate_config_values(config, value_constraints)
        assert not result.is_valid
        assert result.has_errors()

        # 重置为有效值
        config["length_field"] = "valid_string"

        # 测试模式失败
        config["pattern_field"] = "invalid_pattern"
        result = self.validator.validate_config_values(config, value_constraints)
        assert not result.is_valid
        assert result.has_errors()

    def test_validation_result_add_error(self):
        """测试验证结果添加错误"""
        result = ValidationResult(True)

        assert result.is_valid
        assert not result.has_errors()

        result.add_error("Test error")

        assert not result.is_valid
        assert result.has_errors()
        assert "Test error" in result.errors

    def test_validation_result_add_warning(self):
        """测试验证结果添加警告"""
        result = ValidationResult(True)

        assert not result.has_warnings()

        result.add_warning("Test warning")

        assert result.has_warnings()
        assert "Test warning" in result.warnings
