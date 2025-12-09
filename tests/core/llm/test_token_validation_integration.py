"""Token验证集成测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.llm.clients.base import BaseLLMClient
from src.core.llm.config import LLMClientConfig
from src.interfaces.llm.exceptions import LLMTokenLimitError


class TestableLLMClient(BaseLLMClient):
    """可测试的LLM客户端实现"""
    
    async def _do_generate_async(self, messages, parameters, **kwargs):
        """实现抽象方法"""
        from src.infrastructure.llm.models import TokenUsage
        return self._create_response(
            content="Test response",
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
        )
    
    async def _do_stream_generate_async(self, messages, parameters, **kwargs):
        """实现抽象方法"""
        yield "Test"
        yield " "
        yield "response"
    
    def supports_function_calling(self):
        """实现抽象方法"""
        return True


class TestTokenValidationIntegration:
    """Token验证集成测试类"""
    
    def setup_method(self):
        """设置测试方法"""
        self.config = LLMClientConfig(
            model_type="openai",
            model_name="gpt-3.5-turbo",
            max_tokens=100
        )
        
        # 创建一个可测试的客户端实例
        self.client = TestableLLMClient(self.config)
        
        # 创建模拟消息
        self.mock_messages = [
            Mock(content="Hello", type="human"),
            Mock(content="How are you?", type="human"),
            Mock(content="This is a test message.", type="human")
        ]
    
    def test_token_validation_service_integration(self):
        """测试与TokenCalculationService的集成"""
        # Mock TokenCalculationService
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 50
        
        with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
            # 调用验证方法
            self.client._validate_token_limit(self.mock_messages)
            
            # 验证服务被正确调用
            mock_service.calculate_messages_tokens.assert_called_once_with(
                self.mock_messages, "openai", "gpt-3.5-turbo"
            )
    
    def test_token_limit_exceeded_raises_exception(self):
        """测试token超限抛出异常"""
        # Mock TokenCalculationService返回超过限制的token数量
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 150
        
        with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
            # 应该抛出LLMTokenLimitError
            with pytest.raises(LLMTokenLimitError) as exc_info:
                self.client._validate_token_limit(self.mock_messages)
            
            # 验证异常信息
            error = exc_info.value
            assert error.token_count == 150
            assert error.limit == 100
            assert error.model_name == "gpt-3.5-turbo"
            assert "Token数量超过限制: 150 > 100" in error.message
    
    def test_token_service_unhandled_gracefully(self):
        """测试TokenCalculationService不可用时的优雅处理"""
        # Mock服务抛出异常
        with patch('src.services.history.injection.get_token_calculation_service', side_effect=Exception("Service unavailable")):
            with patch('builtins.print') as mock_print:
                # 应该不会抛出异常，而是打印警告
                self.client._validate_token_limit(self.mock_messages)
                
                # 验证警告被打印
                mock_print.assert_called_once()
                assert "Warning: Token验证失败" in mock_print.call_args[0][0]
    
    def test_token_calculation_error_handled_gracefully(self):
        """测试token计算错误时的优雅处理"""
        # Mock服务存在但计算失败
        mock_service = Mock()
        mock_service.calculate_messages_tokens.side_effect = Exception("Calculation failed")
        
        with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
            with patch('builtins.print') as mock_print:
                # 应该不会抛出异常，而是打印警告
                self.client._validate_token_limit(self.mock_messages)
                
                # 验证警告被打印
                mock_print.assert_called_once()
                assert "Warning: Token验证失败" in mock_print.call_args[0][0]
    
    def test_no_max_tokens_skips_validation(self):
        """测试没有设置max_tokens时跳过验证"""
        # 设置max_tokens为None
        self.client.config.max_tokens = None
        
        # Mock服务（不应该被调用）
        mock_service = Mock()
        
        with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
            # 调用验证方法
            self.client._validate_token_limit(self.mock_messages)
            
            # 验证服务没有被调用
            mock_service.calculate_messages_tokens.assert_not_called()
    
    def test_different_model_types(self):
        """测试不同模型类型的token验证"""
        test_cases = [
            ("openai", "gpt-4"),
            ("anthropic", "claude-3"),
            ("gemini", "gemini-pro"),
            ("mock", "test-model")
        ]
        
        for model_type, model_name in test_cases:
            # 更新配置
            self.client.config.model_type = model_type
            self.client.config.model_name = model_name
            
            # Mock服务
            mock_service = Mock()
            mock_service.calculate_messages_tokens.return_value = 50
            
            with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
                # 调用验证方法
                self.client._validate_token_limit(self.mock_messages)
                
                # 验证服务被正确调用
                mock_service.calculate_messages_tokens.assert_called_with(
                    self.mock_messages, model_type, model_name
                )
                
                # 重置mock
                mock_service.reset_mock()
    
    def test_edge_case_zero_tokens(self):
        """测试0个token的边界情况"""
        # Mock服务返回0个token
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 0
        
        with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
            # 应该不会抛出异常
            self.client._validate_token_limit(self.mock_messages)
    
    def test_edge_case_exact_limit(self):
        """测试token数量正好等于限制的边界情况"""
        # Mock服务返回正好等于限制的token数量
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 100
        
        with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
            # 应该不会抛出异常
            self.client._validate_token_limit(self.mock_messages)
    
    def test_edge_case_one_over_limit(self):
        """测试token数量超过限制1个的边界情况"""
        # Mock服务返回超过限制1个token
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 101
        
        with patch('src.services.history.injection.get_token_calculation_service', return_value=mock_service):
            # 应该抛出异常
            with pytest.raises(LLMTokenLimitError) as exc_info:
                self.client._validate_token_limit(self.mock_messages)
            
            # 验证异常信息
            error = exc_info.value
            assert error.token_count == 101
            assert error.limit == 100