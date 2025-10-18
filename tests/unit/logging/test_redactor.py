"""日志脱敏器单元测试"""

import pytest

from src.logging.redactor import LogRedactor, CustomLogRedactor
from src.logging.logger import LogLevel


class TestLogRedactor:
    """日志脱敏器测试类"""
    
    def test_default_patterns(self):
        """测试默认模式"""
        redactor = LogRedactor()
        
        # 测试API Key脱敏
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-***"
        
        # 测试邮箱脱敏
        assert redactor.redact("Email: user@example.com") == "Email: ***@***.***"
        
        # 测试手机号脱敏
        assert redactor.redact("Phone: 13812345678") == "Phone: 1*********"
        
        # 测试身份证号脱敏
        assert redactor.redact("ID: 11010519900307234X") == "ID: ***************"
        
        # 测试密码字段脱敏
        assert redactor.redact('{"password": "secret123"}') == '{"password": "***"}'
        assert redactor.redact('password=admin') == 'password=***'
        
        # 测试Token脱敏
        assert redactor.redact('{"token": "abc123def456789"}') == '{"token": "***"}'
        
        # 测试API Key字段脱敏
        assert redactor.redact('{"api_key": "secret123"}') == '{"api_key": "***"}'
        
        # 测试Bearer Token脱敏
        assert redactor.redact("Authorization: Bearer abc123def456") == "Authorization: Bearer ***"
        
        # 测试JWT Token脱敏
        assert redactor.redact("JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c") == "JWT: JWT.***.***"
    
    def test_debug_level_no_redaction(self):
        """测试DEBUG级别不脱敏"""
        redactor = LogRedactor()
        
        sensitive_text = "API Key: sk-abc123def456"
        
        # DEBUG级别不应该脱敏
        assert redactor.redact(sensitive_text, LogLevel.DEBUG) == sensitive_text
        
        # 其他级别应该脱敏
        assert redactor.redact(sensitive_text, LogLevel.INFO) == "API Key: sk-***"
    
    def test_custom_pattern(self):
        """测试自定义模式"""
        redactor = LogRedactor()
        
        # 添加自定义模式
        redactor.add_pattern(r'custom_secret_\d+', 'CUSTOM_SECRET')
        
        # 测试自定义模式
        assert redactor.redact("Secret: custom_secret_12345") == "Secret: CUSTOM_SECRET"
        
        # 测试默认模式仍然有效
        assert redactor.redact("API Key: sk-abc123") == "API Key: sk-***"
    
    def test_remove_pattern(self):
        """测试移除模式"""
        redactor = LogRedactor()
        
        # 移除API Key模式
        removed = redactor.remove_pattern(r'sk-[a-zA-Z0-9]{20,}')
        assert removed is True
        
        # 测试API Key不再被脱敏
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-abc123def456"
        
        # 测试移除不存在的模式
        removed = redactor.remove_pattern(r'nonexistent_pattern')
        assert removed is False
    
    def test_clear_patterns(self):
        """测试清除所有模式"""
        redactor = LogRedactor()
        
        # 清除所有模式
        redactor.clear_patterns()
        
        # 测试没有任何脱敏
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-abc123def456"
        assert redactor.redact("Email: user@example.com") == "Email: user@example.com"
        
        # 测试模式计数
        assert redactor.get_patterns_count() == 0
    
    def test_reset_to_default(self):
        """测试重置为默认模式"""
        redactor = LogRedactor()
        
        # 清除所有模式
        redactor.clear_patterns()
        assert redactor.get_patterns_count() == 0
        
        # 重置为默认模式
        redactor.reset_to_default()
        assert redactor.get_patterns_count() > 0
        
        # 测试默认模式恢复
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-***"
    
    def test_hash_sensitive(self):
        """测试敏感信息哈希处理"""
        redactor = LogRedactor(hash_sensitive=True)
        
        # 测试哈希替换
        result = redactor.redact("API Key: sk-abc123def4567890123456")
        
        # 应该包含原始部分和哈希部分
        assert "sk-" in result
        assert result != "API Key: sk-***"
        assert len(result) > len("API Key: sk-***")
        
        # 相同的敏感信息应该产生相同的哈希
        result2 = redactor.redact("API Key: sk-abc123def4567890123456")
        assert result == result2
    
    def test_set_hash_sensitive(self):
        """测试设置哈希敏感信息"""
        redactor = LogRedactor()
        
        # 默认不使用哈希
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-***"
        
        # 启用哈希
        redactor.set_hash_sensitive(True)
        result = redactor.redact("API Key: sk-abc123def456")
        assert result != "API Key: sk-***"
        
        # 禁用哈希
        redactor.set_hash_sensitive(False)
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-***"
    
    def test_test_redaction(self):
        """测试脱敏效果测试"""
        redactor = LogRedactor()
        
        # 测试包含敏感信息的文本
        test_text = "API Key: sk-abc123def456 and Email: user@example.com"
        result = redactor.test_redaction(test_text)
        
        # 验证测试结果
        assert result['original'] == test_text
        assert result['redacted'] != test_text
        assert result['has_changes'] is True
        assert len(result['matched_patterns']) > 0
        
        # 验证匹配的模式
        pattern_names = [p['pattern'] for p in result['matched_patterns']]
        assert any('sk-' in name for name in pattern_names)
        assert any('@' in name for name in pattern_names)
        
        # 测试不包含敏感信息的文本
        normal_text = "This is a normal message"
        result = redactor.test_redaction(normal_text)
        
        assert result['original'] == normal_text
        assert result['redacted'] == normal_text
        assert result['has_changes'] is False
        assert len(result['matched_patterns']) == 0


class TestCustomLogRedactor:
    """自定义日志脱敏器测试类"""
    
    def test_init_with_config(self):
        """测试使用配置初始化"""
        config = {
            'hash_sensitive': True,
            'patterns': [
                {
                    'pattern': r'custom_secret_\d+',
                    'replacement': 'CUSTOM_SECRET'
                }
            ]
        }
        
        redactor = CustomLogRedactor(config)
        
        # 测试配置生效
        assert redactor.hash_sensitive is True
        
        # 测试自定义模式
        result = redactor.redact("Secret: custom_secret_12345")
        assert result == "Secret: CUSTOM_SECRET"
    
    def test_update_config(self):
        """测试更新配置"""
        redactor = CustomLogRedactor()
        
        # 默认配置
        assert redactor.hash_sensitive is False
        
        # 更新配置
        new_config = {
            'hash_sensitive': True,
            'patterns': [
                {
                    'pattern': r'new_pattern_\w+',
                    'replacement': 'NEW_REPLACEMENT'
                }
            ]
        }
        
        redactor.update_config(new_config)
        
        # 测试配置更新
        assert redactor.hash_sensitive is True
        
        # 测试新模式
        result = redactor.redact("Match: new_pattern_test")
        assert result == "Match: NEW_REPLACEMENT"
        
        # 测试默认模式被清除
        result = redactor.redact("API Key: sk-abc123def456")
        assert result == "API Key: sk-abc123def456"  # 不应该被脱敏
    
    def test_empty_config(self):
        """测试空配置"""
        redactor = CustomLogRedactor({})
        
        # 应该使用默认模式
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-***"
    
    def test_none_config(self):
        """测试None配置"""
        redactor = CustomLogRedactor(None)
        
        # 应该使用默认模式
        assert redactor.redact("API Key: sk-abc123def456") == "API Key: sk-***"