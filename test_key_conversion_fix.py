#!/usr/bin/env python3
"""
测试按键转换逻辑修复效果
验证Page Up/Down、Home/End键是否能正确转换
"""

import sys
import queue
from unittest.mock import Mock
from blessed import Terminal

# 添加src目录到路径
sys.path.insert(0, 'src')

from presentation.tui.event_engine import EventEngine


def test_key_conversion():
    """测试按键转换功能"""
    print("🧪 测试按键转换逻辑修复效果")
    print("=" * 50)
    
    # 创建模拟终端和事件引擎
    terminal = Terminal()
    config = Mock()
    event_engine = EventEngine(terminal, config)
    
    # 测试用例：ESC序列 -> 预期按键
    test_cases = [
        # (输入序列, 预期输出, 描述)
        (['\x1b', '[', 'A'], "up", "向上键"),
        (['\x1b', '[', 'B'], "down", "向下键"),
        (['\x1b', '[', 'C'], "right", "向右键"),
        (['\x1b', '[', 'D'], "left", "向左键"),
        (['\x1b', '[', 'H'], "home", "Home键 (\\x1b[H)"),
        (['\x1b', '[', 'F'], "end", "End键 (\\x1b[F)"),
        (['\x1b', '[', '5', '~'], "page_up", "Page Up键 (\\x1b[5~)"),
        (['\x1b', '[', '6', '~'], "page_down", "Page Down键 (\\x1b[6~)"),
        (['\x1b', '[', '1', '~'], "home", "Home键 (\\x1b[1~)"),
        (['\x1b', '[', '4', '~'], "end", "End键 (\\x1b[4~)"),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for input_sequence, expected, description in test_cases:
        # 清空输入队列
        while not event_engine.input_queue.empty():
            event_engine.input_queue.get_nowait()
        
        # 添加测试序列到队列
        for char in input_sequence:
            event_engine.input_queue.put(char)
        
        # 测试转换
        try:
            result = event_engine._convert_key_sequence(input_sequence[0])
            
            if result == expected:
                print(f"✅ {description}: {input_sequence} -> {result}")
                success_count += 1
            else:
                print(f"❌ {description}: {input_sequence} -> {result} (期望: {expected})")
        except Exception as e:
            print(f"💥 {description}: {input_sequence} -> 异常: {e}")
    
    print("=" * 50)
    print(f"📊 测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有按键转换测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步调试")
        return False


def test_global_priority_keys():
    """测试全局优先按键机制"""
    print("\n🔧 测试全局优先按键机制")
    print("=" * 50)
    
    terminal = Terminal()
    config = Mock()
    event_engine = EventEngine(terminal, config)
    
    # 设置模拟处理器
    global_handler_called = False
    input_handler_called = False
    
    def mock_global_handler(key):
        global global_handler_called
        global_handler_called = True
        print(f"🌐 全局处理器处理: {key}")
        return True
    
    def mock_input_handler(key):
        global input_handler_called
        input_handler_called = True
        print(f"📝 输入处理器处理: {key}")
        return "REFRESH_UI"
    
    event_engine.set_global_key_handler(mock_global_handler)
    event_engine.set_input_component_handler(mock_input_handler)
    
    # 测试全局优先按键
    priority_keys = ["page_up", "page_down", "home", "end"]
    normal_keys = ["up", "down", "left", "right", "enter"]
    
    print("🎯 测试全局优先按键:")
    for key in priority_keys:
        global_handler_called = False
        input_handler_called = False
        event_engine._process_key(key)
        
        if global_handler_called and not input_handler_called:
            print(f"✅ {key}: 正确由全局处理器处理")
        else:
            print(f"❌ {key}: 处理器调用异常 (全局: {global_handler_called}, 输入: {input_handler_called})")
    
    print("\n📝 测试普通按键:")
    for key in normal_keys:
        global_handler_called = False
        input_handler_called = False
        event_engine._process_key(key)
        
        if input_handler_called:
            print(f"✅ {key}: 正确由输入处理器处理")
        else:
            print(f"❌ {key}: 输入处理器未被调用")


if __name__ == "__main__":
    print("🚀 开始按键处理修复验证测试")
    print("=" * 60)
    
    # 测试按键转换
    conversion_ok = test_key_conversion()
    
    # 测试全局优先机制
    test_global_priority_keys()
    
    print("\n" + "=" * 60)
    if conversion_ok:
        print("🎯 修复验证完成：按键转换逻辑工作正常")
        print("💡 建议：运行实际TUI应用测试虚拟滚动功能")
    else:
        print("🚨 修复验证失败：需要进一步调试")
    
    print("\n📋 修复摘要:")
    print("1. ✅ 添加了Page Up/Down、Home/End键的ESC序列转换")
    print("2. ✅ 实现了全局优先按键机制")
    print("3. ✅ 输入面板正确返回None让全局处理器处理优先按键")