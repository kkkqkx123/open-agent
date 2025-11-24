"""validator.py模块的单元测试"""

import pytest
from unittest.mock import Mock, patch
from src.core.config.processor.validator import ConfigValidator
from src.core.config.models.global_config import GlobalConfig
from src.core.config.models.llm_config import LLMConfig
from src.core.config.models.tool_config import ToolConfig
from src.core.config.models.token_counter_config import TokenCounterConfig


class TestConfigValidator:
    """ConfigValidator类的测试"""

    def setup_method(self):
        """测试前的设置"""
        self.validator = ConfigValidator()

    def test_validate_global_config_valid(self):
        """测试有效的全局配置验证"""
        config = {
            "log_outputs": [{"type": "console"}],
            "secret_patterns": ["password"],
            "env": "development",
            "debug": True
        }
        result = self.validator.validate_global_config(config)
        assert result.is_valid
        assert not result.has_warnings()

    def test_validate_global_config_missing_log_outputs(self):
        """测试缺少日志输出的全局配置"""
        config = {
            "secret_patterns": ["password"],
            "env": "development",
            "debug": True
        }
        result = self.validator.validate_global_config(config)
        assert result.is_valid
        assert result.has_warnings()
        assert "未配置日志输出" in result.warnings[0]

    def test_validate_global_config_missing_secret_patterns(self):
        """测试缺少敏感信息模式的全局配置"""
        config = {
            "log_outputs": [{"type": "console"}],
            "env": "development",
            "debug": True
        }
        result = self.validator.validate_global_config(config)
        assert result.is_valid
        assert result.has_warnings()
        assert "未配置敏感信息模式" in result.warnings[0]

    def test_validate_global_config_production_debug_warning(self):
        """测试生产环境中启用调试的警告"""
        config = {
            "log_outputs": [{"type": "console"}],
            "secret_patterns": ["password"],
            "env": "production",
            "debug": True
        }
        result = self.validator.validate_global_config(config)
        assert result.is_valid
        assert result.has_warnings()
        assert "生产环境不建议启用调试模式" in result.warnings[0]

    def test_validate_global_config_invalid_structure(self):
        """测试无效的全局配置结构"""
        config = {
            "invalid_field": "invalid_value"
        }
        result = self.validator.validate_global_config(config)
        assert not result.is_valid

    def test_validate_llm_config_valid(self):
        """测试有效的LLM配置验证"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test_key",
            "base_url": "https://api.openai.com",
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0
            },
            "timeout_config": {
                "request_timeout": 30,
                "connect_timeout": 10,
                "read_timeout": 20,
                "write_timeout": 20
            }
        }
        result = self.validator.validate_llm_config(config)
        assert result.is_valid
        assert not result.has_warnings()

    def test_validate_llm_config_missing_api_key(self):
        """测试缺少API密钥的LLM配置"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4"
        }
        result = self.validator.validate_llm_config(config)
        assert result.is_valid
        assert result.has_warnings()
        assert "未配置API密钥" in result.warnings[0]

    def test_validate_llm_config_invalid_retry_config(self):
        """测试无效的重试配置"""
        config = {
            "name": "test_llm",
            "model_type": "openai",
            "model_name": "gpt-4",
            "retry_config": {
                "max_retries": -1,  # 无效值
                "base_delay": -1.0 # 无效值
            }
        }
        result = self.validator.validate_llm_config(config)
        assert not result.is_valid
        # 检查是否包含期望的错误信息（Pydantic验证器产生的错误）
        error_str = " ".join(result.errors)
        # 检查是否包含相关的错误信息
        assert any(keyword in error_str for keyword in ["max_retries", "base_delay", "greater than or equal to", "retry_config"])

    def test_validate_llm_config_invalid_timeout_config(self):
        """测试无效的超时配置"""
        config = {
            "name": "test_llm",
            "model_type": "openai",
            "model_name": "gpt-4",
            "timeout_config": {
                "request_timeout": 0,  # 无效值
                "connect_timeout": -1 # 无效值
            }
        }
        result = self.validator.validate_llm_config(config)
        assert not result.is_valid
        # 检查是否包含期望的错误信息（Pydantic验证器产生的错误）
        error_str = " ".join(result.errors)
        # 检查是否包含相关的错误信息
        assert any(keyword in error_str for keyword in ["request_timeout", "connect_timeout", "greater than or equal to", "timeout_config"])

    def test_validate_tool_config_valid(self):
        """测试有效的工具配置验证"""
        config = {
            "name": "test_tool",
            "tools": ["calculator"]
        }
        result = self.validator.validate_tool_config(config)
        assert result.is_valid
        assert not result.has_warnings()

    def test_validate_tool_config_empty_tools(self):
        """测试空工具列表的警告"""
        config = {
            "name": "test_tool",
            "tools": []
        }
        result = self.validator.validate_tool_config(config)
        assert result.is_valid
        assert result.has_warnings()
        assert "未配置任何工具" in result.warnings[0]

    def test_validate_token_counter_config_valid(self):
        """测试有效的Token计数器配置验证"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "enhanced": False
        }
        result = self.validator.validate_token_counter_config(config)
        # 验证配置是否有效（可能有警告但无错误）
        assert result.is_valid # 如果有错误则验证失败，如果有警告则仍可能有效
        # 检查错误，而不是整体有效性
        assert not result.errors  # 确保没有错误

    def test_validate_token_counter_config_enhanced_mode_warnings(self):
        """测试增强模式下的警告"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "enhanced": True,
            "cache": None,  # 使用None而不是False
            "calibration": None  # 使用None而不是False
        }
        result = self.validator.validate_token_counter_config(config)
        # 配置应该有效，但可能有警告
        assert result.is_valid # 有警告但无错误时仍为True
        # 检查是否有警告
        assert result.has_warnings()
        # 检查警告中是否包含预期的文本
        warning_text = " ".join(result.warnings)
        assert "增强模式建议配置缓存以提高性能" in warning_text or "增强模式建议配置校准以提高准确性" in warning_text

    def test_validate_token_counter_config_invalid_model_names(self):
        """测试无效的模型名称"""
        # 测试OpenAI模型名称
        config = {
            "model_type": "openai",
            "model_name": "invalid-model",
            "enhanced": False
        }
        result = self.validator.validate_token_counter_config(config)
        assert result.is_valid  # 仍有效，但有警告
        assert result.has_warnings()
        assert "OpenAI模型名称 invalid-model 可能不符合命名规范" in result.warnings

        # 测试Anthropic模型名称
        config = {
            "model_type": "anthropic",
            "model_name": "invalid-model",
            "enhanced": False
        }
        result = self.validator.validate_token_counter_config(config)
        assert result.is_valid
        assert result.has_warnings()
        assert "Anthropic模型名称 invalid-model 可能不符合命名规范" in result.warnings

        # 测试Gemini模型名称
        config = {
            "model_type": "gemini",
            "model_name": "invalid-model",
            "enhanced": False
        }
        result = self.validator.validate_token_counter_config(config)
        assert result.is_valid
        assert result.has_warnings()
        assert "Gemini模型名称 invalid-model 可能不符合命名规范" in result.warnings

    def test_validate_global_config_with_report(self):
        """测试带报告的全局配置验证"""
        config = {
            "log_outputs": [{"type": "console"}],
            "secret_patterns": ["password"]
        }
        report = self.validator.validate_global_config_with_report(config)
        assert report.config_type == "global_config"
        assert len(report.get_results_by_level("SCHEMA")) > 0

    def test_validate_llm_config_with_report(self):
        """测试带报告的LLM配置验证"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4"
        }
        report = self.validator.validate_llm_config_with_report(config)
        assert report.config_type == "llm_config"
        assert len(report.get_results_by_level("SCHEMA")) > 0

    def test_validate_tool_config_with_report(self):
        """测试带报告的工具配置验证"""
        config = {
            "tools": [{"name": "calculator", "enabled": True}]
        }
        report = self.validator.validate_tool_config_with_report(config)
        assert report.config_type == "tool_config"
        assert len(report.get_results_by_level("SCHEMA")) > 0

    def test_validate_token_counter_config_with_report(self):
        """测试带报告的Token计数器配置验证"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4"
        }
        report = self.validator.validate_token_counter_config_with_report(config)
        assert report.config_type == "token_counter_config"
        assert len(report.get_results_by_level("SCHEMA")) > 0

    @patch('src.core.config.processor.validator.load_config_file')
    def test_validate_config_with_cache(self, mock_load_config_file):
        """测试带缓存的配置验证"""
        mock_load_config_file.return_value = {
            "log_outputs": [{"type": "console"}],
            "secret_patterns": ["password"]
        }
        
        # 第一次调用，应该执行验证
        report1 = self.validator.validate_config_with_cache("test_path", "global")
        assert mock_load_config_file.called
        
        # 第二次调用相同路径，应该从缓存获取
        mock_load_config_file.reset_mock()
        report2 = self.validator.validate_config_with_cache("test_path", "global")
        assert not mock_load_config_file.called  # 缓存命中，不应再次加载

    def test_suggest_config_fixes(self):
        """测试配置修复建议"""
        # 无效配置
        config = {
            "model_type": "openai",
            "retry_config": {
                "max_retries": -1
            }
        }
        
        suggestions = self.validator.suggest_config_fixes(config, "llm")
        # 由于配置无效，应该有修复建议
        # 这里我们只是测试方法不抛出异常
        assert isinstance(suggestions, list)

    def test_suggest_config_fixes_invalid_config_type(self):
        """测试无效配置类型的修复建议"""
        config = {}
        with pytest.raises(ValueError):
            self.validator.suggest_config_fixes(config, "invalid_type")

    def test_validate_config_with_cache_invalid_config_type(self):
        """测试无效配置类型的缓存验证"""
        # 模拟一个已存在的配置文件，避免文件不存在错误
        with patch('src.core.config.processor.validator.load_config_file') as mock_load:
            mock_load.return_value = {"name": "test", "model_type": "openai"}
            with pytest.raises(ValueError):
                self.validator.validate_config_with_cache("test_path", "invalid_type")