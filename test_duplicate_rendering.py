#!/usr/bin/env python3
"""测试重复渲染问题"""

import sys
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.presentation.tui.components.unified_timeline import UnifiedTimelineComponent


def test_duplicate_rendering():
    """测试是否存在重复渲染"""
    console = Console()
    
    # 创建统一时间线组件
    timeline = UnifiedTimelineComponent(max_events=10)
    
    # 添加一些事件
    timeline.add_user_message("用户消息1")
    timeline.add_assistant_message("助手回复1")
    timeline.add_tool_call("calculator", True, {"result": 4})
    
    console.print("\n[bold cyan]第一次渲染[/bold cyan]")
    panel1 = timeline.render()
    console.print(panel1)
    
    console.print("\n[bold cyan]第二次渲染（应该相同）[/bold cyan]")
    panel2 = timeline.render()
    console.print(panel2)
    
    console.print("\n[bold cyan]第三次渲染（应该相同）[/bold cyan]")
    panel3 = timeline.render()
    console.print(panel3)
    
    # 测试滚动后的渲染
    console.print("\n[bold cyan]滚动后渲染[/bold cyan]")
    timeline.scroll_up()
    panel4 = timeline.render()
    console.print(panel4)
    
    console.print("\n[bold cyan]再次滚动后渲染[/bold cyan]")
    timeline.scroll_up()
    panel5 = timeline.render()
    console.print(panel5)
    
    # 测试添加事件后的渲染
    console.print("\n[bold cyan]添加事件后渲染[/bold cyan]")
    timeline.add_user_message("用户消息2")
    panel6 = timeline.render()
    console.print(panel6)
    
    console.print("\n[bold cyan]再次渲染（应该包含新事件）[/bold cyan]")
    panel7 = timeline.render()
    console.print(panel7)


def test_renderable_consistency():
    """测试渲染对象的一致性"""
    console = Console()
    
    # 创建统一时间线组件
    timeline = UnifiedTimelineComponent(max_events=5)
    
    # 添加事件
    for i in range(3):
        timeline.add_user_message(f"用户消息{i+1}")
        timeline.add_assistant_message(f"助手回复{i+1}")
    
    # 获取虚拟滚动渲染器
    renderable = timeline.virtual_renderable
    
    console.print("\n[bold cyan]测试渲染对象一致性[/bold cyan]")
    
    # 多次渲染同一个renderable对象
    for i in range(3):
        console.print(f"\n[bold yellow]第{i+1}次渲染[/bold yellow]")
        console.print(Panel(renderable, title=f"渲染 {i+1}"))
    
    # 测试滚动后的渲染
    console.print("\n[bold cyan]滚动后测试[/bold cyan]")
    timeline.scroll_down()
    
    for i in range(3):
        console.print(f"\n[bold yellow]滚动后第{i+1}次渲染[/bold yellow]")
        console.print(Panel(renderable, title=f"滚动后渲染 {i+1}"))


if __name__ == "__main__":
    console = Console()
    
    console.print("[bold green]开始测试重复渲染问题[/bold green]")
    
    try:
        test_duplicate_rendering()
        test_renderable_consistency()
        
        console.print("\n[bold green]测试完成！[/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]测试失败: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)