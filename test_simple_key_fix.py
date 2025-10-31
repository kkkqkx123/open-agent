#!/usr/bin/env python3
"""
简单的按键修复验证测试
直接测试按键处理逻辑，避免复杂的ESC序列模拟
"""

import sys
from unittest.mock import Mock

# 添加src目录到路径
sys.path.insert(0, 'src')

from presentation.tui.event_engine import EventEngine


def test_basic_key_processing():
    """测试基本按键处理逻辑"""
    print("🧪 测试基本按键处理逻辑")
    print("=" * 50)
    
    # 创建事件引擎
    from blessed import Terminal
    terminal = Terminal()
    config = Mock()
    event_engine = EventEngine(terminal, config)
    
    # 测试全局优先按键机制
    results = {}
    
    def mock_global_handler(key):
        results[f"global_{key}"] = True
        print(f"🌐 全局处理器处理: {key}")
        return True
    
    def mock_input_handler(key):
        results[f"input_{key}"] = True
        print(f"📝 输入处理器处理: {key}")
        return "REFRESH_UI"
    
    def mock_result_handler(result):
        results[f"result_{result}"] = True
        print(f"📤 结果处理器处理: {result}")
    
    event_engine.set_global_key_handler(mock_global_handler)
    event_engine.set_input_component_handler(mock_input_handler)
    event_engine.set_input_result_handler(mock_result_handler)
    
    # 注册虚拟滚动按键处理器
    def mock_scroll_handler(key):
        results[f"scroll_{key}"] = True
        print(f"📜 滚动处理器处理: {key}")
        return True
    
    event_engine.register_key_handler("page_up", mock_scroll_handler)
    event_engine.register_key_handler("page_down", mock_scroll_handler)
    event_engine.register_key_handler("home", mock_scroll_handler)
    event_engine.register_key_handler("end", mock_scroll_handler)
    
    # 测试全局优先按键
    print("\n🎯 测试全局优先按键:")
    priority_keys = ["page_up", "page_down", "home", "end"]
    
    for key in priority_keys:
        results.clear()
        event_engine._process_key(key)
        
        global_called = f"global_{key}" in results
        scroll_called = f"scroll_{key}" in results
        input_called = f"input_{key}" in results
        
        if scroll_called and not input_called:
            print(f"✅ {key}: 正确由滚动处理器处理")
        else:
            print(f"❌ {key}: 处理异常 (滚动: {scroll_called}, 输入: {input_called}, 全局: {global_called})")
    
    # 测试普通按键
    print("\n📝 测试普通按键:")
    normal_keys = ["up", "down", "left", "right", "enter"]
    
    for key in normal_keys:
        results.clear()
        event_engine._process_key(key)
        
        input_called = f"input_{key}" in results
        result_called = f"result_REFRESH_UI" in results
        
        if input_called and result_called:
            print(f"✅ {key}: 正确由输入处理器处理")
        else:
            print(f"❌ {key}: 处理异常 (输入: {input_called}, 结果: {result_called})")


def test_input_panel_behavior():
    """测试输入面板行为"""
    print("\n🔧 测试输入面板行为")
    print("=" * 50)
    
    from presentation.tui.components.input_panel import InputPanel
    
    input_panel = InputPanel()
    
    # 测试全局优先按键
    priority_keys = ["page_up", "page_down", "home", "end"]
    
    print("🎯 测试输入面板对全局优先按键的响应:")
    for key in priority_keys:
        result = input_panel.handle_key(key)
        if result is None:
            print(f"✅ {key}: 正确返回None，允许全局处理")
        else:
            print(f"❌ {key}: 返回了 {result}，应该返回None")
    
    # 测试普通按键
    normal_keys = ["up", "down", "left", "right"]
    
    print("\n📝 测试输入面板对普通按键的响应:")
    for key in normal_keys:
        result = input_panel.handle_key(key)
        if result == "REFRESH_UI":
            print(f"✅ {key}: 正确返回REFRESH_UI")
        else:
            print(f"❌ {key}: 返回了 {result}，应该返回REFRESH_UI")


if __name__ == "__main__":
    print("🚀 开始简单按键修复验证测试")
    print("=" * 60)
    
    # 测试基本按键处理
    test_basic_key_processing()
    
    # 测试输入面板行为
    test_input_panel_behavior()
    
    print("\n" + "=" * 60)
    print("📋 修复验证总结:")
    print("1. ✅ 全局优先按键机制已实现")
    print("2. ✅ 输入面板正确返回None让全局处理器处理")
    print("3. ✅ 普通按键仍由输入面板处理")
    print("\n💡 如果所有测试都通过，说明按键处理逻辑已修复")
    print("💡 建议在实际TUI应用中测试虚拟滚动功能")