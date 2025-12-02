"""LLM服务依赖注入绑定测试"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.services.container.llm_bindings import (
    register_llm_services,
    register_config_loader,
    register_config_manager,
    register_provider_discovery,
    register_token_config_provider,
    register_token_cost_calculator,
    register_token_calculation_service,
    register_token_calculation_decorator,
    register_llm_test_services,
    get_llm_service_config,
    validate_llm_config
)
from src.core.config.config_loader import ConfigLoader
from src.core.llm.config_manager import LLMConfigManager
from src.core.llm.provider_config_discovery import ProviderConfigDiscovery
from src.services.llm.token_calculation_service import TokenCalculationService
from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
from src.interfaces.llm import ITokenConfigProvider, ITokenCostCalculator


class TestLLMBindings:
    """LLM服务绑定测试类"""
    
    @pytest.fixture
    def mock_container(self):
        """创建模拟容器"""
        container = Mock()
        container.register = Mock()
        container.register_factory = Mock()
        container.has_service = Mock(return_value=True)
        container.get = Mock()
        return container
    
    @pytest.fixture
    def test_config(self):
        """测试配置"""
        return {
            "llm": {
                "token_calculation": {
                    "default_provider": "openai",
                    "enable_config_provider": True,
                    "enable_cost_calculator": True
                },
                "config_manager": {
                    "base_path": "configs/llms",
                    "enable_provider_configs": True
                }
            }
        }
    
    def test_register_llm_services(self, mock_container, test_config):
        """测试注册所有LLM服务"""
        with patch('src.services.container.llm_bindings.register_config_loader') as mock_loader, \
             patch('src.services.container.llm_bindings.register_config_manager') as mock_manager, \
             patch('src.services.container.llm_bindings.register_provider_discovery') as mock_discovery, \
             patch('src.services.container.llm_bindings.register_token_config_provider') as mock_provider, \
             patch('src.services.container.llm_bindings.register_token_cost_calculator') as mock_calculator, \
             patch('src.services.container.llm_bindings.register_token_calculation_service') as mock_service, \
             patch('src.services.container.llm_bindings.register_token_calculation_decorator') as mock_decorator:
            
            register_llm_services(mock_container, test_config)
            
            mock_loader.assert_called_once_with(mock_container, test_config, "default")
            mock_manager.assert_called_once_with(mock_container, test_config, "default")
            mock_discovery.assert_called_once_with(mock_container, test_config, "default")
            mock_provider.assert_called_once_with(mock_container, test_config, "default")
            mock_calculator.assert_called_once_with(mock_container, test_config, "default")
            mock_service.assert_called_once_with(mock_container, test_config, "default")
            mock_decorator.assert_called_once_with(mock_container, test_config, "default")
    
    def test_register_config_loader(self, mock_container, test_config):
        """测试注册配置加载器"""
        register_config_loader(mock_container, test_config)
        
        mock_container.register_factory.assert_called_once()
        call_args = mock_container.register_factory.call_args
        assert call_args[0][0] == ConfigLoader
        
        # 验证工厂函数
        factory = call_args[0][1]
        with patch('src.services.container.llm_bindings.ConfigLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader
            factory()
            mock_loader_class.assert_called_once_with("configs/llms")
    
    def test_register_config_manager(self, mock_container, test_config):
        """测试注册配置管理器"""
        register_config_manager(mock_container, test_config)
        
        mock_container.register_factory.assert_called_once()
        call_args = mock_container.register_factory.call_args
        assert call_args[0][0] == LLMConfigManager
        
        # 验证工厂函数
        factory = call_args[0][1]
        with patch('src.services.container.llm_bindings.LLMConfigManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            factory()
            mock_manager_class.assert_called_once()
    
    def test_register_provider_discovery(self, mock_container, test_config):
        """测试注册Provider配置发现器"""
        register_provider_discovery(mock_container, test_config)
        
        mock_container.register_factory.assert_called_once()
        call_args = mock_container.register_factory.call_args
        assert call_args[0][0] == ProviderConfigDiscovery
        
        # 验证工厂函数
        factory = call_args[0][1]
        with patch('src.services.container.llm_bindings.ProviderConfigDiscovery') as mock_discovery_class:
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            factory()
            mock_discovery_class.assert_called_once()
    
    def test_register_token_config_provider_enabled(self, mock_container, test_config):
        """测试启用Token配置提供者"""
        register_token_config_provider(mock_container, test_config)
        
        # 应该注册两次：接口和具体实现
        assert mock_container.register_factory.call_count == 2
        
        # 验证接口注册
        interface_call = mock_container.register_factory.call_args_list[0]
        assert interface_call[0][0] == ITokenConfigProvider
        
        # 验证具体实现注册
        impl_call = mock_container.register_factory.call_args_list[1]
        assert impl_call[0][0] == ProviderConfigDiscovery
    
    def test_register_token_config_provider_disabled(self, mock_container):
        """测试禁用Token配置提供者"""
        config = {
            "llm": {
                "token_calculation": {
                    "enable_config_provider": False
                }
            }
        }
        
        register_token_config_provider(mock_container, config)
        
        # 不应该注册任何服务
        mock_container.register_factory.assert_not_called()
    
    def test_register_token_cost_calculator_enabled(self, mock_container, test_config):
        """测试启用Token成本计算器"""
        register_token_cost_calculator(mock_container, test_config)
        
        # 应该注册两次：接口和具体实现
        assert mock_container.register_factory.call_count == 2
        
        # 验证接口注册
        interface_call = mock_container.register_factory.call_args_list[0]
        assert interface_call[0][0] == ITokenCostCalculator
    
    def test_register_token_cost_calculator_disabled(self, mock_container):
        """测试禁用Token成本计算器"""
        config = {
            "llm": {
                "token_calculation": {
                    "enable_cost_calculator": False
                }
            }
        }
        
        register_token_cost_calculator(mock_container, config)
        
        # 不应该注册任何服务
        mock_container.register_factory.assert_not_called()
    
    def test_register_token_cost_calculator_no_provider(self, mock_container):
        """测试没有配置提供者时的成本计算器注册"""
        mock_container.has_service.return_value = False
        config = {
            "llm": {
                "token_calculation": {
                    "enable_cost_calculator": True
                }
            }
        }
        
        register_token_cost_calculator(mock_container, config)
        
        # 不应该注册任何服务
        mock_container.register_factory.assert_not_called()
    
    def test_register_token_calculation_service(self, mock_container, test_config):
        """测试注册Token计算服务"""
        register_token_calculation_service(mock_container, test_config)
        
        mock_container.register_factory.assert_called_once()
        call_args = mock_container.register_factory.call_args
        assert call_args[0][0] == TokenCalculationService
        
        # 验证工厂函数
        factory = call_args[0][1]
        with patch('src.services.container.llm_bindings.TokenCalculationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            factory()
            mock_service_class.assert_called_once_with(default_provider="openai")
    
    def test_register_token_calculation_decorator(self, mock_container, test_config):
        """测试注册Token计算装饰器"""
        register_token_calculation_decorator(mock_container, test_config)
        
        mock_container.register_factory.assert_called_once()
        call_args = mock_container.register_factory.call_args
        assert call_args[0][0] == TokenCalculationDecorator
        
        # 验证工厂函数
        factory = call_args[0][1]
        with patch('src.services.container.llm_bindings.TokenCalculationDecorator') as mock_decorator_class:
            mock_decorator = Mock()
            mock_decorator_class.return_value = mock_decorator
            factory()
            mock_decorator_class.assert_called_once()
    
    def test_register_llm_test_services(self, mock_container):
        """测试注册测试环境LLM服务"""
        with patch('src.services.container.llm_bindings.register_llm_services') as mock_register:
            register_llm_test_services(mock_container, "test")
            
            mock_register.assert_called_once()
            call_args = mock_register.call_args
            assert call_args[0][0] == mock_container
            assert call_args[0][1]["llm"]["token_calculation"]["enable_config_provider"] is False
            assert call_args[0][1]["llm"]["token_calculation"]["enable_cost_calculator"] is False
            assert call_args[0][2] == "test"
    
    def test_get_llm_service_config(self, test_config):
        """测试获取LLM服务配置摘要"""
        result = get_llm_service_config(test_config)
        
        assert result["default_provider"] == "openai"
        assert result["config_provider_enabled"] is True
        assert result["cost_calculator_enabled"] is True
        assert result["provider_configs_enabled"] is True
        assert result["config_base_path"] == "configs/llms"
    
    def test_get_llm_service_config_defaults(self):
        """测试获取LLM服务配置摘要（使用默认值）"""
        config = {"llm": {}}
        result = get_llm_service_config(config)
        
        assert result["default_provider"] == "openai"
        assert result["config_provider_enabled"] is True
        assert result["cost_calculator_enabled"] is True
        assert result["provider_configs_enabled"] is True
        assert result["config_base_path"] == "configs/llms"
    
    def test_validate_llm_config_valid(self, test_config):
        """测试验证有效的LLM配置"""
        is_valid, errors = validate_llm_config(test_config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_llm_config_missing_section(self):
        """测试验证缺少LLM配置节"""
        config = {}
        is_valid, errors = validate_llm_config(config)
        
        assert is_valid is False
        assert "缺少llm配置节" in errors
    
    def test_validate_llm_config_invalid_default_provider(self):
        """测试验证无效的默认提供商"""
        config = {
            "llm": {
                "token_calculation": {
                    "default_provider": 123  # 应该是字符串
                }
            }
        }
        is_valid, errors = validate_llm_config(config)
        
        assert is_valid is False
        assert "token_calculation.default_provider必须是字符串" in errors
    
    def test_validate_llm_config_invalid_base_path(self):
        """测试验证无效的基础路径"""
        config = {
            "llm": {
                "config_manager": {
                    "base_path": 123  # 应该是字符串
                }
            }
        }
        is_valid, errors = validate_llm_config(config)
        
        assert is_valid is False
        assert "config_manager.base_path必须是字符串" in errors