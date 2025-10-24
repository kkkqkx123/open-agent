"""TUI布局测试脚本"""

import time
from typing import List, Tuple
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout

from ..layout import LayoutManager, LayoutRegion, LayoutConfig, RegionConfig
from ..config import get_tui_config, TUIConfig


class LayoutTester:
    """布局测试器"""
    
    def __init__(self) -> None:
        """初始化布局测试器"""
        self.console = Console()
        self.test_sizes = [
            (80, 24),   # 小屏幕
            (100, 30),  # 中等屏幕
            (120, 40),  # 大屏幕
            (140, 50),  # 超大屏幕
            (60, 20),   # 极小屏幕（测试最小尺寸）
        ]
    
    def test_responsive_layouts(self) -> None:
        """测试响应式布局"""
        print("开始测试响应式布局...")
        
        for i, (width, height) in enumerate(self.test_sizes):
            print(f"\n测试 {i+1}/{len(self.test_sizes)}: 终端尺寸 {width}x{height}")
            
            # 创建布局管理器
            layout_manager = LayoutManager()
            
            # 创建布局
            layout = layout_manager.create_layout((width, height))
            
            # 显示布局信息
            self._display_layout_info(layout_manager, width, height)
            
            # 显示布局预览
            self._display_layout_preview(layout, width, height)
            
            # 等待用户确认
            if i < len(self.test_sizes) - 1:
                input("按回车键继续下一个测试...")
    
    def test_layout_regions(self) -> None:
        """测试布局区域"""
        print("\n测试布局区域...")
        
        layout_manager = LayoutManager()
        layout = layout_manager.create_layout((120, 40))
        
        # 测试每个区域
        for region in LayoutRegion:
            print(f"\n测试区域: {region.value}")
            
            # 获取区域尺寸
            size = layout_manager.get_region_size(region)
            print(f"区域尺寸: {size[0]}x{size[1]}")
            
            # 检查区域可见性
            visible = layout_manager.is_region_visible(region)
            print(f"区域可见性: {visible}")
            
            # 更新区域内容
            test_content = self._create_test_content(region, size)
            layout_manager.update_region_content(region, test_content)
            
            # 显示更新后的布局
            self._display_layout_preview(layout, 120, 40)
            
            input("按回车键继续...")
    
    def test_config_system(self) -> None:
        """测试配置系统"""
        print("\n测试配置系统...")
        
        # 获取默认配置
        config = get_tui_config()
        print(f"默认主题: {config.theme.name}")
        print(f"主色调: {config.theme.primary_color}")
        print(f"自动保存: {config.behavior.auto_save}")
        
        # 测试配置更新
        from ..config import get_config_manager
        config_manager = get_config_manager()
        
        # 更新主题配置
        config_manager.update_config(
            theme={
                "name": "dark",
                "primary_color": "red",
                "secondary_color": "blue"
            }
        )
        
        # 验证更新
        updated_config = config_manager.get_config()
        print(f"更新后主题: {updated_config.theme.name}")
        print(f"更新后主色调: {updated_config.theme.primary_color}")
        
        # 重置配置
        config_manager.reset_to_default()
        print("配置已重置为默认值")
    
    def test_breakpoints(self) -> None:
        """测试响应式断点"""
        print("\n测试响应式断点...")
        
        layout_manager = LayoutManager()
        
        test_sizes = [
            (70, 20),   # 小于最小尺寸
            (80, 24),   # 小屏幕
            (95, 28),   # 小屏幕到中等屏幕之间
            (100, 30),  # 中等屏幕
            (110, 35),  # 中等屏幕到大屏幕之间
            (120, 40),  # 大屏幕
            (130, 45),  # 大屏幕到超大屏幕之间
            (140, 50),  # 超大屏幕
        ]
        
        for width, height in test_sizes:
            layout_manager.create_layout((width, height))
            breakpoint = layout_manager.get_current_breakpoint()
            print(f"尺寸 {width}x{height} -> 断点: {breakpoint}")
    
    def _display_layout_info(self, layout_manager: LayoutManager, width: int, height: int) -> None:
        """显示布局信息"""
        breakpoint = layout_manager.get_current_breakpoint()
        
        info_table = Table(title="布局信息")
        info_table.add_column("属性", style="cyan")
        info_table.add_column("值", style="green")
        
        info_table.add_row("终端尺寸", f"{width}x{height}")
        info_table.add_row("当前断点", breakpoint)
        
        for region in LayoutRegion:
            visible = layout_manager.is_region_visible(region)
            size = layout_manager.get_region_size(region)
            info_table.add_row(f"{region.value} 可见性", str(visible))
            info_table.add_row(f"{region.value} 尺寸", f"{size[0]}x{size[1]}")
        
        self.console.print(info_table)
    
    def _display_layout_preview(self, layout: Layout, width: int, height: int) -> None:
        """显示布局预览"""
        # 创建一个模拟的控制台来显示布局
        preview_console = Console(width=width, height=height, legacy_windows=False)
        
        # 显示布局
        preview_console.print(layout)
        
        # 添加边框
        border_text = Text(f"布局预览 ({width}x{height})", style="bold cyan")
        border_panel = Panel(
            layout,
            title=border_text,
            border_style="cyan"
        )
        
        self.console.print(border_panel)
    
    def _create_test_content(self, region: LayoutRegion, size: Tuple[int, int]) -> Panel:
        """创建测试内容"""
        width, height = size
        
        if region == LayoutRegion.HEADER:
            content = Text(f"标题栏测试内容 ({width}x{height})", style="bold blue")
        elif region == LayoutRegion.SIDEBAR:
            content = Text(f"侧边栏测试内容\n尺寸: {width}x{height}", style="green")
        elif region == LayoutRegion.MAIN:
            content = Text(f"主内容区测试内容\n尺寸: {width}x{height}\n" + "=" * (width - 4), style="white")
        elif region == LayoutRegion.INPUT:
            content = Text(f"输入栏测试内容 ({width}x{height})", style="yellow")
        else:
            content = Text(f"未知区域: {region.value}", style="red")
        
        return Panel(
            content,
            title=f"{region.value} 测试",
            border_style="cyan"
        )
    
    def run_all_tests(self) -> None:
        """运行所有测试"""
        print("开始运行TUI布局测试...")
        print("=" * 50)
        
        try:
            self.test_responsive_layouts()
            self.test_layout_regions()
            self.test_config_system()
            self.test_breakpoints()
            
            print("\n" + "=" * 50)
            print("所有测试完成！")
            
        except Exception as e:
            print(f"测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()


def main() -> None:
    """主函数"""
    tester = LayoutTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()