"""Token配置提供者测试"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.services.llm.config.token_config_provider import (
    ProviderConfigTokenConfigProvider,
    ProviderConfigTokenCostCalculator
)
from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    TokenCalculationConfig,
    TokenCostInfo
)


class TestProviderConfigTokenConfigProvider:
    """Provider配置Token配置提供者测试类"""
    
    @pytest.fixture
    def mock_provider_discovery(self):
        """创建模拟Provider配置发现器"""
        discovery = Mock()
        discovery.get_provider_config.return_value = {
            "token_calculation": {
                "type": "openai",
                "custom_tokenizer": None,
                "fallback_enabled": True,
                "cache_enabled": True
            },
            "pricing": {
                "input_token_cost": 0.01,
                "output_token_cost": 0.02
            },
            "tokenizer": {
                "model": "gpt-4"
            }
        }
        discovery.list_all_models.return_value = {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-sonnet"]
        }
        discovery.validate_provider_config.return_value = True
        return discovery
    
    @pytest.fixture
    def config_provider(self, mock_provider_discovery):
        """创建配置提供者实例"""
        return ProviderConfigTokenConfigProvider(mock_provider_discovery)
    
    def test_initialization(self, mock_provider_discovery):
        """测试初始化"""
        provider = ProviderConfigTokenConfigProvider(mock_provider_discovery)
        
        assert provider._provider_discovery == mock_provider_discovery
        assert provider._config_cache == {}
    
    def test_get_token_config_from_cache(self, config_provider):
        """测试从缓存获取配置"""
        # 预先设置缓存
        config = TokenCalculationConfig(
            provider_name="openai",
            model_name="gpt-4"
        )
        config_provider._config_cache["openai:gpt-4"] = config
        
        result = config_provider.get_token_config("openai", "gpt-4")
        
        assert result == config
        config_provider._provider_discovery.get_provider_config.assert_not_called()
    
    def test_get_token_config_from_provider(self, config_provider, mock_provider_discovery):
        """测试从Provider获取配置"""
        result = config_provider.get_token_config("openai", "gpt-4")
        
        assert result is not None
        assert result.provider_name == "openai"
        assert result.model_name == "gpt-4"
        assert result.cost_per_input_token == 0.01
        assert result.cost_per_output_token == 0.02
        assert result.fallback_enabled is True
        assert result.cache_enabled is True
        
        mock_provider_discovery.get_provider_config.assert_called_once_with("openai", "gpt-4")
    
    def test_get_token_config_not_found(self, config_provider, mock_provider_discovery):
        """测试未找到配置的情况"""
        mock_provider_discovery.get_provider_config.return_value = None
        
        result = config_provider.get_token_config("openai", "unknown-model")
        
        assert result is None
    
    def test_get_token_config_exception(self, config_provider, mock_provider_discovery):
        """测试获取配置时发生异常"""
        mock_provider_discovery.get_provider_config.side_effect = Exception("Test error")
        
        with patch('src.services.llm.config.token_config_provider.logger') as mock_logger:
            result = config_provider.get_token_config("openai", "gpt-4")
            
            assert result is None
            mock_logger.warning.assert_called_once()
    
    def test_extract_token_config(self, config_provider):
        """测试从Provider配置提取Token配置"""
        provider_config = {
            "token_calculation": {
                "type": "openai",
                "custom_tokenizer": "custom",
                "fallback_enabled": False,
                "cache_enabled": False
            },
            "pricing": {
                "input_token_cost": 0.015,
                "output_token_cost": 0.025
            },
            "tokenizer": {
                "model": "gpt-4-turbo"
            }
        }
        
        result = config_provider._extract_token_config(provider_config, "openai", "gpt-4")
        
        assert result.provider_name == "openai"
        assert result.model_name == "gpt-4"
        assert result.tokenizer_type == "openai"
        assert result.custom_tokenizer == "custom"
        assert result.fallback_enabled is False
        assert result.cache_enabled is False
        assert result.cost_per_input_token == 0.015
        assert result.cost_per_output_token == 0.025
        assert result.tokenizer_config == {"model": "gpt-4-turbo"}
    
    def test_get_supported_models(self, config_provider, mock_provider_discovery):
        """测试获取支持的模型列表"""
        result = config_provider.get_supported_models()
        
        assert result == {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-sonnet"]
        }
        mock_provider_discovery.list_all_models.assert_called_once()
    
    def test_get_supported_models_exception(self, config_provider, mock_provider_discovery):
        """测试获取支持模型列表时发生异常"""
        mock_provider_discovery.list_all_models.side_effect = Exception("Test error")
        
        with patch('src.services.llm.config.token_config_provider.logger') as mock_logger:
            result = config_provider.get_supported_models()
            
            assert result == {}
            mock_logger.error.assert_called_once()
    
    def test_is_model_supported(self, config_provider, mock_provider_discovery):
        """测试模型支持检查"""
        result = config_provider.is_model_supported("openai", "gpt-4")
        
        assert result is True
        mock_provider_discovery.validate_provider_config.assert_called_once_with("openai", "gpt-4")
    
    def test_is_model_supported_exception(self, config_provider, mock_provider_discovery):
        """测试模型支持检查时发生异常"""
        mock_provider_discovery.validate_provider_config.side_effect = Exception("Test error")
        
        with patch('src.services.llm.config.token_config_provider.logger') as mock_logger:
            result = config_provider.is_model_supported("openai", "gpt-4")
            
            assert result is False
            mock_logger.error.assert_called_once()
    
    def test_refresh_config_cache(self, config_provider, mock_provider_discovery):
        """测试刷新配置缓存"""
        # 预先设置缓存
        config_provider._config_cache["openai:gpt-4"] = "cached_config"
        
        with patch('src.services.llm.config.token_config_provider.logger') as mock_logger:
            config_provider.refresh_config_cache()
            
            assert config_provider._config_cache == {}
            mock_provider_discovery.refresh_cache.assert_called_once()
            mock_logger.info.assert_called_once_with("Token配置缓存已刷新")


class TestProviderConfigTokenCostCalculator:
    """Provider配置Token成本计算器测试类"""
    
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
        return provider
    
    @pytest.fixture
    def cost_calculator(self, mock_config_provider):
        """创建成本计算器实例"""
        return ProviderConfigTokenCostCalculator(mock_config_provider)
    
    def test_initialization(self, mock_config_provider):
        """测试初始化"""
        calculator = ProviderConfigTokenCostCalculator(mock_config_provider)
        
        assert calculator._config_provider == mock_config_provider
    
    def test_calculate_cost_success(self, cost_calculator, mock_config_provider):
        """测试成功计算成本"""
        result = cost_calculator.calculate_cost(100, 50, "openai", "gpt-4")
        
        assert result is not None
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.input_cost == 1.0  # 100 * 0.01
        assert result.output_cost == 1.0  # 50 * 0.02
        assert result.total_cost == 2.0
        assert result.currency == "USD"
        assert result.model_type == "openai"
        assert result.model_name == "gpt-4"
        
        mock_config_provider.get_token_config.assert_called_once_with("openai", "gpt-4")
    
    def test_calculate_cost_no_config(self, cost_calculator, mock_config_provider):
        """测试没有配置时的成本计算"""
        mock_config_provider.get_token_config.return_value = None
        
        with patch('src.services.llm.config.token_config_provider.logger') as mock_logger:
            result = cost_calculator.calculate_cost(100, 50, "openai", "gpt-4")
            
            assert result is None
            mock_logger.debug.assert_called_once()
    
    def test_calculate_cost_no_pricing(self, cost_calculator, mock_config_provider):
        """测试没有定价信息时的成本计算"""
        mock_config_provider.get_token_config.return_value = TokenCalculationConfig(
            provider_name="openai",
            model_name="gpt-4"
            # 没有定价信息
        )
        
        result = cost_calculator.calculate_cost(100, 50, "openai", "gpt-4")
        
        assert result is not None
        assert result.input_cost == 0.0
        assert result.output_cost == 0.0
        assert result.total_cost == 0.0
    
    def test_calculate_cost_exception(self, cost_calculator, mock_config_provider):
        """测试计算成本时发生异常"""
        mock_config_provider.get_token_config.side_effect = Exception("Test error")
        
        with patch('src.services.llm.config.token_config_provider.logger') as mock_logger:
            result = cost_calculator.calculate_cost(100, 50, "openai", "gpt-4")
            
            assert result is None
            mock_logger.error.assert_called_once()
    
    def test_get_model_pricing_info_success(self, cost_calculator, mock_config_provider):
        """测试成功获取模型定价信息"""
        result = cost_calculator.get_model_pricing_info("openai", "gpt-4")
        
        assert result is not None
        assert result["model_type"] == "openai"
        assert result["model_name"] == "gpt-4"
        assert result["input_token_cost"] == 0.01
        assert result["output_token_cost"] == 0.02
        
        mock_config_provider.get_token_config.assert_called_once_with("openai", "gpt-4")
    
    def test_get_model_pricing_info_no_config(self, cost_calculator, mock_config_provider):
        """测试没有配置时获取模型定价信息"""
        mock_config_provider.get_token_config.return_value = None
        
        result = cost_calculator.get_model_pricing_info("openai", "gpt-4")
        
        assert result is None
    
    def test_get_model_pricing_info_exception(self, cost_calculator, mock_config_provider):
        """测试获取模型定价信息时发生异常"""
        mock_config_provider.get_token_config.side_effect = Exception("Test error")
        
        with patch('src.services.llm.config.token_config_provider.logger') as mock_logger:
            result = cost_calculator.get_model_pricing_info("openai", "gpt-4")
            
            assert result is None
            mock_logger.error.assert_called_once()