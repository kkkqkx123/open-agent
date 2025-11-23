"""Redactor单元测试"""

import json
import re
from src.core.common.utils.redactor import Redactor, LogLevel


class TestRedactor:
    """Redactor测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        redactor = Redactor()
        
        assert redactor.replacement == "***"
        assert len(redactor._patterns) > 0  # 应该有默认模式

    def test_init_custom_patterns(self):
        """测试自定义模式初始化"""
        custom_patterns = [r'\b\d{4}-\d{4}-\d{4}-\d{4}\b']  # 信用卡模式
        redactor = Redactor(patterns=custom_patterns)
        
        assert len(redactor._patterns) == 1
        assert redactor._patterns[0].pattern == r'\b\d{4}-\d{4}-\d{4}-\d{4}\b'

    def test_init_custom_replacement(self):
        """测试自定义替换字符串"""
        redactor = Redactor(replacement="XXXX")
        assert redactor.replacement == "XXXX"

    def test_add_pattern(self):
        """测试添加自定义模式"""
        redactor = Redactor()
        
        # 添加模式
        redactor.add_pattern("credit_card", r'\b\d{4}-\d{4}-\d{4}-\d{4}\b')
        
        assert "credit_card" in redactor._custom_patterns
        assert redactor._custom_patterns["credit_card"].pattern == r'\b\d{4}-\d{4}-\d{4}-\d{4}\b'

    def test_add_pattern_invalid_regex(self):
        """测试添加无效正则表达式模式"""
        redactor = Redactor()
        
        try:
            redactor.add_pattern("invalid", r'[invalid_regex')  # 无效的正则表达式
            assert False, "应该抛出ValueError异常"
        except ValueError:
            pass  # 期望抛出异常

    def test_remove_pattern(self):
        """测试移除自定义模式"""
        redactor = Redactor()
        redactor.add_pattern("test_pattern", r'\btest\b')
        
        # 移除模式
        result = redactor.remove_pattern("test_pattern")
        assert result is True
        assert "test_pattern" not in redactor._custom_patterns

        # 移除不存在的模式
        result = redactor.remove_pattern("nonexistent")
        assert result is False

    def test_redact_api_key(self):
        """测试脱敏API密钥"""
        redactor = Redactor()
        
        text_with_api_key = "使用API密钥sk-1234567890abcdef进行调用"
        result = redactor.redact(text_with_api_key)
        
        assert "sk-1234567890abcdef" not in result
        assert "***" in result

    def test_redact_email(self):
        """测试脱敏邮箱"""
        redactor = Redactor()
        
        text_with_email = "请联系test@example.com获取更多信息"
        result = redactor.redact(text_with_email)
        
        assert "test@example.com" not in result
        assert "***" in result

    def test_redact_phone(self):
        """测试脱敏手机号"""
        redactor = Redactor()
        
        text_with_phone = "联系电话13812345678"
        result = redactor.redact(text_with_phone)
        
        assert "13812345678" not in result
        assert "***" in result

    def test_redact_password(self):
        """测试脱敏密码字段"""
        redactor = Redactor()
        
        text_with_password = '配置: {"password": "secret123", "user": "admin"}'
        result = redactor.redact(text_with_password)
        
        assert "secret123" not in result
        assert "***" in result

    def test_redact_debug_level(self):
        """测试DEBUG级别不脱敏"""
        redactor = Redactor()
        
        sensitive_text = "API密钥: sk-1234567890"
        result = redactor.redact(sensitive_text, level=LogLevel.DEBUG)
        
        assert result == sensitive_text  # DEBUG级别不应脱敏

    def test_redact_info_level(self):
        """测试INFO级别脱敏"""
        redactor = Redactor()
        
        sensitive_text = "API密钥: sk-1234567890"
        result = redactor.redact(sensitive_text, level=LogLevel.INFO)
        
        assert "sk-1234567890" not in result
        assert "***" in result

    def test_redact_dict_simple(self):
        """测试脱敏简单字典"""
        redactor = Redactor()
        
        data = {
            "api_key": "sk-1234567890",
            "email": "test@example.com",
            "name": "John Doe"
        }
        
        result = redactor.redact_dict(data)
        
        assert result["api_key"] == "***"
        assert result["email"] == "***"
        assert result["name"] == "John Doe"  # 非敏感信息保持不变

    def test_redact_dict_nested(self):
        """测试脱敏嵌套字典"""
        redactor = Redactor()
        
        data = {
            "user": {
                "email": "test@example.com",
                "password": "secret123"
            },
            "config": {
                "api_key": "sk-1234567890",
                "settings": {
                    "token": "Bearer token123"
                }
            }
        }
        
        result = redactor.redact_dict(data)
        
        assert result["user"]["email"] == "***"
        assert result["user"]["password"] == "***"
        assert result["config"]["api_key"] == "***"
        assert result["config"]["settings"]["token"] == "***"

    def test_redact_list(self):
        """测试脱敏列表"""
        redactor = Redactor()
        
        data = [
            "email1@example.com",
            "sk-1234567890",
            "normal_string"
        ]
        
        result = redactor.redact_list(data)
        
        assert result[0] == "***"
        assert result[1] == "***"
        assert result[2] == "normal_string"  # 非敏感信息保持不变

    def test_redact_list_with_dicts(self):
        """测试脱敏包含字典的列表"""
        redactor = Redactor()
        
        data = [
            {"email": "test@example.com", "name": "John"},
            {"api_key": "sk-1234567890", "type": "api"}
        ]
        
        result = redactor.redact_list(data)
        
        assert result[0]["email"] == "***"
        assert result[0]["name"] == "John"
        assert result[1]["api_key"] == "***"
        assert result[1]["type"] == "api"

    def test_redact_json(self):
        """测试脱敏JSON字符串"""
        redactor = Redactor()
        
        json_str = '{"email": "test@example.com", "api_key": "sk-1234567890", "name": "John"}'
        result = redactor.redact_json(json_str)
        
        # 解析脱敏后的JSON
        parsed = json.loads(result)
        assert parsed["email"] == "***"
        assert parsed["api_key"] == "***"
        assert parsed["name"] == "John"

    def test_redact_json_invalid(self):
        """测试脱敏无效JSON字符串"""
        redactor = Redactor()
        
        invalid_json = 'email: test@example.com, api_key: sk-1234567890'
        result = redactor.redact_json(invalid_json)
        
        # 对于无效JSON，应该直接对字符串进行脱敏
        assert "***" in result

    def test_is_sensitive(self):
        """测试检测敏感信息"""
        redactor = Redactor()
        
        # 包含敏感信息的文本
        sensitive_text = "API密钥: sk-1234567890"
        assert redactor.is_sensitive(sensitive_text) is True
        
        # 不包含敏感信息的文本
        non_sensitive_text = "这是一般文本"
        assert redactor.is_sensitive(non_sensitive_text) is False

    def test_get_sensitive_parts(self):
        """测试获取敏感信息部分"""
        redactor = Redactor()
        
        text = "邮箱: test@example.com, 电话: 13812345678, API: sk-1234567890"
        sensitive_parts = redactor.get_sensitive_parts(text)
        
        # 验证检测到的敏感信息
        assert any("test@example.com" in part for part in sensitive_parts)
        assert any("13812345678" in part for part in sensitive_parts)
        assert any("sk-1234567890" in part for part in sensitive_parts)

    def test_get_pattern_names(self):
        """测试获取模式名称"""
        redactor = Redactor()
        
        # 添加自定义模式
        redactor.add_pattern("test1", r'\btest1\b')
        redactor.add_pattern("test2", r'\btest2\b')
        
        names = redactor.get_pattern_names()
        assert "test1" in names
        assert "test2" in names

    def test_set_replacement(self):
        """测试设置替换字符串"""
        redactor = Redactor()
        
        # 测试默认替换
        text = "API密钥: sk-1234567890"
        result = redactor.redact(text)
        assert "***" in result
        
        # 更换替换字符串
        redactor.set_replacement("REDACTED")
        result = redactor.redact(text)
        assert "REDACTED" in result
        assert "***" not in result

    def test_clear_patterns(self):
        """测试清除自定义模式"""
        redactor = Redactor()
        
        # 添加自定义模式
        redactor.add_pattern("test", r'\btest\b')
        assert len(redactor._custom_patterns) == 1
        
        # 清除模式
        redactor.clear_patterns()
        assert len(redactor._custom_patterns) == 0

    def test_reset_to_defaults(self):
        """测试重置为默认模式"""
        redactor = Redactor()
        
        # 添加自定义模式
        redactor.add_pattern("custom", r'\bcustom\b')
        original_default_count = len(redactor._patterns)
        
        # 重置为默认
        redactor.reset_to_defaults()
        
        # 验证自定义模式被清除
        assert len(redactor._custom_patterns) == 0
        # 验证默认模式恢复
        assert len(redactor._patterns) == original_default_count

    def test_redact_with_custom_pattern(self):
        """测试使用自定义模式脱敏"""
        redactor = Redactor()
        
        # 添加自定义模式匹配特定格式
        redactor.add_pattern("custom_format", r'\bCUSTOM-\d{4}\b')
        
        text = "编号: CUSTOM-1234, API: sk-1234567890"
        result = redactor.redact(text)
        
        assert "CUSTOM-1234" not in result
        assert "sk-1234567890" not in result
        assert result.count("***") == 2  # 两个敏感信息都被脱敏

    def test_redact_dict_non_recursive(self):
        """测试非递归脱敏字典"""
        redactor = Redactor()
        
        data = {
            "level1": {
                "email": "test@example.com",  # 这个不应该被脱敏，因为非递归
                "value": "normal"
            },
            "api_key": "sk-1234567890"  # 这个应该被脱敏
        }
        
        result = redactor.redact_dict(data, recursive=False)
        
        # 顶层敏感信息被脱敏
        assert result["api_key"] == "***"
        # 嵌套字典不被处理（非递归）
        assert result["level1"]["email"] == "test@example.com"