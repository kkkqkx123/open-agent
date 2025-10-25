#!/usr/bin/env python3
"""测试布局修复的脚本"""

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from src.presentation.tui.layout import LayoutManager

def test_layout_creation():
    """测试布局创建"""
    console = Console()
    terminal_size = console.size
    
    print(f"终端尺寸: {terminal_size} (类型: {type(terminal_size)})")
    print(f"宽度: {terminal_size.width}, 高度: {terminal_size.height}")
    
    # 创建布局管理器
    layout_manager = LayoutManager()
    
    # 测试原始方式（应该失败）
    try:
        layout = layout_manager.create_layout(terminal_size)
        print("错误：原始方式应该失败但却成功了")
    except Exception as e:
        print(f"原始方式失败（预期）: {e}")
    
    # 测试修复后的方式（应该成功）
    try:
        layout = layout_manager.create_layout((terminal_size.width, terminal_size.height))
        print("修复后的方式成功")
        print(f"布局类型: {type(layout)}")
        
        # 测试Live类
        with Live(layout, console=console, refresh_per_second=1, screen=False) as live:
            print("Live显示成功")
            import time
            time.sleep(1)
        print("Live显示结束")
        
    except Exception as e:
        print(f"修复后的方式失败: {e}")

if __name__ == "__main__":
    test_layout_creation()