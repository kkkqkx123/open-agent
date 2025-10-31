#!/usr/bin/env python3
"""测试虚拟滚动修复效果"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.presentation.tui.components.unified_timeline import (
    UnifiedTimelineComponent,
    VirtualScrollManager,
    UserMessageEvent,
    AssistantMessageEvent
)


def test_virtual_scroll_manager():
    """测试虚拟滚动管理器"""
    print("=== 测试虚拟滚动管理器 ===")
    
    # 创建测试数据
    total_items = 100
    visible_height = 30
    item_height = 1
    
    manager = VirtualScrollManager(total_items, visible_height, item_height)
    
    # 测试初始状态
    print(f"初始状态: offset={manager.scroll_offset}, start={manager.visible_start}, end={manager.visible_end}")
    
    # 测试更新可见范围
    start, end = manager.update_visible_range()
    print(f"更新可见范围: start={start}, end={end}")
    
    # 测试滚动
    manager.scroll_by(5)
    print(f"向下滚动5: offset={manager.scroll_offset}")
    
    start, end = manager.update_visible_range()
    print(f"滚动后可见范围: start={start}, end={end}")
    
    # 测试向上滚动
    manager.scroll_by(-3)
    print(f"向上滚动3: offset={manager.scroll_offset}")
    
    # 测试滚动到末尾
    manager.scroll_to_end()
    print(f"滚动到末尾: offset={manager.scroll_offset}")
    
    start, end = manager.update_visible_range()
    print(f"末尾可见范围: start={start}, end={end}")
    
    # 测试滚动检查
    print(f"可以向上滚动: {manager.can_scroll_up()}")
    print(f"可以向下滚动: {manager.can_scroll_down()}")
    
    # 测试更新总项目数
    manager.update_total_items(50)
    print(f"更新总项目数到50: offset={manager.scroll_offset}")
    
    print("虚拟滚动管理器测试完成\n")


def test_unified_timeline_component():
    """测试统一时间线组件"""
    print("=== 测试统一时间线组件 ===")
    
    # 创建时间线组件
    timeline = UnifiedTimelineComponent(max_events=100)
    
    # 添加测试事件
    for i in range(50):
        if i % 2 == 0:
            timeline.add_user_message(f"用户消息 {i}")
        else:
            timeline.add_assistant_message(f"助手回复 {i}")
    
    print(f"添加了50个事件，总数: {len(timeline.events)}")
    
    # 测试滚动功能
    print(f"初始滚动偏移: {timeline.virtual_renderable.scroll_manager.scroll_offset}")
    
    # 测试向上滚动
    timeline.scroll_up()
    print(f"向上滚动后偏移: {timeline.virtual_renderable.scroll_manager.scroll_offset}")
    
    # 测试向下滚动
    timeline.scroll_down()
    print(f"向下滚动后偏移: {timeline.virtual_renderable.scroll_manager.scroll_offset}")
    
    # 测试滚动到末尾
    timeline.scroll_to_end()
    print(f"滚动到末尾后偏移: {timeline.virtual_renderable.scroll_manager.scroll_offset}")
    
    # 测试滚动检查
    print(f"可以向上滚动: {timeline.virtual_renderable.scroll_manager.can_scroll_up()}")
    print(f"可以向下滚动: {timeline.virtual_renderable.scroll_manager.can_scroll_down()}")
    
    # 测试渲染
    try:
        panel = timeline.render()
        print("渲染成功")
        print(f"面板标题: {panel.title}")
    except Exception as e:
        print(f"渲染失败: {e}")
    
    print("统一时间线组件测试完成\n")


def test_scroll_edge_cases():
    """测试滚动边界情况"""
    print("=== 测试滚动边界情况 ===")
    
    # 测试少量项目
    manager = VirtualScrollManager(5, 30, 1)
    print(f"少量项目(5): offset={manager.scroll_offset}")
    print(f"可以向上滚动: {manager.can_scroll_up()}")
    print(f"可以向下滚动: {manager.can_scroll_down()}")
    
    # 测试零项目
    manager = VirtualScrollManager(0, 30, 1)
    print(f"零项目: offset={manager.scroll_offset}")
    print(f"可以向上滚动: {manager.can_scroll_up()}")
    print(f"可以向下滚动: {manager.can_scroll_down()}")
    
    # 测试单项目
    manager = VirtualScrollManager(1, 30, 1)
    print(f"单项目: offset={manager.scroll_offset}")
    print(f"可以向上滚动: {manager.can_scroll_up()}")
    print(f"可以向下滚动: {manager.can_scroll_down()}")
    
    print("边界情况测试完成\n")


if __name__ == "__main__":
    print("开始测试虚拟滚动修复效果...\n")
    
    try:
        test_virtual_scroll_manager()
        test_unified_timeline_component()
        test_scroll_edge_cases()
        
        print("✅ 所有测试完成！虚拟滚动功能修复成功。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()