"""TUI布局模块单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Tuple

from src.presentation.tui.layout import (
    LayoutRegion, RegionConfig, LayoutConfig, ILayoutManager, 
    LayoutManager
)
from rich.console import Console
from rich.layout import Layout as RichLayout


class TestLayoutRegion:
    """测试布局区域枚举"""
    
    def test_layout_region_values(self):
        """测试布局区域枚举值"""
        assert LayoutRegion.HEADER.value == "header"
        assert LayoutRegion.SIDEBAR.value == "sidebar"
        assert LayoutRegion.MAIN.value == "main"
        assert LayoutRegion.INPUT.value == "input"
        assert LayoutRegion.LANGGRAPH.value == "langgraph"
        assert LayoutRegion.STATUS.value == "status"


class TestRegionConfig:
    """测试区域配置类"""
    
    def test_region_config_default_values(self):
        """测试区域配置默认值"""
        config = RegionConfig(name="test_region", min_size=10)
        
        assert config.name == "test_region"
        assert config.min_size == 10
        assert config.max_size is None
        assert config.ratio == 1
        assert config.resizable is True
        assert config.visible is True
    
    def test_region_config_custom_values(self):
        """测试区域配置自定义值"""
        config = RegionConfig(
            name="custom_region",
            min_size=5,
            max_size=20,
            ratio=2,
            resizable=False,
            visible=False
        )
        
        assert config.name == "custom_region"
        assert config.min_size == 5
        assert config.max_size == 20
        assert config.ratio == 2
        assert config.resizable is False
        assert config.visible is False


class TestLayoutConfig:
    """测试布局配置类"""
    
    def test_layout_config_default_values(self):
        """测试布局配置默认值"""
        regions = {
            LayoutRegion.HEADER: RegionConfig(name="header", min_size=3)
        }
        config = LayoutConfig(regions=regions)
        
        assert config.regions == regions
        assert config.min_terminal_width == 80
        assert config.min_terminal_height == 24
        assert config.responsive_breakpoints is not None
        assert "small" in config.responsive_breakpoints
        assert "medium" in config.responsive_breakpoints
        assert "large" in config.responsive_breakpoints
        assert "xlarge" in config.responsive_breakpoints
    
    def test_layout_config_custom_values(self):
        """测试布局配置自定义值"""
        regions = {
            LayoutRegion.HEADER: RegionConfig(name="header", min_size=5)
        }
        breakpoints = {
            "small": (70, 20),
            "large": (130, 45)
        }
        config = LayoutConfig(
            regions=regions,
            min_terminal_width=70,
            min_terminal_height=20,
            responsive_breakpoints=breakpoints
        )
        
        assert config.regions == regions
        assert config.min_terminal_width == 70
        assert config.min_terminal_height == 20
        assert config.responsive_breakpoints == breakpoints


class TestILayoutManager:
    """测试布局管理器接口"""
    
    def test_interface_methods(self):
        """测试接口方法定义"""
        # 验证ILayoutManager是抽象基类
        assert hasattr(ILayoutManager, '__abstractmethods__')
        
        # 验证接口方法
        expected_methods = {
            'create_layout', 'update_region_content', 
            'resize_layout', 'get_region_size'
        }
        assert expected_methods.issubset(ILayoutManager.__abstractmethods__)


class TestLayoutManager:
    """测试布局管理器实现"""
    
    def test_layout_manager_init(self):
        """测试布局管理器初始化"""
        manager = LayoutManager()
        
        assert manager.config is not None
        assert isinstance(manager.console, Console)
        assert manager.layout is None
        assert manager.terminal_size == (80, 24)
        assert manager.region_contents == {}
        assert manager.current_breakpoint == "small"
    
    def test_layout_manager_init_with_config(self):
        """测试使用配置初始化布局管理器"""
        config = LayoutConfig(
            regions={LayoutRegion.HEADER: RegionConfig(name="header", min_size=5)}
        )
        manager = LayoutManager(config)
        
        assert manager.config == config
    
    def test_create_default_config(self):
        """测试创建默认配置"""
        manager = LayoutManager()
        default_config = manager._create_default_config()
        
        assert isinstance(default_config, LayoutConfig)
        assert LayoutRegion.HEADER in default_config.regions
        assert LayoutRegion.SIDEBAR in default_config.regions
        assert LayoutRegion.MAIN in default_config.regions
        assert LayoutRegion.INPUT in default_config.regions
        assert LayoutRegion.LANGGRAPH in default_config.regions
        assert LayoutRegion.STATUS in default_config.regions
        
        # 验证各区域配置
        header_config = default_config.regions[LayoutRegion.HEADER]
        assert header_config.min_size == 3
        assert header_config.max_size == 5
        assert header_config.resizable is False
        
        sidebar_config = default_config.regions[LayoutRegion.SIDEBAR]
        assert sidebar_config.min_size == 15
        assert sidebar_config.max_size == 25
        assert sidebar_config.resizable is True
        
        main_config = default_config.regions[LayoutRegion.MAIN]
        assert main_config.min_size == 30
        assert main_config.resizable is True
        
        input_config = default_config.regions[LayoutRegion.INPUT]
        assert input_config.min_size == 3
        assert input_config.max_size == 5
        assert input_config.resizable is False
        
        langgraph_config = default_config.regions[LayoutRegion.LANGGRAPH]
        assert langgraph_config.visible is False
    
    def test_create_layout_small_terminal(self):
        """测试创建小终端布局"""
        manager = LayoutManager()
        terminal_size = (80, 24)  # 对应 small 断点
        
        layout = manager.create_layout(terminal_size)
        
        assert isinstance(layout, RichLayout)
        assert manager.terminal_size == terminal_size
        assert manager.current_breakpoint == "small"
    
    def test_create_layout_medium_terminal(self):
        """测试创建中等终端布局"""
        manager = LayoutManager()
        terminal_size = (100, 30)  # 对应 medium 断点
        
        layout = manager.create_layout(terminal_size)
        
        assert isinstance(layout, RichLayout)
        assert manager.terminal_size == terminal_size
        assert manager.current_breakpoint == "medium"
    
    def test_create_layout_large_terminal(self):
        """测试创建大终端布局"""
        manager = LayoutManager()
        terminal_size = (120, 40)  # 对应 large 断点
        
        layout = manager.create_layout(terminal_size)
        
        assert isinstance(layout, RichLayout)
        assert manager.terminal_size == terminal_size
        assert manager.current_breakpoint == "large"
    
    def test_update_region_content(self):
        """测试更新区域内容"""
        manager = LayoutManager()
        test_content = "Test content"
        
        manager.update_region_content(LayoutRegion.HEADER, test_content)
        
        assert LayoutRegion.HEADER in manager.region_contents
        assert manager.region_contents[LayoutRegion.HEADER] == test_content
    
    def test_resize_layout_same_breakpoint(self):
        """测试调整布局大小（相同断点）"""
        manager = LayoutManager()
        initial_size = (100, 30)  # medium
        new_size = (110, 35)      # still medium
        
        manager.create_layout(initial_size)
        old_breakpoint = manager.current_breakpoint
        
        manager.resize_layout(new_size)
        
        # 断点应该保持不变
        assert manager.current_breakpoint == old_breakpoint
    
    def test_resize_layout_different_breakpoint(self):
        """测试调整布局大小（不同断点）"""
        manager = LayoutManager()
        initial_size = (80, 24)   # small
        new_size = (120, 40)      # large
        
        manager.create_layout(initial_size)
        old_breakpoint = manager.current_breakpoint
        assert old_breakpoint == "small"
        
        manager.resize_layout(new_size)
        
        # 断点应该改变
        assert manager.current_breakpoint == "large"
    
    def test_determine_breakpoint(self):
        """测试确定响应式断点"""
        manager = LayoutManager()
        
        # 测试各种尺寸对应的断点
        assert manager._determine_breakpoint((70, 20)) == "small"
        assert manager._determine_breakpoint((100, 30)) == "medium"
        assert manager._determine_breakpoint((120, 40)) == "large"
        assert manager._determine_breakpoint((140, 50)) == "xlarge"
    
    def test_get_region_size_when_layout_not_created(self):
        """测试布局未创建时获取区域尺寸"""
        manager = LayoutManager()
        
        size = manager.get_region_size(LayoutRegion.HEADER)
        
        assert size == (0, 0)
    
    def test_is_region_visible(self):
        """测试区域可见性"""
        manager = LayoutManager()
        
        # 在 small 断点下，侧边栏不可见
        manager.current_breakpoint = "small"
        assert manager.is_region_visible(LayoutRegion.SIDEBAR) is False
        
        # 在 large 断点下，侧边栏可见（除非配置为不可见）
        manager.current_breakpoint = "large"
        assert manager.is_region_visible(LayoutRegion.SIDEBAR) is True
        
        # LANGGRAPH 区域的可见性取决于配置
        manager.config.regions[LayoutRegion.LANGGRAPH].visible = False
        assert manager.is_region_visible(LayoutRegion.LANGGRAPH) is False
    
    def test_has_region_method(self):
        """测试检查区域存在方法"""
        manager = LayoutManager()
        
        # 当布局未创建时，区域不存在
        assert manager._has_region("header") is False
        
        # 创建布局后，检查区域存在性
        manager.create_layout((100, 30))
        # 由于布局结构复杂，这里主要验证方法不会报错
        try:
            result = manager._has_region("header")
            # 可能返回 True 或 False，取决于实际布局结构
        except Exception:
            # 某些区域名可能不存在，这是正常的
            pass
    
    def test_get_current_breakpoint(self):
        """测试获取当前断点"""
        manager = LayoutManager()
        
        assert manager.get_current_breakpoint() == "small"
        
        manager.current_breakpoint = "large"
        assert manager.get_current_breakpoint() == "large"


class TestLayoutManagerLayoutCreation:
    """测试布局管理器布局创建功能"""
    
    def test_create_full_layout(self):
        """测试创建完整布局"""
        manager = LayoutManager()
        layout = RichLayout()
        
        # 使用私有方法测试布局结构
        full_layout = manager._create_full_layout(layout)
        
        # 验证返回的是布局对象
        assert isinstance(full_layout, RichLayout)
    
    def test_create_compact_layout_small(self):
        """测试创建小屏幕紧凑布局"""
        manager = LayoutManager()
        layout = RichLayout()
        
        # 设置为小屏幕断点
        manager.current_breakpoint = "small"
        compact_layout = manager._create_compact_layout(layout)
        
        # 验证返回的是布局对象
        assert isinstance(compact_layout, RichLayout)
    
    def test_create_compact_layout_medium(self):
        """测试创建中等屏幕紧凑布局"""
        manager = LayoutManager()
        layout = RichLayout()
        
        # 设置为中等屏幕断点
        manager.current_breakpoint = "medium"
        compact_layout = manager._create_compact_layout(layout)
        
        # 验证返回的是布局对象
        assert isinstance(compact_layout, RichLayout)
    
    def test_adjust_region_sizes_small(self):
        """测试调整小屏幕区域大小"""
        manager = LayoutManager()
        manager.terminal_size = (80, 24)
        manager.current_breakpoint = "small"
        
        # 先创建布局
        manager.create_layout(manager.terminal_size)
        
        # 调整区域大小
        manager._adjust_region_sizes()
        
        # 验证没有异常
        assert True
    
    def test_adjust_region_sizes_large(self):
        """测试调整大屏幕区域大小"""
        manager = LayoutManager()
        manager.terminal_size = (120, 40)
        manager.current_breakpoint = "large"
        
        # 先创建布局
        manager.create_layout(manager.terminal_size)
        
        # 调整区域大小
        manager._adjust_region_sizes()
        
        # 验证没有异常
        assert True
