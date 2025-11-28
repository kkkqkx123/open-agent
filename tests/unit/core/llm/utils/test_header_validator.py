"""HeaderValidator单元测试"""

import os
from src.core.llm.utils.header_validator import HeaderValidator, HeaderProcessor


class TestHeaderValidator:
    """HeaderValidator测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.validator = HeaderValidator()
        self.processor = HeaderProcessor(validator=self.validator)
    
    def test_allowed_headers_contains_common_headers(self):
        """测试白名单包含常用标头"""
        allowed_headers = self.validator.ALLOWED_HEADERS
        
        # 检查关键标头是否在白名单中
        assert "authorization" in allowed_headers
        assert "x-api-key" in allowed_headers
        assert "user-agent" in allowed_headers
        assert "content-type" in allowed_headers
        assert "x-custom-header" in allowed_headers
        
        # 检查总数是否符合预期（23个标头）
        assert len(allowed_headers) == 23
    
    def test_sensitive_headers_contains_only_truly_sensitive(self):
        """测试敏感标头只包含真正的敏感标头"""
        sensitive_headers = self.validator.SENSITIVE_HEADERS
        
        # 检查真正的敏感标头
        assert "authorization" in sensitive_headers
        assert "x-api-key" in sensitive_headers
        
        # 确保只有这两个标头是敏感的
        assert sensitive_headers == {"authorization", "x-api-key"}
    
    def test_valid_non_sensitive_headers_pass_validation(self):
        """测试有效的非敏感标头能通过验证"""
        headers = {
            "user-agent": "Test Agent",
            "content-type": "application/json",
            "accept": "application/json",
            "x-custom-header": "custom-value"
        }
        
        is_valid, errors = self.validator.validate_headers(headers)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_sensitive_headers_with_env_vars_pass_validation(self):
        """测试使用环境变量格式的敏感标头能通过验证"""
        # 设置测试环境变量
        os.environ['TEST_TOKEN'] = 'test_token_value'
        os.environ['TEST_API_KEY'] = 'test_api_key_value'
        
        headers = {
            "authorization": "Bearer ${TEST_TOKEN}",
            "x-api-key": "${TEST_API_KEY}"
        }
        
        is_valid, errors = self.validator.validate_headers(headers)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_sensitive_headers_without_env_vars_fail_validation(self):
        """测试不使用环境变量格式的敏感标头会验证失败"""
        headers = {
            "authorization": "Bearer actual_token_here",
            "x-api-key": "actual_api_key_here"
        }
        
        is_valid, errors = self.validator.validate_headers(headers)
        assert is_valid is False
        assert len(errors) == 2  # 两个标头都失败
        assert "Authorization标头的token必须使用环境变量引用格式" in errors[0]
        assert "敏感标头 'x-api-key' 必须使用环境变量引用格式" in errors[1]
    
    def test_non_whitelisted_headers_fail_validation(self):
        """测试不在白名单中的标头会验证失败"""
        headers = {
            "x-forbidden-header": "forbidden-value"
        }
        
        is_valid, errors = self.validator.validate_headers(headers)
        assert is_valid is False
        assert len(errors) == 1
        assert "不在白名单中" in errors[0]
    
    def test_mixed_valid_and_invalid_headers_validation(self):
        """测试混合有效和无效标头的验证"""
        os.environ['TEST_TOKEN'] = 'test_token_value'
        
        headers = {
            "user-agent": "Test Agent",  # 有效
            "content-type": "application/json",  # 有效
            "authorization": "Bearer ${TEST_TOKEN}",  # 有效（环境变量格式）
            "x-forbidden-header": "forbidden-value"  # 无效
        }
        
        is_valid, errors = self.validator.validate_headers(headers)
        assert is_valid is False
        assert len(errors) == 1
        assert "x-forbidden-header" in errors[0]
    
    def test_header_sanitization(self):
        """测试标头脱敏功能"""
        os.environ['TEST_TOKEN'] = 'test_token_value'
        os.environ['TEST_API_KEY'] = 'test_api_key_value'
        
        headers = {
            "user-agent": "Test Agent",
            "authorization": "Bearer ${TEST_TOKEN}",
            "x-api-key": "${TEST_API_KEY}",
            "content-type": "application/json"
        }
        
        sanitized = self.validator.sanitize_headers_for_logging(headers)
        
        # 非敏感标头保持不变
        assert sanitized["user-agent"] == "Test Agent"
        assert sanitized["content-type"] == "application/json"
        
        # 敏感标头被脱敏
        assert sanitized["authorization"] == "***"
        assert sanitized["x-api-key"] == "***"
    
    def test_header_resolution_with_env_vars(self):
        """测试标头环境变量解析功能"""
        os.environ['TEST_TOKEN'] = 'resolved_token_value'
        os.environ['TEST_API_KEY'] = 'resolved_api_key_value'
        
        headers = {
            "authorization": "Bearer ${TEST_TOKEN}",
            "x-api-key": "${TEST_API_KEY}",
            "user-agent": "Test Agent"
        }
        
        resolved = self.validator.resolve_headers(headers)
        
        assert resolved["authorization"] == "Bearer resolved_token_value"
        assert resolved["x-api-key"] == "resolved_api_key_value"
        assert resolved["user-agent"] == "Test Agent"
    
    def test_header_resolution_with_nonexistent_env_vars(self):
        """测试不存在环境变量的解析"""
        headers = {
            "authorization": "Bearer ${NONEXISTENT_TOKEN}",
            "x-api-key": "${NONEXISTENT_API_KEY}"
        }
        
        resolved = self.validator.resolve_headers(headers)
        
        # 不存在的环境变量应该使用默认值（空字符串）
        assert resolved["authorization"] == "Bearer "
        assert resolved["x-api-key"] == ""
    
    def test_header_processor_integration(self):
        """测试HeaderProcessor集成"""
        os.environ['TEST_TOKEN'] = 'test_token_value'
        
        headers = {
            "user-agent": "Test Agent",
            "authorization": "Bearer ${TEST_TOKEN}"
        }
        
        resolved, sanitized, is_valid, errors = self.processor.process_headers(headers)
        
        assert is_valid is True
        assert len(errors) == 0
        assert resolved["user-agent"] == "Test Agent"
        assert resolved["authorization"] == "Bearer test_token_value"
        assert sanitized["user-agent"] == "Test Agent"
        assert sanitized["authorization"] == "***"
    
    def test_authorization_format_validation(self):
        """测试Authorization标头格式验证"""
        # 有效的Bearer格式
        assert self.validator.validate_authorization_format("Bearer token") is True
        assert self.validator.validate_authorization_format("bearer token") is True  # 不区分大小写
        
        # 无效的格式
        assert self.validator.validate_authorization_format("Bearer") is False  # 没有token
        assert self.validator.validate_authorization_format("") is False
        assert self.validator.validate_authorization_format("Invalid token") is True  # 其他格式认为有效