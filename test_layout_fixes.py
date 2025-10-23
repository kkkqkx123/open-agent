#!/usr/bin/env python3
"""测试TUI布局修复的功能"""

import sys
import os
from typing import Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.presentation.tui.layout import LayoutManager, LayoutRegion, LayoutConfig, RegionConfig


def test_medium_breakpoint_input_area():
    """测试中等断点布局中输入区域是否正常显示"""
    print("测试1: 中等断点布局中输入区域是否正常显示")
    
    # 创建布局管理器
    layout_manager = LayoutManager()
    
    # 设置中等断点尺寸
    terminal_size = (100, 30)
    layout = layout_manager.create_layout(terminal_size)
    
    # 检查输入区域是否存在
    has_input = layout_manager._has_region("input")
    print(f"  - 输入区域存在: {has_input}")
    
    # 检查是否有未注册的info区域
    has_info = layout_manager._has_region("info")
    print(f"  - 未注册的info区域存在: {has_info}")
    
    # 检查断点是否正确
    current_breakpoint = layout_manager.get_current_breakpoint()
    print(f"  - 当前断点: {current_breakpoint}")
    
    # 获取输入区域尺寸
    input_size = layout_manager.get_region_size(LayoutRegion.INPUT)
    print(f"  - 输入区域尺寸: {input_size}")
    
    success = has_input and not has_info and current_breakpoint == "medium"
    print(f"  - 测试结果: {'通过' if success else '失败'}")
    print()
    
    return success


def test_resize_layout_trigger():
    """测试resize_layout触发机制是否正常工作"""
    print("测试2: resize_layout触发机制是否正常工作")
    
    # 创建布局管理器
    layout_manager = LayoutManager()
    
    # 初始尺寸
    initial_size = (95, 30)
    layout = layout_manager.create_layout(initial_size)
    initial_breakpoint = layout_manager.get_current_breakpoint()
    print(f"  - 初始尺寸: {initial_size}, 断点: {initial_breakpoint}")
    
    # 调整尺寸跨越断点阈值（95 → 103）
    new_size = (103, 30)
    layout_manager.resize_layout(new_size)
    new_breakpoint = layout_manager.get_current_breakpoint()
    print(f"  - 调整后尺寸: {new_size}, 断点: {new_breakpoint}")
    
    # 检查是否正确触发布局重建
    breakpoint_changed = initial_breakpoint != new_breakpoint
    print(f"  - 断点是否变化: {breakpoint_changed}")
    
    success = breakpoint_changed
    print(f"  - 测试结果: {'通过' if success else '失败'}")
    print()
    
    return success


def test_langgraph_region_in_large_layout():
    """测试大屏布局中langgraph区域是否正确处理"""
    print("测试3: 大屏布局中langgraph区域是否正确处理")
    
    # 创建布局管理器
    layout_manager = LayoutManager()
    
    # 设置大屏断点尺寸
    terminal_size = (120, 40)
    layout = layout_manager.create_layout(terminal_size)
    
    # 检查断点是否正确
    current_breakpoint = layout_manager.get_current_breakpoint()
    print(f"  - 当前断点: {current_breakpoint}")
    
    # 默认情况下langgraph不可见
    langgraph_visible = layout_manager.is_region_visible(LayoutRegion.LANGGRAPH)
    print(f"  - LangGraph区域默认可见性: {langgraph_visible}")
    
    # 设置langgraph可见
    layout_manager.set_region_visible("langgraph", True)
    langgraph_visible_after = layout_manager.is_region_visible(LayoutRegion.LANGGRAPH)
    print(f"  - 设置可见后LangGraph区域可见性: {langgraph_visible_after}")
    
    # 检查langgraph区域是否存在
    has_langgraph = layout_manager._has_region("langgraph")
    print(f"  - LangGraph区域存在: {has_langgraph}")
    
    # 获取langgraph区域尺寸
    langgraph_size = layout_manager.get_region_size(LayoutRegion.LANGGRAPH)
    print(f"  - LangGraph区域尺寸: {langgraph_size}")
    
    success = current_breakpoint == "large" and has_langgraph
    print(f"  - 测试结果: {'通过' if success else '失败'}")
    print()
    
    return success


def test_size_calculation_logic():
    """测试尺寸计算逻辑是否正确"""
    print("测试4: 尺寸计算逻辑是否正确")
    
    # 创建布局管理器
    layout_manager = LayoutManager()
    
    # 测试中等断点
    terminal_size = (100, 30)
    layout = layout_manager.create_layout(terminal_size)
    
    # 获取侧边栏尺寸
    sidebar_size = layout_manager.get_region_size(LayoutRegion.SIDEBAR)
    print(f"  - 中等断点侧边栏尺寸: {sidebar_size}")
    
    # 检查侧边栏宽度是否基于终端宽度而不是高度
    width_based_on_width = sidebar_size[0] < terminal_size[0] and sidebar_size[0] > 0
    print(f"  - 侧边栏宽度基于终端宽度: {width_based_on_width}")
    
    # 测试大断点
    terminal_size_large = (120, 40)
    layout_large = layout_manager.create_layout(terminal_size_large)
    
    # 获取侧边栏尺寸
    sidebar_size_large = layout_manager.get_region_size(LayoutRegion.SIDEBAR)
    print(f"  - 大断点侧边栏尺寸: {sidebar_size_large}")
    
    # 检查侧边栏宽度是否在大断点下合理
    reasonable_width = 20 <= sidebar_size_large[0] <= 40
    print(f"  - 大断点侧边栏宽度合理: {reasonable_width}")
    
    success = width_based_on_width and reasonable_width
    print(f"  - 测试结果: {'通过' if success else '失败'}")
    print()
    
    return success


def test_size_constraints():
    """测试区域尺寸约束机制"""
    print("测试5: 区域尺寸约束机制")
    
    # 创建自定义配置
    regions = {
        LayoutRegion.HEADER: RegionConfig(
            name="标题栏",
            min_size=3,
            max_size=5,
            ratio=1,
            resizable=False,
            min_height=3,
            max_height=5
        ),
        LayoutRegion.SIDEBAR: RegionConfig(
            name="侧边栏",
            min_size=15,
            max_size=25,
            ratio=1,
            resizable=True,
            min_width=15,
            max_width=40
        ),
        LayoutRegion.MAIN: RegionConfig(
            name="主内容区",
            min_size=30,
            ratio=3,
            resizable=True,
            min_width=30
        ),
        LayoutRegion.INPUT: RegionConfig(
            name="输入栏",
            min_size=3,
            max_size=5,
            ratio=1,
            resizable=False,
            min_height=3,
            max_height=5
        ),
        LayoutRegion.LANGGRAPH: RegionConfig(
            name="LangGraph面板",
            min_size=15,
            max_size=30,
            ratio=1,
            resizable=True,
            visible=False,
            min_width=15,
            max_width=30
        ),
        LayoutRegion.STATUS: RegionConfig(
            name="状态栏",
            min_size=1,
            max_size=1,
            ratio=1,
            resizable=False,
            min_height=1,
            max_height=1
        )
    }
    
    config = LayoutConfig(
        regions=regions,
        resize_threshold=(6, 3),
        resize_throttle_ms=30,
        sidebar_width_range=(20, 40),
        langgraph_width_range=(15, 30)
    )
    
    # 创建布局管理器
    layout_manager = LayoutManager(config)
    
    # 测试大断点
    terminal_size = (120, 40)
    layout = layout_manager.create_layout(terminal_size)
    
    # 获取侧边栏尺寸
    sidebar_size = layout_manager.get_region_size(LayoutRegion.SIDEBAR)
    print(f"  - 侧边栏尺寸: {sidebar_size}")
    
    # 检查侧边栏宽度是否在约束范围内
    sidebar_width_in_range = 20 <= sidebar_size[0] <= 40
    print(f"  - 侧边栏宽度在约束范围内: {sidebar_width_in_range}")
    
    # 设置langgraph可见并检查尺寸
    layout_manager.set_region_visible("langgraph", True)
    langgraph_size = layout_manager.get_region_size(LayoutRegion.LANGGRAPH)
    print(f"  - LangGraph区域尺寸: {langgraph_size}")
    
    # 检查langgraph宽度是否在约束范围内
    langgraph_width_in_range = 15 <= langgraph_size[0] <= 30
    print(f"  - LangGraph宽度在约束范围内: {langgraph_width_in_range}")
    
    success = sidebar_width_in_range and langgraph_width_in_range
    print(f"  - 测试结果: {'通过' if success else '失败'}")
    print()
    
    return success


def main():
    """运行所有测试"""
    print("开始测试TUI布局修复功能...\n")
    
    tests = [
        test_medium_breakpoint_input_area,
        test_resize_layout_trigger,
        test_langgraph_region_in_large_layout,
        test_size_calculation_logic,
        test_size_constraints
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试执行出错: {e}")
            results.append(False)
    
    # 汇总结果
    passed = sum(results)
    total = len(results)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("所有测试通过！布局修复成功。")
        return 0
    else:
        print("部分测试失败，需要进一步检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())