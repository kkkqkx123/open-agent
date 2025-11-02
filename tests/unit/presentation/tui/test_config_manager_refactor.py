"""测试TUI ConfigManager重构后的功能"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json
import yaml

from src.presentation.tui.config import ConfigManager, TUIConfig


class TestTUIConfigManagerRefactor:
    """测试TUI ConfigManager重构后的功能"""

    @pytest.fixture
    def mock_config_loader(self):
        """模拟配置加载器"""
        mock_loader = Mock()
        mock_loader.resolve_env_vars.return_value = {
            "theme": {
                "primary_color": "blue",
                "secondary_color": "green"
            },
            "behavior": {
                "auto_save": True,
                "max_history": 1000
            }
        }
        return mock_loader

    @pytest.fixture
    def config_manager(self, mock_config_loader):
        """创建ConfigManager实例"""
        return ConfigManager(
            config_path=Path("/tmp/test_tui_config.yaml"),
            config_loader=mock_config_loader
        )

    def test_init_with_config_loader(self, mock_config_loader):
        """测试使用配置加载器初始化"""
        manager = ConfigManager(
            config_path=Path("/tmp/test_config.yaml"),
            config_loader=mock_config_loader
        )
        
        assert manager.config_loader == mock_config_loader
        assert manager.config_path == Path("/tmp/test_config.yaml")

    def test_init_without_config_loader(self):
        """测试不使用配置加载器初始化"""
        manager = ConfigManager(
            config_path=Path("/tmp/test_config.yaml"),
            config_loader=None
        )
        
        assert manager.config_loader is None
        assert manager.config_path == Path("/tmp/test_config.yaml")

    def test_load_config_uses_loader_for_env_vars(self, mock_config_loader):
        """测试加载配置时使用加载器处理环境变量"""
        config_data = {
            "theme": {
                "primary_color": "${PRIMARY_COLOR:blue}",
                "secondary_color": "green"
            },
            "behavior": {
                "auto_save": True,
                "max_history": "${MAX_HISTORY:1000}"
            }
        }
        
        # 模拟文件存在和内容
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            
            manager = ConfigManager(
                config_path=Path("/tmp/test_config.yaml"),
                config_loader=mock_config_loader
            )
            
            # 验证配置加载器的环境变量处理被调用
            mock_config_loader.resolve_env_vars.assert_called_once()
            
            # 验证配置已加载
            assert manager.config is not None
            assert isinstance(manager.config, TUIConfig)

    def test_load_config_without_loader(self):
        """测试不使用配置加载器时正常加载"""
        config_data = {
            "theme": {
                "primary_color": "blue",
                "secondary_color": "green"
            },
            "behavior": {
                "auto_save": True,
                "max_history": 1000
            }
        }
        
        # 模拟文件存在和内容
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            
            manager = ConfigManager(
                config_path=Path("/tmp/test_config.yaml"),
                config_loader=None
            )
            
            # 验证配置已加载
            assert manager.config is not None
            assert isinstance(manager.config, TUIConfig)
            assert manager.config.theme.primary_color == "blue"

    def test_load_config_with_json_format(self, mock_config_loader):
        """测试加载JSON格式的配置"""
        config_data = {
            "theme": {
                "primary_color": "blue",
                "secondary_color": "green"
            },
            "behavior": {
                "auto_save": True,
                "max_history": 1000
            }
        }
        
        # 模拟JSON文件
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(config_data))), \
             patch('pathlib.Path.suffix', '.json'):
            
            manager = ConfigManager(
                config_path=Path("/tmp/test_config.json"),
                config_loader=mock_config_loader
            )
            
            # 验证配置已加载
            assert manager.config is not None
            assert isinstance(manager.config, TUIConfig)

    def test_load_config_file_not_exists(self, mock_config_loader):
        """测试配置文件不存在时使用默认配置"""
        with patch('pathlib.Path.exists', return_value=False):
            manager = ConfigManager(
                config_path=Path("/tmp/nonexistent_config.yaml"),
                config_loader=mock_config_loader
            )
            
            # 验证使用了默认配置
            assert manager.config is not None
            assert isinstance(manager.config, TUIConfig)
            assert manager.config.theme.primary_color == "default"  # 默认值

    def test_load_config_error_handling(self, mock_config_loader):
        """测试加载配置文件时的错误处理"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("Read error")):
            
            # 捕获print输出
            with patch('builtins.print') as mock_print:
                manager = ConfigManager(
                    config_path=Path("/tmp/test_config.yaml"),
                    config_loader=mock_config_loader
                )
                
                # 验证打印了警告信息
                mock_print.assert_called()
                assert "警告" in str(mock_print.call_args)
                
                # 验证使用了默认配置
                assert manager.config is not None

    def test_get_config_manager_with_loader(self, mock_config_loader):
        """测试获取配置管理器时传入加载器"""
        # 清除全局实例
        import src.presentation.tui.config as config_module
        config_module._global_config_manager = None
        
        manager = config_module.get_config_manager(
            config_path=Path("/tmp/test_config.yaml"),
            config_loader=mock_config_loader
        )
        
        # 验证返回了正确的管理器
        assert isinstance(manager, ConfigManager)
        assert manager.config_loader == mock_config_loader

    def test_get_config_manager_without_loader(self):
        """测试获取配置管理器时不传入加载器"""
        # 清除全局实例
        import src.presentation.tui.config as config_module
        config_module._global_config_manager = None
        
        manager = config_module.get_config_manager(
            config_path=Path("/tmp/test_config.yaml")
        )
        
        # 验证返回了正确的管理器
        assert isinstance(manager, ConfigManager)
        assert manager.config_loader is None

    def test_get_tui_config_with_loader(self, mock_config_loader):
        """测试获取TUI配置时传入加载器"""
        config_data = {
            "theme": {
                "primary_color": "blue",
                "secondary_color": "green"
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            
            # 清除全局实例
            import src.presentation.tui.config as config_module
            config_module._global_config_manager = None
            
            tui_config = config_module.get_tui_config(
                config_path=Path("/tmp/test_config.yaml"),
                config_loader=mock_config_loader
            )
            
            # 验证返回了正确的配置
            assert isinstance(tui_config, TUIConfig)
            assert tui_config.theme.primary_color == "blue"

    def test_save_config_still_works(self, mock_config_loader):
        """测试保存配置功能仍然正常工作"""
        config_data = {
            "theme": {
                "primary_color": "red",
                "secondary_color": "yellow"
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))), \
             patch('yaml.dump') as mock_dump:
            
            manager = ConfigManager(
                config_path=Path("/tmp/test_config.yaml"),
                config_loader=mock_config_loader
            )
            
            # 修改配置
            manager.config.theme.primary_color = "purple"
            
            # 保存配置
            manager.save_config()
            
            # 验证调用了yaml.dump
            mock_dump.assert_called()

    def test_update_config_still_works(self, mock_config_loader):
        """测试更新配置功能仍然正常工作"""
        config_data = {
            "theme": {
                "primary_color": "blue",
                "secondary_color": "green"
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))), \
             patch('yaml.dump'):
            
            manager = ConfigManager(
                config_path=Path("/tmp/test_config.yaml"),
                config_loader=mock_config_loader
            )
            
            # 更新配置
            manager.update_config(
                theme={"primary_color": "red"},
                behavior={"auto_save": False}
            )
            
            # 验证配置已更新
            assert manager.config.theme.primary_color == "red"
            assert manager.config.behavior.auto_save is False