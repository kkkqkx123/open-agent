"""Token计算装饰器测试"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Optional

from src.services.llm.token_calculation_service import TokenCalculationService
from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    TokenCalculationConfig,
    TokenCostInfo
)


class TestTokenCalculationDecorator:
    """Token计算装饰器测试类"""
    
    @pytest.fixture
    def base_service(self):
        """创建基础Token计算服务"""
        return TokenCalculationService("openai")
    
    @pytest.fixture
    def mock_config_provider(self):
        """创建模拟配置提供者"""
        provider = Mock(spec=ITokenConfigProvider)
        provider.get_token_config.return_value = TokenCalculationConfig(
            provider_name="openai",
            model_name="gpt-4",
            cost_per_input_token=0.01,
            cost_per_output_token=0.02
        )
        provider.get_supported_models.return_value = {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-sonnet"]
        }
        provider.is_model_supported.return_value = True
        return provider
    
    @pytest.fixture
    def mock_cost_calculator(self):
        """创建模拟成本计算器"""
        calculator = Mock(spec=ITokenCostCalculator)
        calculator.calculate_cost.return_value = TokenCostInfo(
            input_tokens=100,
            output_tokens=50,
            input_cost=1.0,
            output_cost=1.0,
            total_cost=2.0,
            currency="USD",
            model_type="openai",
            model_name="gpt-4"
        )
        calculator.get_model_pricing_info.return_value = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "input_token_cost": 0.01,
            "output_token_cost": 0.02
        }
        return calculator
    
    @pytest.fixture
    def decorator(self, base_service, mock_config_provider, mock_cost_calculator):
        """创建装饰器实例"""
        return TokenCalculationDecorator(
            base_service=base_service,
            config_provider=mock_config_provider,
            cost_calculator=mock_cost_calculator
        )
    
    def test_decorator_initialization(self, base_service, mock_config_provider, mock_cost_calculator):
        """测试装饰器初始化"""
        decorator = TokenCalculationDecorator(
            base_service=base_service,
            config_provider=mock_config_provider,
            cost_calculator=mock_cost_calculator
        )
        
        assert decorator.base_service == base_service
        assert decorator.config_provider == mock_config_provider
        assert decorator.cost_calculator == mock_cost_calculator
    
    def test_decorator_initialization_without_cost_calculator(self, base_service, mock_config_provider):
        """测试没有成本计算器的装饰器初始化"""
        with patch('src.services.llm.token_calculation_decorator.ProviderConfigTokenCostCalculator') as mock_calculator_class:
            mock_calculator = Mock(spec=ITokenCostCalculator)
            mock_calculator_class.return_value = mock_calculator
            
            decorator = TokenCalculationDecorator(
                base_service=base_service,
                config_provider=mock_config_provider,
                cost_calculator=None
            )
            
            assert decorator.cost_calculator == mock_calculator
            mock_calculator_class.assert_called_once_with(mock_config_provider)
    
    def test_calculate_tokens_delegates_to_base_service(self, decorator, base_service):
        """测试Token计算委托给基础服务"""
        with patch.object(base_service, 'calculate_tokens', return_value=10) as mock_calculate:
            result = decorator.calculate_tokens("Hello world", "openai", "gpt-4")
            
            assert result == 10
            mock_calculate.assert_called_once_with("Hello world", "openai", "gpt-4")
    
    def test_calculate_messages_tokens_delegates_to_base_service(self, decorator, base_service):
        """测试消息Token计算委托给基础服务"""
        messages = [{"role": "user", "content": "Hello"}]
        with patch.object(base_service, 'calculate_messages_tokens', return_value=5) as mock_calculate:
            result = decorator.calculate_messages_tokens(messages, "openai", "gpt-4")
            
            assert result == 5
            mock_calculate.assert_called_once_with(messages, "openai", "gpt-4")
    
    def test_parse_token_usage_delegates_to_base_service(self, decorator, base_service):
        """测试Token使用解析委托给基础服务"""
        response = {"usage": {"total_tokens": 15}}
        with patch.object(base_service, 'parse_token_usage_from_response') as mock_parse:
            decorator.parse_token_usage_from_response(response, "openai")
            
            mock_parse.assert_called_once_with(response, "openai")
    
    def test_get_processor_stats_delegates_to_base_service(self, decorator, base_service):
        """测试处理器统计获取委托给基础服务"""
        with patch.object(base_service, 'get_processor_stats', return_value={"cache_hits": 10}) as mock_stats:
            result = decorator.get_processor_stats("openai", "gpt-4")
            
            assert result == {"cache_hits": 10}
            mock_stats.assert_called_once_with("openai", "gpt-4")
    
    def test_calculate_cost_with_calculator(self, decorator, mock_cost_calculator):
        """测试有成本计算器时的成本计算"""
        result = decorator.calculate_cost(100, 50, "openai", "gpt-4")
        
        assert result is not None
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_cost == 2.0
        mock_cost_calculator.calculate_cost.assert_called_once_with(100, 50, "openai", "gpt-4")
    
    def test_calculate_cost_without_calculator(self, base_service):
        """测试没有成本计算器时的成本计算"""
        decorator = TokenCalculationDecorator(base_service=base_service)
        
        with patch('src.services.llm.token_calculation_decorator.logger') as mock_logger:
            result = decorator.calculate_cost(100, 50, "openai", "gpt-4")
            
            assert result is None
            mock_logger.warning.assert_called_once_with("未设置成本计算器，无法计算成本")
    
    def test_get_model_pricing_info_with_calculator(self, decorator, mock_cost_calculator):
        """测试有成本计算器时的定价信息获取"""
        result = decorator.get_model_pricing_info("openai", "gpt-4")
        
        assert result is not None
        assert result["model_type"] == "openai"
        assert result["model_name"] == "gpt-4"
        assert result["input_token_cost"] == 0.01
        mock_cost_calculator.get_model_pricing_info.assert_called_once_with("openai", "gpt-4")
    
    def test_get_model_pricing_info_without_calculator(self, base_service):
        """测试没有成本计算器时的定价信息获取"""
        decorator = TokenCalculationDecorator(base_service=base_service)
        
        with patch('src.services.llm.token_calculation_decorator.logger') as mock_logger:
            result = decorator.get_model_pricing_info("openai", "gpt-4")
            
            assert result is None
            mock_logger.warning.assert_called_once_with("未设置成本计算器，无法获取定价信息")
    
    def test_get_supported_models_with_provider(self, decorator, mock_config_provider):
        """测试有配置提供者时的支持模型获取"""
        result = decorator.get_supported_models()
        
        assert result == {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-sonnet"]
        }
        mock_config_provider.get_supported_models.assert_called_once()
    
    def test_get_supported_models_without_provider(self, base_service):
        """测试没有配置提供者时的支持模型获取"""
        decorator = TokenCalculationDecorator(base_service=base_service)
        
        result = decorator.get_supported_models()
        
        assert "openai" in result
        assert "anthropic" in result
        assert "gemini" in result
        assert "gpt-4" in result["openai"]
    
    def test_is_model_supported_with_provider(self, decorator, mock_config_provider):
        """测试有配置提供者时的模型支持检查"""
        result = decorator.is_model_supported("openai", "gpt-4")
        
        assert result is True
        mock_config_provider.is_model_supported.assert_called_once_with("openai", "gpt-4")
    
    def test_is_model_supported_without_provider(self, base_service):
        """测试没有配置提供者时的模型支持检查"""
        decorator = TokenCalculationDecorator(base_service=base_service)
        
        result = decorator.is_model_supported("openai", "gpt-4")
        
        assert result is True
    
    def test_refresh_config_cache_with_provider(self, decorator, mock_config_provider):
        """测试有配置提供者时的配置缓存刷新"""
        with patch('src.services.llm.token_calculation_decorator.logger') as mock_logger:
            decorator.refresh_config_cache()
            
            mock_config_provider.refresh_config_cache.assert_called_once()
            mock_logger.info.assert_called_once_with("Token配置缓存已刷新")
    
    def test_refresh_config_cache_without_provider(self, base_service):
        """测试没有配置提供者时的配置缓存刷新"""
        decorator = TokenCalculationDecorator(base_service=base_service)
        
        with patch('src.services.llm.token_calculation_decorator.logger') as mock_logger:
            decorator.refresh_config_cache()
            
            mock_logger.warning.assert_called_once_with("未设置配置提供者，无法刷新缓存")
    
    def test_get_enhanced_processor_with_provider(self, decorator, mock_config_provider):
        """测试有配置提供者时的增强处理器获取"""
        with patch.object(decorator, '_create_processor_with_config') as mock_create:
            mock_processor = Mock()
            mock_create.return_value = mock_processor
            
            result = decorator.get_enhanced_processor_for_model("openai", "gpt-4")
            
            assert result == mock_processor
            mock_config_provider.get_token_config.assert_called_once_with("openai", "gpt-4")
            mock_create.assert_called_once()
    
    def test_get_enhanced_processor_without_config(self, decorator, mock_config_provider, base_service):
        """测试没有配置时使用基础处理器"""
        mock_config_provider.get_token_config.return_value = None
        
        with patch.object(base_service, '_get_processor_for_model') as mock_get:
            mock_processor = Mock()
            mock_get.return_value = mock_processor
            
            result = decorator.get_enhanced_processor_for_model("openai", "gpt-4")
            
            assert result == mock_processor
            mock_get.assert_called_once_with("openai", "gpt-4")
    
    def test_get_enhanced_processor_without_provider(self, decorator, base_service):
        """测试没有配置提供者时使用基础处理器"""
        decorator._config_provider = None
        
        with patch.object(base_service, '_get_processor_for_model') as mock_get:
            mock_processor = Mock()
            mock_get.return_value = mock_processor
            
            result = decorator.get_enhanced_processor_for_model("openai", "gpt-4")
            
            assert result == mock_processor
            mock_get.assert_called_once_with("openai", "gpt-4")
    
    def test_get_service_status(self, decorator, mock_config_provider, mock_cost_calculator):
        """测试服务状态获取"""
        result = decorator.get_service_status()
        
        assert result["base_service_type"] == "TokenCalculationService"
        assert result["has_config_provider"] is True
        assert result["has_cost_calculator"] is True
        assert result["config_provider_type"] == "Mock"
        assert result["cost_calculator_type"] == "Mock"
        assert "supported_models" in result
    
    def test_set_config_provider(self, base_service):
        """测试设置配置提供者"""
        decorator = TokenCalculationDecorator(base_service=base_service)
        mock_provider = Mock(spec=ITokenConfigProvider)
        
        with patch('src.services.llm.token_calculation_decorator.ProviderConfigTokenCostCalculator') as mock_calculator_class:
            mock_calculator = Mock(spec=ITokenCostCalculator)
            mock_calculator_class.return_value = mock_calculator
            
            decorator.set_config_provider(mock_provider)
            
            assert decorator.config_provider == mock_provider
            assert decorator.cost_calculator == mock_calculator
            mock_calculator_class.assert_called_once_with(mock_provider)
    
    def test_set_cost_calculator(self, base_service):
        """测试设置成本计算器"""
        decorator = TokenCalculationDecorator(base_service=base_service)
        mock_calculator = Mock(spec=ITokenCostCalculator)
        
        decorator.set_cost_calculator(mock_calculator)
        
        assert decorator.cost_calculator == mock_calculator