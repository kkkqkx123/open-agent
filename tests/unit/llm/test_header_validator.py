"""HTTP标头验证器测试"""

import os
import pytest
from unittest.mock import patch

from src.llm.header_validator import HeaderValidator, HeaderProcessor
from src.llm.exceptions import LLMConfigurationError


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


class TestHeaderIntegration:
    """HTTP标头集成测试"""
    
    def test_llm_config_header_validation(self):
        """测试LLM配置标头验证"""
        from src.config.models.llm_config import LLMConfig
        
        # 有效配置
        valid_config = {
            'model_type': 'openai',
            'model_name': 'gpt-4',
            'api_key': '${OPENAI_API_KEY}',
            'headers': {
                'User-Agent': 'ModularAgent/1.0',
                'X-Custom-Header': 'custom-value'
            }
        }
        
        config = LLMConfig(**valid_config)
        assert config.model_type == 'openai'
        assert config.model_name == 'gpt-4'
    
    def test_llm_config_header_validation_failure(self):
        """测试LLM配置标头验证失败"""
        from src.config.models.llm_config import LLMConfig
        
        # 无效配置
        invalid_config = {
            'model_type': 'openai',
            'model_name': 'gpt-4',
            'api_key': '${OPENAI_API_KEY}',
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer hardcoded-token'
            }
        }
        
        with pytest.raises(ValueError, match="HTTP标头验证失败"):
            LLMConfig(**invalid_config)
    
    def test_llm_client_config_header_validation(self):
        """测试LLM客户端配置标头验证"""
        from src.llm.config import LLMClientConfig
        
        # 有效配置
        valid_config = LLMClientConfig(
            model_type='openai',
            model_name='gpt-4',
            api_key='${OPENAI_API_KEY}',
            headers={
                'User-Agent': 'ModularAgent/1.0',
                'X-Custom-Header': 'custom-value'
            }
        )
        
        is_valid, errors = valid_config.validate_headers()
        assert is_valid
        assert len(errors) == 0
        
        # 测试解析后的标头
        resolved = valid_config.get_resolved_headers()
        assert 'User-Agent' in resolved
        assert 'X-Custom-Header' in resolved
        
        # 测试脱敏后的标头
        sanitized = valid_config.get_sanitized_headers()
        assert sanitized['User-Agent'] == 'ModularAgent/1.0'
        assert sanitized['X-Custom-Header'] == 'custom-value'