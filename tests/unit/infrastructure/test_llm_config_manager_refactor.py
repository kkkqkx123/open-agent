"""测试LLMConfigManager重构后的功能"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.infrastructure.llm.config_manager import LLMConfigManager
from infrastructure.config.loader.yaml_loader import IConfigLoader
from src.infrastructure.llm.config import LLMClientConfig, LLMModuleConfig


class TestLLMConfigManagerRefactor:
    """测试LLMConfigManager重构后的功能"""

    @pytest.fixture
    def mock_config_loader(self):
        """模拟配置加载器"""
        mock_loader = Mock(spec=IConfigLoader)
        mock_loader.load.return_value = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        mock_loader.watch_for_changes.return_value = None
        mock_loader.stop_watching.return_value = None
        return mock_loader

    @pytest.fixture
    def llm_config_manager(self, mock_config_loader):
        """创建LLMConfigManager实例"""
        return LLMConfigManager(
            config_loader=mock_config_loader,
            config_subdir="llms",
            enable_hot_reload=False,  # 禁用热重载以简化测试
            validation_enabled=True
        )

    def test_init_with_config_loader(self, mock_config_loader):
        """测试使用配置加载器初始化"""
        manager = LLMConfigManager(
            config_loader=mock_config_loader,
            config_subdir="test_llms"
        )
        
        assert manager.config_loader == mock_config_loader
        assert manager.config_subdir == "test_llms"
        assert manager.enable_hot_reload is True  # 默认值
        assert manager.validation_enabled is True  # 默认值

    def test_load_module_config(self, llm_config_manager, mock_config_loader):
        """测试加载模块配置"""
        # 模拟模块配置数据
        mock_config_loader.load.return_value = {
            "default_model": "openai-gpt4",
            "default_timeout": 30,
            "cache_enabled": True
        }
        
        llm_config_manager._load_module_config()
        
        # 验证配置加载器被正确调用
        mock_config_loader.load.assert_called_once_with("llms/_group.yaml")
        
        # 验证模块配置已加载
        assert llm_config_manager._module_config is not None
        assert isinstance(llm_config_manager._module_config, LLMModuleConfig)
        assert llm_config_manager._module_config.default_model == "openai-gpt4"

    def test_load_client_configs(self, llm_config_manager, mock_config_loader):
        """测试加载客户端配置"""
        # 模拟目录扫描
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = [
                Path("openai-gpt4.yaml"),
                Path("gemini-pro.yaml")
            ]
            
            # 模拟配置数据
            def load_side_effect(path):
                if "openai-gpt4.yaml" in path:
                    return {
                        "model_type": "openai",
                        "model_name": "gpt-4",
                        "temperature": 0.7
                    }
                elif "gemini-pro.yaml" in path:
                    return {
                        "model_type": "gemini",
                        "model_name": "gemini-pro",
                        "temperature": 0.5
                    }
                return {}
            
            mock_config_loader.load.side_effect = load_side_effect
            
            llm_config_manager._load_client_configs()
            
            # 验证配置已加载
            assert len(llm_config_manager._client_configs) == 2
            assert "openai:gpt-4" in llm_config_manager._client_configs
            assert "gemini:gemini-pro" in llm_config_manager._client_configs

    def test_load_config_file_delegates_to_loader(self, llm_config_manager, mock_config_loader):
        """测试加载配置文件委托给核心加载器"""
        config_data = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "temperature": 0.7
        }
        mock_config_loader.load.return_value = config_data
        
        result = llm_config_manager._load_config_file("test_config.yaml")
        
        # 验证委托给了核心加载器
        mock_config_loader.load.assert_called_once_with("test_config.yaml")
        
        # 验证返回了正确的数据
        assert result == config_data

    def test_hot_reload_uses_loader(self, llm_config_manager, mock_config_loader):
        """测试热重载使用核心加载器"""
        llm_config_manager.enable_hot_reload = True
        llm_config_manager._start_hot_reload()
        
        # 验证注册了回调函数
        mock_config_loader.watch_for_changes.assert_called_once()
        
        # 获取回调函数
        callback = mock_config_loader.watch_for_changes.call_args[1]['callback']
        
        # 模拟文件变更
        config_data = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "temperature": 0.8  # 修改后的值
        }
        
        callback("llms/test_config.yaml", config_data)
        
        # 验证配置已更新
        assert "llms/test_config.yaml" in llm_config_manager._config_cache
        assert llm_config_manager._config_cache["llms/test_config.yaml"] == config_data

    def test_stop_hot_reload_uses_loader(self, llm_config_manager, mock_config_loader):
        """测试停止热重载使用核心加载器"""
        llm_config_manager._stop_hot_reload()
        
        # 验证调用了核心加载器的停止方法
        mock_config_loader.stop_watching.assert_called_once()

    def test_get_global_config_manager_compatibility(self):
        """测试全局配置管理器向后兼容性"""
        with patch('src.infrastructure.llm.config_manager.YamlConfigLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader
            
            # 导入并调用全局函数
            from src.infrastructure.llm.config_manager import get_global_config_manager
            
            # 清除全局实例
            import src.infrastructure.llm.config_manager as config_module
            config_module._global_config_manager = None
            
            manager = get_global_config_manager()
            
            # 验证创建了默认的配置加载器
            mock_loader_class.assert_called_once()
            
            # 验证管理器使用了配置加载器
            assert manager.config_loader == mock_loader

    def test_config_validation_still_works(self, mock_config_loader):
        """测试配置验证功能仍然正常工作"""
        # 模拟无效配置
        mock_config_loader.load.return_value = {
            "model_type": "invalid_type",  # 无效的模型类型
            "model_name": "gpt-4"
        }
        
        manager = LLMConfigManager(
            config_loader=mock_config_loader,
            validation_enabled=True
        )
        
        # 尝试加载配置应该抛出验证错误
        with pytest.raises(Exception) as exc_info:
            manager._load_config_file("test_config.yaml")
        
        assert "配置验证失败" in str(exc_info.value)