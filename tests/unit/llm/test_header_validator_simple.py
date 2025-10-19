"""HTTP标头验证器简化测试"""

import os
import sys
import pytest
from unittest.mock import patch

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from src.llm.header_validator import HeaderValidator, HeaderProcessor


class TestHeaderValidator:
    """HTTP标头验证器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.validator = HeaderValidator()
    
    def test_allowed_headers(self):
        """测试允许的标头"""
        allowed_headers = {
            'X-API-Key': '${API_KEY}',
            'User-Agent': 'ModularAgent/1.0',
            'Authorization': 'Bearer ${TOKEN}',
            'X-Custom-Header': 'custom-value'
        }
        
        is_valid, errors = self.validator.validate_headers(allowed_headers)
        assert is_valid
        assert len(errors) == 0
    
    def test_disallowed_headers(self):
        """测试不允许的标头"""
        disallowed_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Forbidden': 'value'
        }
        
        is_valid, errors = self.validator.validate_headers(disallowed_headers)
        assert not is_valid
        assert len(errors) == 3
        assert "Content-Type" in errors[0]
        assert "Accept" in errors[1]
        assert "X-Forbidden" in errors[2]
    
    def test_sensitive_headers_without_env_var(self):
        """测试敏感标头未使用环境变量引用"""
        sensitive_headers = {
            'Authorization': 'Bearer hardcoded-token',
            'X-API-Key': 'hardcoded-key'
        }
        
        is_valid, errors = self.validator.validate_headers(sensitive_headers)
        assert not is_valid
        assert len(errors) == 2
        assert "环境变量引用" in errors[0]
        assert "环境变量引用" in errors[1]
    
    def test_sensitive_headers_with_env_var(self):
        """测试敏感标头使用环境变量引用"""
        sensitive_headers = {
            'Authorization': 'Bearer ${AUTH_TOKEN}',
            'X-API-Key': '${API_KEY}'
        }
        
        is_valid, errors = self.validator.validate_headers(sensitive_headers)
        assert is_valid
        assert len(errors) == 0
    
    def test_env_var_pattern(self):
        """测试环境变量引用模式"""
        # 有效模式
        assert self.validator._is_env_var_reference('${ENV_VAR}')
        assert self.validator._is_env_var_reference('${ENV_VAR:default}')
        assert self.validator._is_env_var_reference('${ENV_VAR:default value}')
        
        # 无效模式
        assert not self.validator._is_env_var_reference('ENV_VAR')
        assert not self.validator._is_env_var_reference('${ENV_VAR')
        assert not self.validator._is_env_var_reference('ENV_VAR}')
        assert not self.validator._is_env_var_reference('${}')
    
    def test_extract_env_var_name(self):
        """测试提取环境变量名称"""
        assert self.validator._extract_env_var_name('${API_KEY}') == 'API_KEY'
        assert self.validator._extract_env_var_name('${API_KEY:default}') == 'API_KEY'
        assert self.validator._extract_env_var_name('API_KEY') is None
    
    @patch.dict(os.environ, {'TEST_VAR': 'test_value'})
    def test_resolve_env_var(self):
        """测试解析环境变量"""
        # 存在的环境变量
        assert self.validator._resolve_env_var('${TEST_VAR}') == 'test_value'
        
        # 带默认值的环境变量
        assert self.validator._resolve_env_var('${NON_EXISTENT:default}') == 'default'
        
        # 不存在的环境变量
        assert self.validator._resolve_env_var('${NON_EXISTENT}') == ''
    
    def test_authorization_format_validation(self):
        """测试Authorization标头格式验证"""
        # Bearer格式
        assert self.validator.validate_authorization_format('Bearer token123')
        assert not self.validator.validate_authorization_format('Bearer')
        
        # 其他格式
        assert self.validator.validate_authorization_format('Basic token123')
        assert self.validator.validate_authorization_format('token123')
        assert not self.validator.validate_authorization_format('')
    
    def test_sanitize_headers_for_logging(self):
        """测试标头脱敏"""
        headers = {
            'Authorization': 'Bearer secret-token',
            'X-API-Key': 'secret-key',
            'User-Agent': 'ModularAgent/1.0',
            'X-Custom-Header': '${CUSTOM_VAR}'
        }
        
        sanitized = self.validator.sanitize_headers_for_logging(headers)
        
        assert sanitized['Authorization'] == '***'
        assert sanitized['X-API-Key'] == '***'
        assert sanitized['User-Agent'] == 'ModularAgent/1.0'
        assert sanitized['X-Custom-Header'] == '${***}'


class TestHeaderProcessor:
    """HTTP标头处理器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.processor = HeaderProcessor()
    
    @patch.dict(os.environ, {'API_KEY': 'secret-api-key', 'TOKEN': 'secret-token'})
    def test_process_headers_success(self):
        """测试成功处理标头"""
        headers = {
            'X-API-Key': '${API_KEY}',
            'User-Agent': 'ModularAgent/1.0',
            'Authorization': 'Bearer ${TOKEN}'
        }
        
        resolved, sanitized, is_valid, errors = self.processor.process_headers(headers)
        
        assert is_valid
        assert len(errors) == 0
        assert resolved['X-API-Key'] == 'secret-api-key'
        assert resolved['User-Agent'] == 'ModularAgent/1.0'
        assert resolved['Authorization'] == 'Bearer secret-token'
        
        assert sanitized['X-API-Key'] == '***'
        assert sanitized['User-Agent'] == 'ModularAgent/1.0'
        assert sanitized['Authorization'] == '***'
    
    def test_process_headers_failure(self):
        """测试处理标头失败"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer hardcoded-token'
        }
        
        resolved, sanitized, is_valid, errors = self.processor.process_headers(headers)
        
        assert not is_valid
        assert len(errors) == 2
        assert resolved == {}
        assert sanitized['Content-Type'] == 'application/json'
        assert sanitized['Authorization'] == '***'
    
    def test_get_allowed_headers(self):
        """测试获取允许的标头列表"""
        allowed = self.processor.get_allowed_headers()
        assert 'x-api-key' in allowed
        assert 'user-agent' in allowed
        assert 'authorization' in allowed
        assert 'x-custom-header' in allowed
        assert len(allowed) == 4
    
    def test_get_sensitive_headers(self):
        """测试获取敏感标头列表"""
        sensitive = self.processor.get_sensitive_headers()
        assert 'authorization' in sensitive
        assert 'x-api-key' in sensitive
        assert len(sensitive) == 2


if __name__ == "__main__":
    pytest.main([__file__])