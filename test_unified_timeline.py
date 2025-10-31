#!/usr/bin/env python3
"""测试统一时间线组件"""

import sys
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.presentation.tui.components.unified_timeline import (
    UnifiedTimelineComponent,
    UserMessageEvent,
    AssistantMessageEvent,
    ToolCallStartEvent,
    ToolCallEndEvent,
    NodeSwitchEvent,
    TriggerEvent,
    WorkflowEvent,
    StreamSegmentEvent,
    SystemMessageEvent
)
from src.presentation.tui.components.unified_main_content import UnifiedMainContentComponent


def test_unified_timeline():
    """测试统一时间线组件"""
    console = Console()
    
    # 创建统一时间线组件
    timeline = UnifiedTimelineComponent(max_events=100)
    
    # 添加各种事件
    timeline.add_user_message("你好，请介绍一下你自己")
    timeline.add_assistant_message("你好！我是一个AI助手，可以帮助你处理各种任务。")
    
    # 添加工具调用
    timeline.add_tool_call("calculator", True, {"expression": "2 + 2", "result": 4})
    timeline.add_tool_call("weather", False, error="无法获取天气信息")
    
    # 添加节点切换
    timeline.add_node_switch("input_node", "processing_node")
    
    # 添加触发器事件
    timeline.add_trigger_event("timer_trigger", "每5分钟触发一次")
    
    # 添加工作流事件
    timeline.add_workflow_event("main_workflow", "started", "开始执行工作流")
    
    # 添加系统消息
    timeline.add_system_message("系统初始化完成", "success")
    timeline.add_system_message("检测到错误", "error")
    
    # 测试流式输出
    timeline.start_stream()
    timeline.add_stream_content("正在生成回复...")
    timeline.add_stream_content("这是一个测试流式输出的示例。")
    timeline.add_stream_content("流式输出可以分段显示，避免频繁刷新界面。")
    timeline.end_stream()
    
    # 渲染时间线
    console.print("\n[bold cyan]统一时间线测试[/bold cyan]")
    console.print(timeline.render())
    
    # 测试滚动功能
    console.print("\n[bold cyan]测试滚动功能[/bold cyan]")
    console.print("向上滚动...")
    timeline.scroll_up()
    console.print(timeline.render())
    
    console.print("\n向下滚动...")
    timeline.scroll_down()
    console.print(timeline.render())
    
    console.print("\n滚动到末尾...")
    timeline.scroll_to_end()
    console.print(timeline.render())


def test_unified_main_content():
    """测试统一主内容区组件"""
    console = Console()
    
    # 创建统一主内容区组件
    main_content = UnifiedMainContentComponent()
    
    # 添加各种内容
    main_content.add_user_message("你好，请介绍一下你自己")
    main_content.add_assistant_message("你好！我是一个AI助手，可以帮助你处理各种任务。")
    
    # 添加工具调用
    main_content.add_tool_call("calculator", True, {"expression": "2 + 2", "result": 4})
    main_content.add_tool_call("weather", False, error="无法获取天气信息")
    
    # 添加节点切换
    main_content.add_node_switch("input_node", "processing_node")
    
    # 添加触发器事件
    main_content.add_trigger_event("timer_trigger", "每5分钟触发一次")
    
    # 添加工作流事件
    main_content.add_workflow_event("main_workflow", "started", "开始执行工作流")
    
    # 添加系统消息
    main_content.add_system_message("系统初始化完成", "success")
    main_content.add_system_message("检测到错误", "error")
    
    # 测试流式输出
    main_content.start_stream()
    main_content.add_stream_content("正在生成回复...")
    main_content.add_stream_content("这是一个测试流式输出的示例。")
    main_content.add_stream_content("流式输出可以分段显示，避免频繁刷新界面。")
    main_content.end_stream()
    
    # 渲染主内容区
    console.print("\n[bold cyan]统一主内容区测试[/bold cyan]")
    console.print(main_content.render())
    
    # 显示统计信息
    stats = main_content.get_stats()
    console.print("\n[bold cyan]统计信息[/bold cyan]")
    for key, value in stats.items():
        console.print(f"{key}: {value}")
    
    # 测试按键处理
    console.print("\n[bold cyan]测试按键处理[/bold cyan]")
    console.print("测试PageUp按键...")
    result = main_content.handle_key("page_up")
    console.print(f"处理结果: {result}")
    
    console.print("测试PageDown按键...")
    result = main_content.handle_key("page_down")
    console.print(f"处理结果: {result}")
    
    console.print("测试Home按键...")
    result = main_content.handle_key("home")
    console.print(f"处理结果: {result}")
    
    console.print("测试End按键...")
    result = main_content.handle_key("end")
    console.print(f"处理结果: {result}")
    
    console.print("测试A按键...")
    result = main_content.handle_key("a")
    console.print(f"处理结果: {result}")
    
    # 显示帮助信息
    console.print("\n[bold cyan]帮助信息[/bold cyan]")
    console.print(main_content.get_help_text())


def test_performance():
    """测试性能"""
    console = Console()
    
    # 创建统一时间线组件
    timeline = UnifiedTimelineComponent(max_events=1000)
    
    # 添加大量事件
    console.print("\n[bold cyan]性能测试 - 添加1000个事件[/bold cyan]")
    start_time = datetime.now()
    
    for i in range(1000):
        timeline.add_user_message(f"用户消息 {i}")
        timeline.add_assistant_message(f"助手回复 {i}")
        if i % 10 == 0:
            timeline.add_tool_call(f"tool_{i}", True, {"result": i})
        if i % 50 == 0:
            timeline.add_system_message(f"系统消息 {i}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    console.print(f"添加1000个事件耗时: {duration:.3f}秒")
    console.print(f"平均每个事件耗时: {duration/1000*1000:.3f}毫秒")
    
    # 测试渲染性能
    console.print("\n[bold cyan]渲染性能测试[/bold cyan]")
    start_time = datetime.now()
    
    # 渲染10次
    for _ in range(10):
        panel = timeline.render()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    console.print(f"渲染10次耗时: {duration:.3f}秒")
    console.print(f"平均每次渲染耗时: {duration/10*1000:.3f}毫秒")


if __name__ == "__main__":
    console = Console()
    
    console.print("[bold green]开始测试统一时间线组件[/bold green]")
    
    try:
        test_unified_timeline()
        test_unified_main_content()
        test_performance()
        
        console.print("\n[bold green]所有测试完成！[/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]测试失败: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)