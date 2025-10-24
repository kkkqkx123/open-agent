"""TUI配置模块单元测试"""

import pytest
from pathlib import Path
import tempfile
import json
import yaml

from src.presentation.tui.config import (
    ThemeConfig, BehaviorConfig, SubviewConfig, ShortcutConfig, 
    TUIConfig, ConfigManager, get_tui_config, get_config_manager
)
from src.presentation.tui.layout import LayoutManager


class TestThemeConfig:
    """测试主题配置类"""
    
    def test_theme_config_default_values(self):
        """测试主题配置默认值"""
        theme = ThemeConfig()
        assert theme.name == "default"
        assert theme.primary_color == "blue"
        assert theme.secondary_color == "green"
        assert theme.accent_color == "cyan"
        assert theme.text_color == "white"
        assert theme.border_style == "round"
        assert theme.background_color is None
    
    def test_theme_config_custom_values(self):
        """测试主题配置自定义值"""
        theme = ThemeConfig(
            name="dark",
            primary_color="red",
            background_color="black"
        )
        assert theme.name == "dark"
        assert theme.primary_color == "red"
        assert theme.background_color == "black"


class TestBehaviorConfig:
    """测试行为配置类"""
    
    def test_behavior_config_default_values(self):
        """测试行为配置默认值"""
        behavior = BehaviorConfig()
        assert behavior.auto_save is True
        assert behavior.auto_save_interval == 300
        assert behavior.max_history == 1000
        assert behavior.scroll_speed == 5
        assert behavior.animation_enabled is True
        assert behavior.refresh_rate == 10
    
    def test_behavior_config_custom_values(self):
        """测试行为配置自定义值"""
        behavior = BehaviorConfig(
            auto_save=False,
            max_history=500,
            refresh_rate=20
        )
        assert behavior.auto_save is False
        assert behavior.max_history == 500
        assert behavior.refresh_rate == 20


class TestSubviewConfig:
    """测试子界面配置类"""
    
    def test_subview_config_default_values(self):
        """测试子界面配置默认值"""
        subview = SubviewConfig()
        assert subview.enabled is True
        assert subview.auto_refresh is True
        assert subview.refresh_interval == 1.0
        assert subview.max_data_points == 100
        assert subview.analytics_show_details is True
        assert subview.visualization_show_details is True
        assert subview.system_show_studio_controls is True
        assert subview.errors_auto_collect is True
    
    def test_subview_config_custom_values(self):
        """测试子界面配置自定义值"""
        subview = SubviewConfig(
            enabled=False,
            refresh_interval=2.0,
            analytics_show_details=False
        )
        assert subview.enabled is False
        assert subview.refresh_interval == 2.0
        assert subview.analytics_show_details is False


class TestShortcutConfig:
    """测试快捷键配置类"""
    
    def test_shortcut_config_default_values(self):
        """测试快捷键配置默认值"""
        shortcuts = ShortcutConfig()
        assert shortcuts.analytics == "alt+1"
        assert shortcuts.visualization == "alt+2"
        assert shortcuts.system == "alt+3"
        assert shortcuts.errors == "alt+4"
        assert shortcuts.back == "escape"
        assert shortcuts.help == "f1"
    
    def test_shortcut_config_custom_values(self):
        """测试快捷键配置自定义值"""
        shortcuts = ShortcutConfig(
            analytics="ctrl+1",
            back="ctrl+c"
        )
        assert shortcuts.analytics == "ctrl+1"
        assert shortcuts.back == "ctrl+c"


class TestTUIConfig:
    """测试TUI配置类"""
    
    def test_tui_config_to_dict(self):
        """测试TUI配置转换为字典"""
        layout_manager = LayoutManager()
        config = TUIConfig(
            layout=layout_manager.config,
            theme=ThemeConfig(name="test"),
            behavior=BehaviorConfig(max_history=500),
            subview=SubviewConfig(enabled=False),
            shortcuts=ShortcutConfig(analytics="ctrl+1")
        )
        
        config_dict = config.to_dict()
        
        assert "layout" in config_dict
        assert "theme" in config_dict
        assert "behavior" in config_dict
        assert "subview" in config_dict
        assert "shortcuts" in config_dict
        
        assert config_dict["theme"]["name"] == "test"
        assert config_dict["behavior"]["max_history"] == 500
        assert config_dict["subview"]["enabled"] is False
        assert config_dict["shortcuts"]["analytics"] == "ctrl+1"
    
    def test_tui_config_from_dict(self):
        """测试从字典创建TUI配置"""
        data = {
            "layout": {
                "regions": {},
                "min_terminal_width": 80,
                "min_terminal_height": 24
            },
            "theme": {
                "name": "test",
                "primary_color": "red"
            },
            "behavior": {
                "auto_save": False,
                "max_history": 500
            },
            "subview": {
                "enabled": False,
                "refresh_interval": 2.0
            },
            "shortcuts": {
                "analytics": "ctrl+1",
                "back": "ctrl+c"
            }
        }
        
        config = TUIConfig.from_dict(data)
        
        assert config.theme.name == "test"
        assert config.theme.primary_color == "red"
        assert config.behavior.auto_save is False
        assert config.behavior.max_history == 500
        assert config.subview.enabled is False
        assert config.subview.refresh_interval == 2.0
        assert config.shortcuts.analytics == "ctrl+1"
        assert config.shortcuts.back == "ctrl+c"


class TestConfigManager:
    """测试配置管理器类"""
    
    def test_config_manager_init(self):
        """测试配置管理器初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            manager = ConfigManager(config_path)
            
            assert manager.config_path == config_path
            assert manager.config is not None
    
    def test_config_manager_load_default_config(self):
        """测试加载默认配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent_config.yaml"
            manager = ConfigManager(config_path)
            
            config = manager.load_config()
            
            assert config is not None
            assert config.theme.name == "default"
            assert config.behavior.auto_save is True
    
    def test_config_manager_save_and_load_yaml(self):
        """测试保存和加载YAML配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            manager = ConfigManager(config_path)
            
            # 修改配置
            manager.get_config().theme.name = "test_theme"
            manager.get_config().behavior.max_history = 2000
            manager.save_config()
            
            # 重新加载配置
            new_manager = ConfigManager(config_path)
            new_config = new_manager.get_config()
            
            assert new_config.theme.name == "test_theme"
            assert new_config.behavior.max_history == 2000
    
    def test_config_manager_save_and_load_json(self):
        """测试保存和加载JSON配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)
            
            # 修改配置
            manager.get_config().theme.name = "json_theme"
            manager.get_config().behavior.refresh_rate = 15
            manager.save_config()
            
            # 重新加载配置
            new_manager = ConfigManager(config_path)
            new_config = new_manager.get_config()
            
            assert new_config.theme.name == "json_theme"
            assert new_config.behavior.refresh_rate == 15
    
    def test_config_manager_update_config(self):
        """测试更新配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            manager = ConfigManager(config_path)
            
            # 更新主题配置
            manager.update_config(theme={"name": "updated_theme", "primary_color": "purple"})
            
            assert manager.get_config().theme.name == "updated_theme"
            assert manager.get_config().theme.primary_color == "purple"
            
            # 更新行为配置
            manager.update_config(behavior={"max_history": 3000, "refresh_rate": 25})
            
            assert manager.get_config().behavior.max_history == 3000
            assert manager.get_config().behavior.refresh_rate == 25
    
    def test_config_manager_reset_to_default(self):
        """测试重置为默认配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            manager = ConfigManager(config_path)
            
            # 修改配置
            manager.get_config().theme.name = "modified"
            manager.get_config().behavior.max_history = 9999
            
            # 重置为默认
            manager.reset_to_default()
            
            assert manager.get_config().theme.name == "default"
            assert manager.get_config().behavior.max_history == 1000  # 默认值


def test_get_tui_config():
    """测试获取TUI配置函数"""
    config = get_tui_config()
    
    assert config is not None
    assert hasattr(config, 'theme')
    assert hasattr(config, 'behavior')
    assert hasattr(config, 'subview')
    assert hasattr(config, 'shortcuts')


def test_get_config_manager():
    """测试获取配置管理器函数"""
    manager = get_config_manager()
    
    assert manager is not None
    assert hasattr(manager, 'config')
    assert hasattr(manager, 'load_config')
    assert hasattr(manager, 'save_config')
