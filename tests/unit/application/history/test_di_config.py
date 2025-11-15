"""History模块依赖注入配置单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.application.history.di_config import (
    register_history_services,
    register_history_services_with_dependencies,
    register_test_history_services
)
from src.infrastructure.container import IDependencyContainer
from src.domain.history.interfaces import IHistoryManager
from src.domain.history.cost_interfaces import ICostCalculator
from src.infrastructure.llm.token_calculators.base import ITokenCalculator
from src.infrastructure.llm.interfaces import ILLMCallHook
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.infrastructure.history.storage.memory_storage import MemoryHistoryStorage
from src.application.history.manager import HistoryManager
from infrastructure.history.token_tracker import TokenUsageTracker
from src.domain.history.cost_calculator import CostCalculator
from src.infrastructure.history.history_hook import HistoryRecordingHook


class TestRegisterHistoryServices:
    """register_history_services函数测试"""

    def test_register_history_services_enabled(self) -> None:
        """测试注册历史服务（启用）"""
        mock_container = Mock(spec=IDependencyContainer)
        config = {
            "history": {
                "enabled": True,
                "storage_path": "./test_history"
            }
        }
        
        with patch('src.application.history.di_config.FileHistoryStorage') as mock_storage_class:
            with patch('src.application.history.di_config.Path') as mock_path:
                mock_path.return_value = Path("./test_history")
                mock_storage_instance = Mock()
                mock_storage_class.return_value = mock_storage_instance
                
                register_history_services(mock_container, config)
                
                # 验证存储被注册
                mock_container.register_instance.assert_any_call(
                    mock_storage_class,
                    mock_storage_instance
                )
                
                # 验证管理器被注册
                mock_container.register.assert_any_call(
                    IHistoryManager,
                    HistoryManager,
                    lifetime="singleton"
                )

    def test_register_history_services_disabled(self) -> None:
        """测试注册历史服务（禁用）"""
        mock_container = Mock(spec=IDependencyContainer)
        config = {
            "history": {
                "enabled": False
            }
        }
        
        register_history_services(mock_container, config)
        
        # 验证没有注册任何服务
        mock_container.register_instance.assert_not_called()
        mock_container.register.assert_not_called()

    def test_register_history_services_no_config(self) -> None:
        """测试注册历史服务（无配置）"""
        mock_container = Mock(spec=IDependencyContainer)
        config = {}
        
        register_history_services(mock_container, config)
        
        # 验证没有注册任何服务
        mock_container.register_instance.assert_not_called()
        mock_container.register.assert_not_called()

    def test_register_history_services_default_storage_path(self) -> None:
        """测试注册历史服务（默认存储路径）"""
        mock_container = Mock(spec=IDependencyContainer)
        config = {
            "history": {
                "enabled": True
            }
        }
        
        with patch('src.application.history.di_config.FileHistoryStorage') as mock_storage_class:
            with patch('src.application.history.di_config.Path') as mock_path:
                mock_path_instance = Mock()
                mock_path.return_value = mock_path_instance
                mock_storage_instance = Mock()
                mock_storage_class.return_value = mock_storage_instance
                
                register_history_services(mock_container, config)
                
                # 验证使用默认路径
                mock_path.assert_called_once_with("./history")
                mock_container.register_instance.assert_any_call(
                    mock_storage_class,
                    mock_storage_instance
                )

    def test_register_history_services_with_pricing(self) -> None:
        """测试注册历史服务（带定价配置）"""
        mock_container = Mock(spec=IDependencyContainer)
        config = {
            "history": {
                "enabled": True,
                "pricing": {
                    "openai:gpt-4": {
                        "prompt_price_per_1k": 0.01,
                        "completion_price_per_1k": 0.03
                    }
                }
            }
        }
        
        with patch('src.application.history.di_config.FileHistoryStorage'):
            with patch('src.application.history.di_config.Path'):
                with patch('src.application.history.di_config.CostCalculator') as mock_cost_calculator_class:
                    mock_cost_calculator_instance = Mock()
                    mock_cost_calculator_class.return_value = mock_cost_calculator_instance
                    
                    register_history_services(mock_container, config)
                    
                    # 验证成本计算器被注册
                    mock_cost_calculator_class.assert_called_once_with({
                        "openai:gpt-4": {
                            "prompt_price_per_1k": 0.01,
                            "completion_price_per_1k": 0.03
                        }
                    })
                    mock_container.register_instance.assert_any_call(
                        ICostCalculator,
                        mock_cost_calculator_instance
                    )


class TestRegisterHistoryServicesWithDependencies:
    """register_history_services_with_dependencies函数测试"""

    def test_register_history_services_with_dependencies_enabled(self) -> None:
        """测试注册历史服务（带依赖，启用）"""
        mock_container = Mock(spec=IDependencyContainer)
        mock_token_calculator = Mock(spec=ITokenCalculator)
        config = {
            "history": {
                "enabled": True,
                "storage_path": "./test_history",
                "pricing": {
                    "openai:gpt-4": {
                        "prompt_price_per_1k": 0.01
                    }
                }
            }
        }
        
        # 模拟容器返回的服务
        mock_history_manager = Mock()
        mock_token_tracker = Mock()
        mock_cost_calculator = Mock()
        mock_history_hook = Mock()
        
        mock_container.get.side_effect = [
            mock_history_manager,  # TokenUsageTracker工厂函数中
            mock_cost_calculator,   # HistoryRecordingHook工厂函数中
            mock_token_tracker,     # HistoryRecordingHook工厂函数中
            mock_history_hook       # ILLMCallHook工厂函数中
        ]
        
        with patch('src.application.history.di_config.FileHistoryStorage'):
            with patch('src.application.history.di_config.Path'):
                with patch('src.application.history.di_config.CostCalculator') as mock_cost_calculator_class:
                    mock_cost_calculator_class.return_value = mock_cost_calculator
                    
                    register_history_services_with_dependencies(
                        mock_container,
                        config,
                        mock_token_calculator
                    )
                    
                    # 验证存储被注册
                    assert mock_container.register_instance.call_count >= 1
                    
                    # 验证管理器被注册
                    mock_container.register.assert_any_call(
                        IHistoryManager,
                        HistoryManager,
                        lifetime="singleton"
                    )
                    
                    # 验证成本计算器被注册
                    mock_container.register_instance.assert_any_call(
                        ICostCalculator,
                        mock_cost_calculator
                    )
                    
                    # 验证工厂方法被注册
                    assert mock_container.register_factory.call_count >= 1

    def test_register_history_services_with_dependencies_disabled(self) -> None:
        """测试注册历史服务（带依赖，禁用）"""
        mock_container = Mock(spec=IDependencyContainer)
        mock_token_calculator = Mock(spec=ITokenCalculator)
        config = {
            "history": {
                "enabled": False
            }
        }
        
        register_history_services_with_dependencies(
            mock_container,
            config,
            mock_token_calculator
        )
        
        # 验证没有注册任何服务
        mock_container.register_instance.assert_not_called()
        mock_container.register.assert_not_called()
        mock_container.register_factory.assert_not_called()

    def test_register_history_services_with_dependencies_no_pricing(self) -> None:
        """测试注册历史服务（带依赖，无定价配置）"""
        mock_container = Mock(spec=IDependencyContainer)
        mock_token_calculator = Mock(spec=ITokenCalculator)
        config = {
            "history": {
                "enabled": True
            }
        }
        
        with patch('src.application.history.di_config.FileHistoryStorage'):
            with patch('src.application.history.di_config.Path'):
                with patch('src.application.history.di_config.CostCalculator') as mock_cost_calculator_class:
                    mock_cost_calculator_instance = Mock()
                    mock_cost_calculator_class.return_value = mock_cost_calculator_instance
                    
                    register_history_services_with_dependencies(
                        mock_container,
                        config,
                        mock_token_calculator
                    )
                    
                    # 验证成本计算器使用空配置
                    mock_cost_calculator_class.assert_called_once_with({})


class TestRegisterTestHistoryServices:
    """register_test_history_services函数测试"""

    def test_register_test_history_services(self) -> None:
        """测试注册测试历史服务"""
        mock_container = Mock(spec=IDependencyContainer)
        
        with patch('src.infrastructure.history.storage.memory_storage.MemoryHistoryStorage') as mock_memory_storage_class:
            with patch('src.application.history.di_config.CostCalculator') as mock_cost_calculator_class:
                mock_memory_storage_instance = Mock()
                mock_memory_storage_class.return_value = mock_memory_storage_instance
                mock_cost_calculator_instance = Mock()
                mock_cost_calculator_class.return_value = mock_cost_calculator_instance
                
                register_test_history_services(mock_container)
                
                # 验证内存存储被注册为FileHistoryStorage
                mock_container.register_instance.assert_any_call(
                    FileHistoryStorage,
                    mock_memory_storage_instance
                )
                
                # 验证管理器被注册
                mock_container.register.assert_any_call(
                    IHistoryManager,
                    HistoryManager,
                    lifetime="singleton"
                )
                
                # 验证成本计算器被注册
                mock_cost_calculator_class.assert_called_once_with({
                    "openai:gpt-4": {
                        "prompt_price_per_1k": 0.01,
                        "completion_price_per_1k": 0.03
                    },
                    "openai:gpt-3.5-turbo": {
                        "prompt_price_per_1k": 0.001,
                        "completion_price_per_1k": 0.002
                    }
                })
                mock_container.register_instance.assert_any_call(
                    ICostCalculator,
                    mock_cost_calculator_instance
                )
                
                # 验证ILLMCallHook被注册
                mock_container.register.assert_any_call(
                    ILLMCallHook,
                    HistoryRecordingHook,
                    lifetime="singleton"
                )

    def test_register_test_history_services_memory_storage_import(self) -> None:
        """测试注册测试历史服务（内存存储导入）"""
        mock_container = Mock(spec=IDependencyContainer)
        
        with patch('src.infrastructure.history.storage.memory_storage.MemoryHistoryStorage') as mock_memory_storage_class:
            with patch('src.application.history.di_config.CostCalculator'):
                mock_memory_storage_instance = Mock()
                mock_memory_storage_class.return_value = mock_memory_storage_instance
                
                register_test_history_services(mock_container)
                
                # 验证MemoryHistoryStorage被实例化
                mock_memory_storage_class.assert_called_once()

    def test_register_test_history_services_cost_calculator_config(self) -> None:
        """测试注册测试历史服务（成本计算器配置）"""
        mock_container = Mock(spec=IDependencyContainer)
        
        with patch('src.infrastructure.history.storage.memory_storage.MemoryHistoryStorage'):
            with patch('src.application.history.di_config.CostCalculator') as mock_cost_calculator_class:
                mock_cost_calculator_instance = Mock()
                mock_cost_calculator_class.return_value = mock_cost_calculator_instance
                
                register_test_history_services(mock_container)
                
                # 验证测试定价配置
                expected_pricing = {
                    "openai:gpt-4": {
                        "prompt_price_per_1k": 0.01,
                        "completion_price_per_1k": 0.03
                    },
                    "openai:gpt-3.5-turbo": {
                        "prompt_price_per_1k": 0.001,
                        "completion_price_per_1k": 0.002
                    }
                }
                mock_cost_calculator_class.assert_called_once_with(expected_pricing)


class TestIntegrationScenarios:
    """集成场景测试"""

    def test_full_registration_flow(self) -> None:
        """测试完整注册流程"""
        mock_container = Mock(spec=IDependencyContainer)
        mock_token_calculator = Mock(spec=ITokenCalculator)
        config = {
            "history": {
                "enabled": True,
                "storage_path": "./custom_history",
                "pricing": {
                    "openai:gpt-4": {
                        "prompt_price_per_1k": 0.01,
                        "completion_price_per_1k": 0.03
                    }
                }
            }
        }
        
        # 模拟容器返回的服务
        mock_history_manager = Mock()
        mock_token_tracker = Mock()
        mock_cost_calculator = Mock()
        mock_history_hook = Mock()
        
        mock_container.get.side_effect = [
            mock_history_manager,
            mock_cost_calculator,
            mock_token_tracker,
            mock_history_hook
        ]
        
        with patch('src.application.history.di_config.FileHistoryStorage') as mock_storage_class:
            with patch('src.application.history.di_config.Path') as mock_path:
                with patch('src.application.history.di_config.CostCalculator') as mock_cost_calculator_class:
                    mock_path_instance = Mock()
                    mock_path.return_value = mock_path_instance
                    mock_storage_instance = Mock()
                    mock_storage_class.return_value = mock_storage_instance
                    mock_cost_calculator_class.return_value = mock_cost_calculator
                    
                    # 执行注册
                    register_history_services_with_dependencies(
                        mock_container,
                        config,
                        mock_token_calculator
                    )
                    
                    # 验证调用
                    assert mock_container.register_instance.call_count >= 1
                    assert mock_container.register.call_count >= 1
                    assert mock_container.register_factory.call_count >= 1

    def test_error_handling_in_registration(self) -> None:
        """测试注册中的错误处理"""
        mock_container = Mock(spec=IDependencyContainer)
        config = {
            "history": {
                "enabled": True
            }
        }
        
        # 模拟Path抛出异常
        with patch('src.application.history.di_config.Path', side_effect=Exception("路径错误")):
            # 应该抛出异常
            with pytest.raises(Exception, match="路径错误"):
                register_history_services(mock_container, config)