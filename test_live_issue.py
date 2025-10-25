#!/usr/bin/env python3
"""测试Live类问题的脚本"""

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from src.presentation.tui.layout import LayoutManager

def test_live_issue():
    """测试Live类问题"""
    console = Console()
    terminal_size = console.size
    
    # 创建布局管理器
    layout_manager = LayoutManager()
    
    # 使用原始方式创建布局
    layout = layout_manager.create_layout(terminal_size)
    
    print(f"布局类型: {type(layout)}")
    print(f"终端尺寸: {terminal_size}")
    
    # 测试Live类的使用
    try:
        # 这是原始代码中的使用方式
        with Live(layout, console=console, refresh_per_second=0.1, screen=True) as live:
            print("Live显示成功启动")
            import time
            time.sleep(1)
        print("Live显示成功结束")
    except Exception as e:
        print(f"Live显示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_live_issue()